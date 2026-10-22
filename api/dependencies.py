import os
import sys
import re
import json
import asyncio
import threading
import time
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, UploadFile

# Base Paths
USER_HOME = Path.home() / ".crewlyze"
DATA_DIR = Path(os.getenv("CREWLYZE_DATA_DIR", str(USER_HOME / "data")))
SESSIONS_DIR = DATA_DIR / "sessions"
OUTPUTS_DIR = Path(os.getenv("CREWLYZE_OUTPUTS_DIR", str(USER_HOME / "outputs")))

for p in (DATA_DIR, SESSIONS_DIR, OUTPUTS_DIR):
    p.mkdir(exist_ok=True, parents=True)

# Application Version
CURRENT_APP_VERSION = "1.2.4"
try:
    _pkg_path = Path(__file__).resolve().parent.parent / "package.json"
    if _pkg_path.exists():
        with open(_pkg_path, "r", encoding="utf-8") as _f:
            CURRENT_APP_VERSION = json.load(_f).get("version", CURRENT_APP_VERSION)
except Exception:
    pass

# Security & Validation
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

def parse_bool(value: Optional[str]) -> bool:
    return bool(value and str(value).strip().lower() not in {"false", "0", "off", "no", ""})

MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500MB safety ceiling

async def save_upload_file_safely(file: UploadFile, dest_path: Path) -> int:
    """Streams file upload to destination path while enforcing the MAX_UPLOAD_SIZE ceiling."""
    total_bytes = 0
    chunk_size = 1024 * 1024  # 1MB chunk
    with open(dest_path, "wb") as buffer:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > MAX_UPLOAD_SIZE:
                buffer.close()
                dest_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail=f"File exceeds maximum allowed upload size (500MB).")
            buffer.write(chunk)
    return total_bytes

def is_valid_url(url: Optional[str]) -> bool:
    """Validate that a URL is a non-empty HTTP/HTTPS web address."""
    if not url or not isinstance(url, str):
        return False
    u = url.strip()
    return (u.startswith("http://") or u.startswith("https://")) and len(u) > 10

# Configuration Management
def get_local_config_path() -> Path:
    return USER_HOME / "config.json"

config_lock = asyncio.Lock()

# Project Metadata Management
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

# Log Sanitization & Formatting
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
log_stream_states = {}

def clean_log_message(line: str, session_id: Optional[str] = None) -> Optional[str]:
    """Strip ANSI color codes, ignore noisy messages, and format thoughts/actions nicely."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    line = ANSI_ESCAPE.sub('', line)
    stripped = line.strip()
    if not stripped:
        return None

    line_lower = stripped.lower()
    
    if log_level == "ERROR":
        if "warning" in line_lower or "error" in line_lower or "exception" in line_lower:
            if "error" in line_lower or "exception" in line_lower:
                return f"[Error] {stripped}"
            return f"[Warning] {stripped}"
        return None

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

    if log_level != "DEBUG" and session_id:
        if session_id not in log_stream_states:
            log_stream_states[session_id] = {"in_prompt": False}
        state = log_stream_states[session_id]
        
        if "prompt after formatting:" in line_lower or "use the following format:" in line_lower:
            state["in_prompt"] = True
            return None
            
        if state["in_prompt"]:
            stop_triggers = ["thought:", "action:", "action input:", "response:", "observation:", "entering new", "finished chain"]
            if any(trig in line_lower for trig in stop_triggers):
                state["in_prompt"] = False
            else:
                return None

    if log_level != "DEBUG":
        if stripped.startswith("[DEBUG]:") or stripped.startswith("[INFO]:"):
            if "working agent" in line_lower:
                agent_name = stripped.split(":", 2)[-1].strip()
                return f"[Agent] {agent_name} is active..."
            return None
    else:
        if stripped.startswith("[DEBUG]:"):
            return f"[DEBUG] {stripped[8:].strip()}"
        if stripped.startswith("[INFO]:"):
            return f"[INFO] {stripped[7:].strip()}"

    if "entering new crewagentexecutor chain" in line_lower:
        return "[Task] Starting agent execution task..."
    if "finished chain" in line_lower:
        return "[Task] Execution task completed."
    
    if stripped.startswith("Thought:"):
        return f"[Thought] {stripped[8:].strip()}"
        
    if stripped.startswith("Action:"):
        return f"[Calling Tool] {stripped[7:].strip()}"
        
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

# Lazy Crew & Module Loader
_run_crew = None
_apply_runtime_llm_settings = None
_validate_llm_connection = None
_run_copilot_query = None
_export_pdf = None
_export_chat_pdf = None
_run_auto_relation_fallback = None
_run_auto_insights_fallback = None
_run_auto_predictive_fallback = None
_run_auto_anomaly_fallback = None
_run_auto_trend_fallback = None
_run_auto_visualizer_fallback = None

def load_crew_modules():
    global _run_crew, _apply_runtime_llm_settings, _validate_llm_connection
    global _run_copilot_query, _export_pdf, _export_chat_pdf
    global _run_auto_relation_fallback, _run_auto_insights_fallback
    global _run_auto_predictive_fallback, _run_auto_anomaly_fallback
    global _run_auto_trend_fallback, _run_auto_visualizer_fallback
    if _run_crew is None:
        from crew import (
            run_crew as _rc,
            _run_auto_relation_fallback as _rarf,
            _run_auto_insights_fallback as _raif,
            _run_auto_predictive_fallback as _rapf,
            _run_auto_anomaly_fallback as _raaf,
            _run_auto_trend_fallback as _ratf,
            _run_auto_visualizer_fallback as _ravf,
        )
        from config.llm_config import apply_runtime_llm_settings as _arls, validate_llm_connection as _vlc
        from ui.copilot import run_copilot_query as _rcq
        from ui.export import export_pdf as _ep, export_chat_pdf as _ecp
        _run_crew = _rc
        _run_auto_relation_fallback = _rarf
        _run_auto_insights_fallback = _raif
        _run_auto_predictive_fallback = _rapf
        _run_auto_anomaly_fallback = _raaf
        _run_auto_trend_fallback = _ratf
        _run_auto_visualizer_fallback = _ravf
        _apply_runtime_llm_settings = _arls
        _validate_llm_connection = _vlc
        _run_copilot_query = _rcq
        _export_pdf = _ep
        _export_chat_pdf = _ecp
    return {
        "run_crew": _run_crew,
        "apply_runtime_llm_settings": _apply_runtime_llm_settings,
        "validate_llm_connection": _validate_llm_connection,
        "run_copilot_query": _run_copilot_query,
        "export_pdf": _export_pdf,
        "export_chat_pdf": _export_chat_pdf,
        "run_auto_relation_fallback": _run_auto_relation_fallback,
        "run_auto_insights_fallback": _run_auto_insights_fallback,
        "run_auto_predictive_fallback": _run_auto_predictive_fallback,
        "run_auto_anomaly_fallback": _run_auto_anomaly_fallback,
        "run_auto_trend_fallback": _run_auto_trend_fallback,
        "run_auto_visualizer_fallback": _run_auto_visualizer_fallback,
    }

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

# Concurrency Controls
MAX_CONCURRENT_ANALYSES = 2
active_analyses = 0
active_analyses_lock = threading.Lock()
