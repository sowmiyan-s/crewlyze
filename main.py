# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
FastAPI Server backend for the Crewlyze application.
Serves static HTML/JS/CSS assets and exposes REST APIs + Server-Sent Events (SSE)
for streaming real-time analysis logs.
"""

import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import json
import re
import uuid
import asyncio
import shutil
import threading
import time
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional

import pandas as pd
from tools.dataset_tools import read_csv_robust

# Monkey patch crewai caching to avoid Nvidia NIM / LiteLLM validation errors
try:
    import crewai.llms.cache as _crewai_cache
    _crewai_cache.mark_cache_breakpoint = lambda msg: msg
except Exception:
    pass

# Copy assets on startup/reload
try:
    # 1. Convert bin/crewlyze.js line endings to LF
    bin_js = Path(__file__).resolve().parent / "bin" / "crewlyze.js"
    if bin_js.exists():
        with open(bin_js, "rb") as f:
            content = f.read()
        lf_content = content.replace(b"\r\n", b"\n")
        with open(bin_js, "wb") as f:
            f.write(lf_content)
        print("Successfully converted bin/crewlyze.js line endings to LF")
except Exception as e:
    print(f"Failed to convert line endings: {e}")

from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# regex to find ANSI terminal escape patterns
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

# To keep track of log states (e.g. ignoring prompt blocks) per session
log_stream_states = {}

def clean_log_message(line: str, session_id: Optional[str] = None) -> Optional[str]:
    """Strip ANSI color codes, ignore noisy messages, and format thoughts/actions nicely."""
    # Strip ANSI colors/escapes
    line = ANSI_ESCAPE.sub('', line)
    
    # Check if empty
    stripped = line.strip()
    if not stripped:
        return None

    line_lower = stripped.lower()
    
    # System logs noise keywords to ignore
    noise_keywords = [
        "scriptruncontext",
        "telemetry_opt_out",
        "otel_sdk_disabled",
        "opentelemetry",
        "urllib3",
        "connectionpool",
        "http/1.1",
        "httpx",
        "backoff",
        "requests.packages",
        "missing scriptruncontext",
        "openai-api-keyword",
        "http request",
        "cooldown",
        "rate limit",
        "max_tokens",
    ]
    if any(kw in line_lower for kw in noise_keywords):
        return None

    # Handle stateful prompt block ignoring
    if session_id:
        if session_id not in log_stream_states:
            log_stream_states[session_id] = {"in_prompt": False}
        state = log_stream_states[session_id]
        
        # Start ignoring if prompt starts
        if "prompt after formatting:" in line_lower or "use the following format:" in line_lower:
            state["in_prompt"] = True
            return None
            
        # Stop ignoring if agent thoughts/actions/results start
        if state["in_prompt"]:
            stop_triggers = ["thought:", "action:", "action input:", "response:", "observation:", "entering new", "finished chain"]
            if any(trig in line_lower for trig in stop_triggers):
                state["in_prompt"] = False
            else:
                return None  # Still ignoring prompt contents

    # Ignore raw debug logs from crewai/langchain
    if stripped.startswith("[DEBUG]:") or stripped.startswith("[INFO]:"):
        if "working agent" in line_lower:
            agent_name = stripped.split(":", 2)[-1].strip()
            return f"[Agent] {agent_name} is active..."
        return None

    # Format specific Langchain output structures for a premium look
    if "entering new crewagentexecutor chain" in line_lower:
        return "[Task] Starting agent execution task..."
    if "finished chain" in line_lower:
        return "[Task] Execution task completed."
    
    # Format Thoughts, Actions, inputs, and outputs nicely
    if stripped.startswith("Thought:"):
        thought_text = stripped[8:].strip()
        return f"[Thought] {thought_text}"
        
    if stripped.startswith("Action:"):
        action_text = stripped[7:].strip()
        return f"[Calling Tool] {action_text}"
        
    if stripped.startswith("Action Input:"):
        input_text = stripped[13:].strip()
        if len(input_text) > 150:
            input_text = input_text[:150] + "..."
        return f"[Input] {input_text}"
        
    if stripped.startswith("Response:") or stripped.startswith("Observation:"):
        resp_text = stripped.split(":", 1)[1].strip()
        if len(resp_text) > 150:
            resp_text = resp_text[:150] + "..."
        return f"[Tool Response] {resp_text}"

    if "warning" in line_lower or "error" in line_lower:
        if "error" in line_lower:
            return f"[Error] {stripped}"
        return f"[Warning] {stripped}"

    return stripped

# Core analysis engines — imported lazily so the server boots
# even if crewai has install issues on this Python version.
# Actual ImportError surfaces only when analysis is triggered.
_run_crew = None
_apply_runtime_llm_settings = None
_validate_llm_connection = None
_run_copilot_query = None
_export_pdf = None
_export_chat_pdf = None

def _load_crew():
    global _run_crew, _apply_runtime_llm_settings, _validate_llm_connection
    global _run_copilot_query, _export_pdf, _export_chat_pdf
    if _run_crew is None:
        from crew import run_crew as _rc
        from config.llm_config import apply_runtime_llm_settings as _arls, validate_llm_connection as _vlc
        from ui.copilot import run_copilot_query as _rcq
        from ui.export import export_pdf as _ep, export_chat_pdf as _ecp
        _run_crew = _rc
        _apply_runtime_llm_settings = _arls
        _validate_llm_connection = _vlc
        _run_copilot_query = _rcq
        _export_pdf = _ep
        _export_chat_pdf = _ecp

# Suppress warnings
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"]        = "true"

app = FastAPI(
    title="Crewlyze API",
    description="Autonomous Multi-Agent Business Intelligence and Data Engineering Platform",
    version="3.1.0"
)

# Enable CORS for local development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Optional Enterprise Auth
# ---------------------------------------------------------------------------
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "enterprise-secret-key")

class OptionalAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if AUTH_ENABLED:
            if request.url.path.startswith("/api/") and not request.url.path.startswith("/api/validate-key"):
                auth_header = request.headers.get("Authorization")
                if not auth_header or not auth_header.startswith("Bearer ") or auth_header.split(" ")[1] != AUTH_TOKEN:
                    return JSONResponse(status_code=401, content={"detail": "Unauthorized: Invalid or missing Enterprise Token"})
        response = await call_next(request)
        return response

app.add_middleware(OptionalAuthMiddleware)

# ---------------------------------------------------------------------------
# State & Directory Setup
# ---------------------------------------------------------------------------

USER_HOME = Path.home() / ".crewlyze"
DATA_DIR = Path(os.getenv("CREWLYZE_DATA_DIR", str(USER_HOME / "data")))
SESSIONS_DIR = DATA_DIR / "sessions"
OUTPUTS_DIR = Path(os.getenv("CREWLYZE_OUTPUTS_DIR", str(USER_HOME / "outputs")))

for path in (DATA_DIR, SESSIONS_DIR, OUTPUTS_DIR):
    path.mkdir(exist_ok=True, parents=True)

def is_safe_id(id_str: str) -> bool:
    """Ensure the ID is strictly alphanumeric (plus dashes/underscores) to prevent path traversal."""
    if not id_str:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", id_str))

def is_safe_filename(filename: str) -> bool:
    """Ensure the filename doesn't contain path traversal characters and has a safe pattern."""
    if not filename:
        return False
    if ".." in filename or "/" in filename or "\\" in filename:
        return False
    if "\0" in filename:
        return False
    # Allow safe characters including spaces, dashes, dots, underscores, parentheses, brackets, and common special symbols in column names
    return bool(re.match(r"^[a-zA-Z0-9_\-. ()[\]$,%&+@=;\'~#]+$", filename))

def validate_project_id(project_id: str) -> str:
    """Validate that the project_id matches a safe pattern to prevent path traversal."""
    if not is_safe_id(project_id):
        raise HTTPException(status_code=400, detail="Invalid project ID.")
    return project_id

def get_safe_session_dir(project_id: str) -> Path:
    pid = validate_project_id(project_id)
    base = SESSIONS_DIR.resolve()
    resolved = (base / pid).resolve()
    try:
        resolved.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=400, detail="Path traversal detected.")
    return resolved

def get_safe_output_dir(project_id: str) -> Path:
    pid = validate_project_id(project_id)
    base = OUTPUTS_DIR.resolve()
    resolved = (base / pid).resolve()
    try:
        resolved.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=400, detail="Path traversal detected.")
    return resolved

_metadata_lock = threading.Lock()

def save_project_metadata(project_id: str, meta: dict):
    session_dir = get_safe_session_dir(project_id)
    if not session_dir.exists():
        session_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = session_dir / "metadata.json"
    with _metadata_lock:
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

def get_project_metadata(project_id: str) -> dict:
    session_dir = get_safe_session_dir(project_id)
    metadata_path = session_dir / "metadata.json"
    
    if not session_dir.exists():
        return {}
        
    meta = {}
    with _metadata_lock:
        if metadata_path.exists():
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception:
                pass
            
    # Default metadata if not present or corrupt (compatibility check)
    if not meta:
        upload_file = session_dir / "original_upload.csv"
        filename = "dataset.csv"
        size = 0
        if upload_file.exists():
            filename = "dataset.csv"
            size = upload_file.stat().st_size
        
        results_path = session_dir / "results.json"
        status = "idle"
        if results_path.exists():
            status = "completed"
        elif (session_dir / "done.txt").exists():
            status = "completed"
            
        created_at = session_dir.stat().st_ctime
        meta = {
            "id": project_id,
            "name": f"Project {project_id}",
            "filename": filename,
            "report_title": f"{filename.rsplit('.', 1)[0].replace('_', ' ').title()} Executive Analysis",
            "size": size,
            "created_at": created_at * 1000,
            "status": status,
            "thumbnail": None
        }

    # Dynamically resolve and update the thumbnail link if generated PNGs exist
    output_dir = get_safe_output_dir(project_id)
    current_thumb = meta.get("thumbnail")
    target_thumb = None
    if output_dir.exists() and output_dir.is_dir():
        png_charts = sorted(
            [f for f in output_dir.glob("*.png")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        if png_charts:
            import urllib.parse
            target_thumb = f"/api/charts/{project_id}/{urllib.parse.quote(png_charts[0].name)}"

    if current_thumb != target_thumb:
        meta["thumbnail"] = target_thumb
        save_project_metadata(project_id, meta)
        
    return meta


def parse_bool(value: Optional[str]) -> bool:
    return bool(value and str(value).strip().lower() not in {"false", "0", "off", "no", ""})


def optimize_goal_grammar(goal: str, provider: str, model: str, api_key: str, env_key_name: str) -> str:
    """Uses the runtime-configured LLM to optimize the grammar of the project goal."""
    if not goal.strip():
        return ""
    try:
        from config.llm_config import apply_runtime_llm_settings, get_llm_params
        from crewai import LLM
        
        apply_runtime_llm_settings(provider, model, api_key or "", env_key_name)
        params = get_llm_params()
        llm = LLM(**params)
        
        prompt = (
            "You are a professional editor. Improve the grammar, phrasing, and professional tone "
            "of the following data analysis goal. Keep it concise (1-2 sentences). "
            "Return ONLY the corrected goal text, without any introductory text, quotes, or metadata.\n\n"
            f"Goal: {goal.strip()}"
        )
        response = llm.call([{"role": "user", "content": prompt}])
        result = response if isinstance(response, str) else str(response)
        return result.strip().strip('"').strip("'")
    except Exception as e:
        print(f"Grammar optimization failed: {e}")
        return goal.strip()


# ---------------------------------------------------------------------------
# Background Task Pipeline
# ---------------------------------------------------------------------------

MAX_CONCURRENT_ANALYSES = 2
active_analyses = 0
active_analyses_lock = threading.Lock()

def run_crew_in_background(
    session_id: str,
    csv_path: str,
    provider: str,
    model: str,
    api_key: str,
    env_key_name: str,
    cooldown: int,
    selected_tasks: list[str],
    deep_analysis: bool,
    report_title: str,
):
    """
    Orchestrates the CrewAI pipeline in a background thread, writing all
    stdout progress to a tail-able stdout.log file and serializing results.
    """
    if not is_safe_id(session_id):
        raise ValueError("Invalid session ID.")
    session_dir = (SESSIONS_DIR / session_id).resolve()
    resolved_csv = Path(csv_path).resolve()
    try:
        resolved_csv.relative_to(session_dir)
    except ValueError:
        raise ValueError("Path traversal detected in CSV path.")

    # 1. Inject thread-isolated LLM configurations and context variables
    from config.context import (
        current_session_id,
        current_session_csv,
        current_session_output_dir,
        current_llm_provider,
        current_llm_model,
        current_llm_api_key,
        current_llm_env_key_name,
        current_cooldown,
        current_deep_analysis,
    )
    current_session_id.set(session_id)
    current_session_csv.set(str(resolved_csv))
    current_session_output_dir.set(str((OUTPUTS_DIR / session_id).resolve()))
    current_llm_provider.set(provider)
    current_llm_model.set(model)
    current_llm_api_key.set(api_key or "")
    current_llm_env_key_name.set(env_key_name or "")
    current_cooldown.set(cooldown)
    current_deep_analysis.set(deep_analysis)



    # Save or update the report title and goal in project metadata
    try:
        meta = get_project_metadata(session_id)
        if report_title:
            meta["report_title"] = report_title.strip()
        
        user_goal = meta.get("goal", "")
        if user_goal.strip():
            print("Optimizing goal grammar...")
            opt_goal = optimize_goal_grammar(user_goal, provider, model, api_key, env_key_name)
            meta["optimized_goal"] = opt_goal
            print(f"Optimized goal: {opt_goal}")
        else:
            meta["optimized_goal"] = ""
            
        save_project_metadata(session_id, meta)
    except Exception as e:
        print(f"Error handling metadata goal/title: {e}")

    session_dir = SESSIONS_DIR / session_id
    log_path = session_dir / "stdout.log"
    done_path = session_dir / "done.txt"
    results_path = session_dir / "results.json"

    # Clean up previous state
    done_path.unlink(missing_ok=True)
    results_path.unlink(missing_ok=True)

    # Update metadata status to running
    try:
        meta = get_project_metadata(session_id)
        meta["status"] = "running"
        save_project_metadata(session_id, meta)
    except Exception:
        pass

    # 2. Redirect stdout and kickoff
    with open(log_path, "w", encoding="utf-8", errors="replace") as log_file:
        import contextlib
        with contextlib.redirect_stdout(log_file):
            try:
                print("Initializing multi-agent workflows...")
                _load_crew()
                result = _run_crew(
                    csv_path,
                    session_id=session_id,
                    selected_tasks=selected_tasks or None,
                    deep_analysis=deep_analysis,
                )
                
                # Convert results to JSON-serializable structure
                # Re-map Plotly charts into serializable JSON dictionaries
                plotly_serializable = []
                for chart in result.get("plotly_charts", []):
                    try:
                        plotly_serializable.append({
                            "title": chart["title"],
                            "fig_json": json.loads(chart["fig"].to_json())
                        })
                    except Exception:
                        pass

                # Gather static PNG charts
                png_charts_list = [f.name for f in Path(result["output_dir"]).glob("*.png")]

                serializable_result = {
                    "cleaning_steps": result["cleaning_steps"],
                    "relations":      result["relations"],
                    "insights":       result["insights"],
                    "code":           result.get("code", ""),
                    "output_dir":     result["output_dir"],
                    "plotly_charts":  plotly_serializable,
                    "png_charts":     png_charts_list,
                    "rows_count":     int(result["dataframe"].shape[0]),
                    "cols_count":     int(result["dataframe"].shape[1]),
                    "numeric_count":  int(len(result["dataframe"].select_dtypes(include=["number"]).columns)),
                    "cat_count":      int(len(result["dataframe"].select_dtypes(include=["object"]).columns))
                }

                # Cache first 100 rows as JSON data preview
                preview_data = result["dataframe"].head(100).replace([float('inf'), float('-inf')], float('nan')).fillna("").to_dict(orient="records")
                serializable_result["preview"] = preview_data

                with open(results_path, "w", encoding="utf-8") as f:
                    json.dump(serializable_result, f, indent=2)
                
                print("\nAnalysis complete! Ready to render dashboard.")

                # Update metadata status to completed
                try:
                    meta = get_project_metadata(session_id)
                    meta["status"] = "completed"
                    if png_charts_list:
                        import urllib.parse
                        meta["thumbnail"] = f"/api/charts/{session_id}/{urllib.parse.quote(png_charts_list[0])}"
                    save_project_metadata(session_id, meta)
                except Exception:
                    pass

            except Exception as e:
                import traceback
                print(f"\nPipeline failed: {e}", file=sys.stderr)
                traceback.print_exc(file=log_file)
                
                error_result = {"error": str(e)}
                with open(results_path, "w", encoding="utf-8") as f:
                    json.dump(error_result, f, indent=2)

                # Update metadata status to failed
                try:
                    meta = get_project_metadata(session_id)
                    meta["status"] = "failed"
                    save_project_metadata(session_id, meta)
                except Exception:
                    pass
            finally:
                # Write done sentinel to stop EventSource streams
                with open(done_path, "w") as f:
                    f.write("done")
                global active_analyses
                with active_analyses_lock:
                    active_analyses = max(0, active_analyses - 1)


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Uploads the dataset and registers a unique user session ID."""
    session_id = uuid.uuid4().hex[:12]
    session_dir = get_safe_session_dir(session_id)
    session_dir.mkdir(parents=True, exist_ok=True)

    file_path = session_dir / "original_upload.csv"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Pre-configure fresh log files
    log_path = session_dir / "stdout.log"
    with open(log_path, "w") as f:
        f.write("Dataset uploaded successfully.\n")

    # Save default project metadata
    try:
        proj_name = file.filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
        meta = {
            "id": session_id,
            "name": proj_name,
            "filename": file.filename,
            "size": file_path.stat().st_size,
            "created_at": time.time() * 1000,
            "status": "idle"
        }
        save_project_metadata(session_id, meta)
    except Exception:
        pass

    return {
        "session_id": session_id,
        "filename": file.filename,
        "size": file_path.stat().st_size
    }


@app.post("/api/validate-key")
async def validate_api_key(
    provider: str = Form(...),
    model: str = Form(...),
    api_key: Optional[str] = Form(""),
):
    """Validate LLM provider credentials before starting analysis."""
    try:
        _load_crew()
    except ImportError as exc:
        raise HTTPException(status_code=503, detail=f"CrewAI not available: {exc}")
    result = _validate_llm_connection(provider, model, api_key or "")
    if not result.get("valid"):
        raise HTTPException(status_code=400, detail=result.get("message", "Validation failed."))
    return result


@app.post("/api/analyze")
async def trigger_analysis(
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
    provider: str = Form(...),
    model: str = Form(...),
    api_key: Optional[str] = Form(""),
    cooldown: int = Form(5),
    selected_tasks: str = Form(""),
    deep_analysis: str = Form("false"),
    report_title: str = Form("")
):
    """Launches the CrewAI analysis process in the background."""
    session_dir = get_safe_session_dir(session_id)
    csv_path = session_dir / "original_upload.csv"

    if not csv_path.exists():
        raise HTTPException(status_code=400, detail="Session upload not found.")

    # Match provider key name
    if provider == "ollama":
        env_key_name = "OLLAMA_BASE_URL"
    elif provider in ("nvidia", "minimax"):
        env_key_name = "NVIDIA_API_KEY"
    else:
        env_key_name = f"{provider.upper()}_API_KEY"

    selected_tasks = [
        task.strip()
        for task in selected_tasks.split(",")
        if task.strip()
    ]
    if not selected_tasks:
        selected_tasks = ["cleaning", "relations", "insights", "visualization"]

    deep = deep_analysis.strip().lower() in {"true", "1", "yes", "on"}

    # Persist report title if provided
    try:
        meta = get_project_metadata(session_id)
        if report_title.strip():
            meta["report_title"] = report_title.strip()
            save_project_metadata(session_id, meta)
    except Exception:
        pass

    # Concurrency control checks
    global active_analyses
    with active_analyses_lock:
        if active_analyses >= MAX_CONCURRENT_ANALYSES:
            raise HTTPException(
                status_code=429,
                detail="Server is busy. Maximum concurrent analyses limit reached. Please try again later."
            )
        active_analyses += 1

    # Spawn thread-safe background execution
    try:
        background_tasks.add_task(
            run_crew_in_background,
            session_id=session_id,
            csv_path=str(csv_path),
            provider=provider,
            model=model,
            api_key=api_key,
            env_key_name=env_key_name,
            cooldown=cooldown,
            selected_tasks=selected_tasks,
            deep_analysis=deep,
            report_title=report_title.strip(),
        )
    except Exception as e:
        with active_analyses_lock:
            active_analyses = max(0, active_analyses - 1)
        raise e

    return {"status": "started", "session_id": session_id}


@app.get("/api/analyze/stream")
async def stream_analysis_logs(session_id: str):
    """Streams running stdout log lines using Server-Sent Events (SSE)."""
    session_dir = get_safe_session_dir(session_id)
    log_path = session_dir / "stdout.log"

    # Reset streaming state
    if session_id in log_stream_states:
        log_stream_states[session_id] = {"in_prompt": False}

    async def log_generator():
        # Wait for stdout.log file to populate
        for _ in range(50):
            if log_path.exists():
                break
            await asyncio.sleep(0.1)

        if not log_path.exists():
            yield "data: [Initializing pipeline...]\n\n"

        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            while True:
                line = f.readline()
                if line:
                    cleaned = clean_log_message(line, session_id=session_id)
                    if cleaned is not None:
                        yield f"data: {cleaned}\n\n"
                else:
                    # Look for done flag
                    done_path = session_dir / "done.txt"
                    if done_path.exists():
                        # Read final trailing lines
                        for trail_line in f.readlines():
                            cleaned_trail = clean_log_message(trail_line, session_id=session_id)
                            if cleaned_trail is not None:
                                yield f"data: {cleaned_trail}\n\n"
                        yield "data: [EOF]\n\n"
                        break
                    await asyncio.sleep(0.1)

    return StreamingResponse(log_generator(), media_type="text/event-stream")


@app.get("/api/results")
async def get_results(session_id: str):
    """Retrieves cached JSON results containing stats, insights, and charts."""
    session_dir = get_safe_session_dir(session_id)
    results_path = session_dir / "results.json"
    if not results_path.exists():
        return {"ready": False, "status": "pending"}

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if "error" in data:
            return data
        data["ready"] = True
        return data


@app.post("/api/copilot")
async def ask_copilot(
    session_id: str = Form(...),
    query: str = Form(...),
    provider: str = Form(...),
    model: str = Form(...),
    api_key: Optional[str] = Form("")
):
    """Runs a natural language query against the dataset using the Copilot agent."""
    if provider == "ollama":
        env_key_name = "OLLAMA_BASE_URL"
    elif provider in ("nvidia", "minimax"):
        env_key_name = "NVIDIA_API_KEY"
    else:
        env_key_name = f"{provider.upper()}_API_KEY"
    _load_crew()
    _apply_runtime_llm_settings(provider, model, api_key or "", env_key_name)

    session_dir = get_safe_session_dir(session_id)
    csv_path = session_dir / "cleaned.csv"
    output_dir = get_safe_output_dir(session_id)

    if not csv_path.exists():
        # Fall back to original upload if cleaning hasn't run or completed
        csv_path = session_dir / "original_upload.csv"

    if not csv_path.exists():
        raise HTTPException(status_code=400, detail="Dataset not uploaded.")

    # Bind thread-local context variables for the current request
    from config.context import current_session_csv, current_session_output_dir
    current_session_csv.set(str(csv_path))
    current_session_output_dir.set(str(output_dir))

    # Call copilot model runner
    res = _run_copilot_query(query, str(csv_path), str(output_dir))

    # Re-map absolute plot path to relative HTTP endpoint URL
    plot_url = None
    if res.get("plot_path"):
        plot_filename = Path(res["plot_path"]).name
        import urllib.parse
        plot_url = f"/api/charts/{session_id}/{urllib.parse.quote(plot_filename)}"

    return {
        "success": res["success"],
        "text":    res["text"],
        "plot_url": plot_url
    }


@app.get("/api/export-pdf")
async def get_pdf_report(session_id: str, report_title: Optional[str] = None):
    """Generates and streams back the executive PDF report."""
    session_dir = get_safe_session_dir(session_id)
    results_path = session_dir / "results.json"
    cleaned_csv = session_dir / "cleaned.csv"

    if not results_path.exists() or not cleaned_csv.exists():
        raise HTTPException(status_code=400, detail="Data analysis results not available.")

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = get_project_metadata(session_id)
    title = report_title.strip() if report_title else meta.get("report_title", meta.get("name", "Analysis Report"))
    goal = meta.get("optimized_goal") or meta.get("goal") or ""

    # Format result structure for reportlab builder
    df = read_csv_robust(cleaned_csv)
    report_dict = {
        "dataframe":      df,
        "cleaning_steps": data["cleaning_steps"],
        "relations":      data["relations"],
        "insights":       data["insights"],
        "code":           data.get("code", ""),
        "output_dir":     str(get_safe_output_dir(session_id)),
        "report_title":   title,
        "goal":           goal,
    }

    try:
        _load_crew()
        pdf_bytes = _export_pdf(report_dict)
        filename = re.sub(r"[^a-zA-Z0-9_-]", "_", title.lower())[:60] or f"report_{session_id}"
        return StreamingResponse(
            BytesIO_iterator(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


@app.post("/api/export-chat-pdf")
async def export_chat_history_pdf(
    session_id: str = Form(...),
    messages_json: str = Form(...)
):
    """Generates and downloads a PDF containing a custom selection of chat messages."""
    import json
    try:
        messages = json.loads(messages_json)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid messages format: {e}")

    try:
        _load_crew()
        pdf_bytes = _export_chat_pdf(messages, session_id)
        filename = f"chat_history_{session_id}"
        return StreamingResponse(
            BytesIO_iterator(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


@app.post("/api/export/webhook")
async def export_webhook(
    session_id: str = Form(...),
    webhook_url: str = Form(...)
):
    """(Enterprise) Export PDF report directly to a Slack/Discord webhook."""
    import requests
    output_dir = get_safe_output_dir(session_id)
    pdf_path = output_dir / f"{session_id}_report.pdf"
    
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF report not found. Run analysis first.")
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (f"report_{session_id}.pdf", f, 'application/pdf')}
            payload = {'content': f"📈 **Crewlyze AI Analysis Complete!**\nNew business insights are ready for session: `{session_id}`"}
            response = requests.post(webhook_url, data=payload, files=files, timeout=10)
            response.raise_for_status()
        return {"status": "success", "message": "Report successfully dispatched to webhook!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook dispatch failed: {str(e)}")


@app.get("/api/charts/{session_id}/{filename}")
async def serve_chart(session_id: str, filename: str):
    """Serves the generated PNG visual charts."""
    if not is_safe_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename.")
    output_dir = get_safe_output_dir(session_id)
    chart_path = (output_dir / filename).resolve()
    try:
        chart_path.relative_to(output_dir)
    except ValueError:
        raise HTTPException(status_code=400, detail="Path traversal detected.")
    if not chart_path.exists():
        raise HTTPException(status_code=404, detail="Chart not found.")
    return FileResponse(chart_path)


# ---------------------------------------------------------------------------
# Utility Streams
# ---------------------------------------------------------------------------

def BytesIO_iterator(data_bytes: bytes):
    """Simple generator to stream raw bytes back to the response."""
    yield data_bytes


# ---------------------------------------------------------------------------
# Ollama Models Fetch
# ---------------------------------------------------------------------------

@app.get("/api/ollama-models")
async def list_ollama_models(base_url: str = "http://localhost:11434"):
    """Fetches list of local Ollama models from the local Ollama service tags API."""
    import requests
    try:
        url = base_url.rstrip("/") + "/api/tags"
        response = requests.get(url, timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            if models:
                prefixed = [f"ollama/{m}" if not m.startswith("ollama/") else m for m in models]
                return {"models": prefixed}
    except Exception:
        pass
    # Fallback defaults if Ollama service is unreachable or empty
    return {"models": ["ollama/llama3", "ollama/mistral", "ollama/gemma2"]}


# ---------------------------------------------------------------------------
# Metrics & Configurations APIs
# ---------------------------------------------------------------------------

def get_local_config_path() -> Path:
    return USER_HOME / "config.json"

@app.get("/api/metrics")
async def get_performance_metrics():
    from config.metrics_tracker import get_metrics
    return get_metrics()

@app.get("/api/config")
async def get_local_config():
    cfg_path = get_local_config_path()
    if not cfg_path.exists():
        return {}
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            masked = {}
            for k, v in cfg.items():
                if v and any(keyword in k.lower() for keyword in ("key", "secret", "token")):
                    masked[k] = v[:4] + "..." + v[-4:] if len(v) > 8 else "********"
                else:
                    masked[k] = v
            return masked
    except Exception:
        return {}

@app.post("/api/config")
async def save_local_config(
    provider: str = Form(...),
    api_key: Optional[str] = Form(""),
    base_url: Optional[str] = Form("")
):
    cfg_path = get_local_config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = {}
    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            pass
    
    if provider == "ollama":
        key_name = "OLLAMA_BASE_URL"
        cfg[key_name] = base_url.strip()
    elif provider in ("nvidia", "minimax"):
        key_name = "NVIDIA_API_KEY"
    else:
        key_name = f"{provider.upper()}_API_KEY"

    if provider != "ollama":
        if api_key.strip():
            if not api_key.endswith("..."):
                cfg[key_name] = api_key.strip()
        else:
            cfg.pop(key_name, None)
            
    if base_url.strip() and provider == "custom":
        cfg["CUSTOM_BASE_URL"] = base_url.strip()
        
    try:
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        for k, v in cfg.items():
            os.environ[k] = str(v)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write config: {e}")
    return {"status": "success"}

@app.get("/api/llm/providers")
async def get_llm_providers():
    try:
        import litellm
        # Filter out extremely esoteric or broken prefixes if needed, but we return all.
        providers = sorted(list(litellm.models_by_provider.keys()))
        return {"providers": providers}
    except Exception as e:
        return {"providers": ["openai", "anthropic", "nvidia", "groq", "gemini", "ollama"], "error": str(e)}

@app.get("/api/llm/providers/{provider}/models")
async def get_llm_models(provider: str, api_key: Optional[str] = None):
    """Returns only text-to-text (chat/completion) models for a provider.
    Filters out voice, image, embedding, moderation, realtime, and other
    non-text-generation models that this project cannot use.
    If api_key is provided, dynamically queries the provider's active models list."""
    
    # Substrings that indicate a model is NOT a text-to-text chat model.
    _EXCLUDE_PATTERNS = (
        # Audio / voice / speech
        "tts", "whisper", "audio", "speech", "realtime",
        # Image generation / vision-only
        "dall-e", "stable-diffusion", "imagen", "image-generation",
        # Embeddings / Encoders
        "embed", "ada-002", "text-embedding", "search-", "embedding", "encoder",
        # Moderation / safety / guardrails
        "moderation", "content-filter", "shield", "guard",
        # Code-only non-chat (old Codex completions API)
        "code-davinci", "code-cushman", "davinci-edit", "text-davinci-edit",
        "text-ada", "text-babbage", "text-curie",
        # Deprecated / legacy completions-only
        "babbage-002", "davinci-002",
        "text-davinci-001", "text-davinci-002", "text-davinci-003",
        # Computer-use / tool-only
        "computer-use",
        # Fine-tune helper models
        "ft:davinci", "ft:babbage", "ft:curie", "ft:ada",
        # Transcription / translation
        "transcription", "translation",
        # Rerankers & Vision-specific
        "rerank", "clip", "vit", "siglip",
    )

    def _is_text_model(name: str) -> bool:
        low = name.lower()
        return not any(pat in low for pat in _EXCLUDE_PATTERNS)

    models = []
    fetched_successfully = False

    # Dynamic fetching based on user's API Key (if provided)
    if api_key and api_key.strip() and not api_key.endswith("..."):
        import requests
        clean_key = api_key.strip()
        try:
            if provider == "nvidia":
                res = requests.get(
                    "https://integrate.api.nvidia.com/v1/models",
                    headers={"Authorization": f"Bearer {clean_key}"},
                    timeout=4
                )
                if res.status_code == 200:
                    models = [f"nvidia_nim/{m['id']}" for m in res.json().get("data", [])]
                    fetched_successfully = True
            elif provider == "groq":
                res = requests.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {clean_key}"},
                    timeout=4
                )
                if res.status_code == 200:
                    models = [f"groq/{m['id']}" for m in res.json().get("data", [])]
                    fetched_successfully = True
            elif provider == "openai":
                res = requests.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {clean_key}"},
                    timeout=4
                )
                if res.status_code == 200:
                    models = [m['id'] for m in res.json().get("data", [])]
                    fetched_successfully = True
        except Exception:
            pass # Fallback to litellm list if request fails

    if not fetched_successfully:
        try:
            import litellm
            models = list(litellm.models_by_provider.get(provider, []))

            # Also grab models from the global model_list if they match the provider
            if hasattr(litellm, "model_list"):
                extra = [m for m in litellm.model_list if m.startswith(f"{provider}/")]
                if provider == "openai":
                    extra.extend([m for m in litellm.model_list if "gpt-" in m and "/" not in m])
                models.extend(extra)
        except Exception as e:
            return {"models": [], "error": str(e)}

    # Deduplicate, filter, sort
    models = sorted(set(m for m in models if _is_text_model(m)))
    return {"models": models}

@app.post("/api/validate-key")
async def validate_key(
    provider: str = Form(...),
    model: str = Form(...),
    api_key: Optional[str] = Form(""),
):
    """Pings the LLM provider to validate the model identifier and API key."""
    try:
        # Load crew module functions lazily if needed
        _load_crew()
        
        # Get actual env key name
        if provider == "ollama":
            env_key_name = "OLLAMA_BASE_URL"
        elif provider in ("nvidia", "minimax"):
            env_key_name = "NVIDIA_API_KEY"
        else:
            env_key_name = f"{provider.upper()}_API_KEY"
            
        result = _validate_llm_connection(provider, model, api_key)
        if not result.get("valid"):
            raise HTTPException(status_code=400, detail=result.get("message", "Validation failed"))
        return {"status": "success", "message": result.get("message")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")


# ---------------------------------------------------------------------------
# Project Management APIs
# ---------------------------------------------------------------------------

@app.get("/api/projects")
async def list_projects():
    """Lists all available data analysis projects/sessions."""
    projects = []
    if SESSIONS_DIR.exists():
        for p in SESSIONS_DIR.iterdir():
            if p.is_dir():
                try:
                    meta = get_project_metadata(p.name)
                    if meta:
                        projects.append(meta)
                except Exception:
                    pass
    # Sort projects: newest first
    projects.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return projects

@app.post("/api/projects")
async def create_project(
    name: str = Form(...),
    report_title: str = Form(""),
    goal: str = Form(""),
    file: UploadFile = File(...)
):
    """Creates a new project context and uploads the dataset CSV."""
    project_id = uuid.uuid4().hex[:12]
    session_dir = get_safe_session_dir(project_id)
    session_dir.mkdir(parents=True, exist_ok=True)

    file_path = session_dir / "original_upload.csv"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Pre-configure fresh log files
    log_path = session_dir / "stdout.log"
    with open(log_path, "w") as f:
        f.write("Project created. Dataset uploaded successfully.\n")

    meta = {
        "id": project_id,
        "name": name.strip(),
        "report_title": report_title.strip() or f"{name.strip()} Executive Analysis",
        "goal": goal.strip(),
        "optimized_goal": "",
        "filename": file.filename,
        "size": file_path.stat().st_size,
        "created_at": time.time() * 1000,
        "status": "idle"
    }
    save_project_metadata(project_id, meta)

    return meta

@app.post("/api/projects/{project_id}/rename")
async def rename_project(project_id: str, name: str = Form(...)):
    """Renames an existing project context."""
    session_dir = get_safe_session_dir(project_id)
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    meta = get_project_metadata(project_id)
    meta["name"] = name.strip()
    save_project_metadata(project_id, meta)

    return meta


@app.post("/api/projects/{project_id}/tweak-relations")
async def tweak_relations(project_id: str, relations_text: str = Form(...)):
    """Saves tweaked relationships back to the results cache."""
    session_dir = get_safe_session_dir(project_id)
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    results_path = session_dir / "results.json"
    
    # Ensure results.json structure is present even if not analysed yet
    res_data = {}
    if results_path.exists():
        try:
            with open(results_path, "r", encoding="utf-8") as f:
                res_data = json.load(f)
        except Exception:
            pass
            
    res_data["relations"] = relations_text.strip()
    
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(res_data, f, indent=2)
        
    return {"status": "success", "relations": res_data["relations"]}

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Deletes all session files, artifacts, and outputs of a project."""
    session_dir = get_safe_session_dir(project_id)
    output_dir = get_safe_output_dir(project_id)

    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    shutil.rmtree(session_dir, ignore_errors=True)
    if output_dir.exists():
        shutil.rmtree(output_dir, ignore_errors=True)

    return {"status": "deleted", "id": project_id}


@app.get("/api/projects/{project_id}/export-zip")
async def export_project_zip(project_id: str):
    """Exports the entire project (metadata, data files, results, and generated charts) as a ZIP file."""
    session_dir = get_safe_session_dir(project_id)
    output_dir = get_safe_output_dir(project_id)
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Zip session files
        for root, dirs, files in os.walk(session_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = Path("session") / file_path.relative_to(session_dir)
                zip_file.write(file_path, arcname=arcname)
        # Zip output files (charts)
        if output_dir.exists():
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = Path("outputs") / file_path.relative_to(output_dir)
                    zip_file.write(file_path, arcname=arcname)

    zip_buffer.seek(0)
    meta = get_project_metadata(project_id)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", meta.get("name", "project").lower())
    filename = f"{safe_name}_{project_id}.zip"
    return StreamingResponse(
        BytesIO_iterator(zip_buffer.getvalue()),
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.post("/api/projects/import-zip")
async def import_project_zip(file: UploadFile = File(...)):
    """Imports a project from a ZIP file and registers it in the system."""
    zip_contents = await file.read()
    zip_buffer = BytesIO(zip_contents)
    
    project_id = uuid.uuid4().hex[:12]
    temp_dir = DATA_DIR / "temp_import" / project_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    target_project_id = project_id
    session_dir = None
    output_dir = None
    try:
        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            # Zip Slip check:
            for member in zip_file.infolist():
                if ".." in member.filename or member.filename.startswith("/") or member.filename.startswith("\\"):
                    raise HTTPException(status_code=400, detail=f"Invalid zip entry: {member.filename}")
                target_path = (temp_dir / member.filename).resolve()
                try:
                    target_path.relative_to(temp_dir.resolve())
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Zip Slip detected: {member.filename}")
            zip_file.extractall(temp_dir)
            
        # Verify metadata.json exists
        meta_file = temp_dir / "session" / "metadata.json"
        if not meta_file.exists():
            raise HTTPException(status_code=400, detail="Invalid zip format: missing metadata.json")
            
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)
            
        orig_project_id = meta.get("id")
        if orig_project_id:
            if not is_safe_id(orig_project_id):
                raise HTTPException(status_code=400, detail="Invalid project ID in metadata.")
            target_project_id = orig_project_id
            
        # Check if project conflicts. If so, generate new ID
        session_dir = get_safe_session_dir(target_project_id)
        if session_dir.exists():
            target_project_id = uuid.uuid4().hex[:12]
            session_dir = get_safe_session_dir(target_project_id)
            meta["id"] = target_project_id
            meta["name"] = f"{meta.get('name', 'Imported')} (Copy)"
            
        output_dir = get_safe_output_dir(target_project_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy session files
        for item in (temp_dir / "session").iterdir():
            if item.is_file():
                if not is_safe_filename(item.name):
                    continue
                shutil.copy2(item, session_dir / item.name)
                
        # Copy outputs
        if (temp_dir / "outputs").exists():
            output_dir.mkdir(parents=True, exist_ok=True)
            for item in (temp_dir / "outputs").iterdir():
                if item.is_file():
                    if not is_safe_filename(item.name):
                        continue
                    shutil.copy2(item, output_dir / item.name)
                    
        # Update metadata.json
        meta["id"] = target_project_id
        if meta.get("thumbnail"):
            # Update thumbnail link with new project ID
            thumb_parts = meta["thumbnail"].split("/")
            if len(thumb_parts) >= 5:
                thumb_parts[3] = target_project_id
                meta["thumbnail"] = "/".join(thumb_parts)
                
        with open(session_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
            
        return meta
    except Exception as e:
        if session_dir and session_dir.exists():
            shutil.rmtree(session_dir, ignore_errors=True)
        if output_dir and output_dir.exists():
            shutil.rmtree(output_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.get("/api/projects/{project_id}/preview")
async def get_dynamic_preview(project_id: str):
    """Dynamically reads the latest state of the CSV and returns a 100-row preview, column names, shapes, and types."""
    session_dir = get_safe_session_dir(project_id)
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    cleaned_csv = session_dir / "cleaned.csv"
    original_csv = session_dir / "original_upload.csv"
    csv_path = cleaned_csv if cleaned_csv.exists() else original_csv

    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="CSV not found.")

    try:
        df = read_csv_robust(str(csv_path))
        rows_count, cols_count = df.shape
        preview = df.head(100).fillna("").to_dict(orient="records")
        col_types = {col: str(dtype) for col, dtype in df.dtypes.items()}
        columns = list(df.columns)

        # Update cache in results.json if it exists
        results_path = session_dir / "results.json"
        if results_path.exists():
            try:
                with open(results_path, "r", encoding="utf-8") as f:
                    res_data = json.load(f)
                res_data["preview"] = preview
                res_data["rows_count"] = rows_count
                res_data["cols_count"] = cols_count
                with open(results_path, "w", encoding="utf-8") as f:
                    json.dump(res_data, f, indent=2)
            except Exception:
                pass

        return {
            "columns": columns,
            "col_types": col_types,
            "rows_count": rows_count,
            "cols_count": cols_count,
            "preview": preview
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load preview: {str(e)}")


@app.get("/api/projects/{project_id}/download-csv")
async def download_project_csv(project_id: str):
    """Downloads the cleaned dataset CSV for the specified project."""
    session_dir = get_safe_session_dir(project_id)
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    cleaned_csv = session_dir / "cleaned.csv"
    original_csv = session_dir / "original_upload.csv"
    csv_path = cleaned_csv if cleaned_csv.exists() else original_csv

    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="CSV not found.")

    try:
        meta = get_project_metadata(project_id)
        orig_name = meta.get("filename", "dataset.csv")
    except Exception:
        orig_name = "dataset.csv"

    base_name = orig_name.rsplit(".", 1)[0] if "." in orig_name else orig_name
    download_filename = f"{base_name}_cleaned.csv"

    return FileResponse(csv_path, media_type="text/csv", filename=download_filename)


# ---------------------------------------------------------------------------
# Frontend Static Mounts
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
web_dir = BASE_DIR / "web"
assets_dir = BASE_DIR / "assets"

app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")


# ── Server Boot ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    # Start server on 8000
    print("\n" + "=" * 50)
    print("Crewlyze Web Platform")
    print("Local URL: http://localhost:8000")
    print("=" * 50 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
