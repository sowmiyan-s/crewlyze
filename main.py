# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
FastAPI Server backend for the Agentic Data Analyst application.
Serves static HTML/JS/CSS assets and exposes REST APIs + Server-Sent Events (SSE)
for streaming real-time analysis logs.
"""

import os
import sys
import json
import uuid
import asyncio
import threading
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Core analysis engines
from crew import run_crew
from ui.copilot import run_copilot_query
from ui.export import export_pdf

# Suppress warnings
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"]        = "true"

app = FastAPI(
    title="Agentic Data Analyst API",
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
# State & Directory Setup
# ---------------------------------------------------------------------------

DATA_DIR = Path("data")
SESSIONS_DIR = DATA_DIR / "sessions"
OUTPUTS_DIR = Path("outputs")

for path in (DATA_DIR, SESSIONS_DIR, OUTPUTS_DIR):
    path.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Background Task Pipeline
# ---------------------------------------------------------------------------

def run_crew_in_background(
    session_id: str,
    csv_path: str,
    provider: str,
    model: str,
    api_key: str,
    env_key_name: str,
    cooldown: int
):
    """
    Orchestrates the CrewAI pipeline in a background thread, writing all
    stdout progress to a tail-able stdout.log file and serializing results.
    """
    # 1. Inject thread-isolated LLM configurations
    os.environ["LLM_PROVIDER"] = provider
    os.environ["LLM_MODEL"]    = model
    os.environ["API_COOLDOWN"]  = str(cooldown)
    if api_key:
        os.environ[env_key_name] = api_key

    session_dir = SESSIONS_DIR / session_id
    log_path = session_dir / "stdout.log"
    done_path = session_dir / "done.txt"
    results_path = session_dir / "results.json"

    # Clean up previous state
    done_path.unlink(missing_ok=True)
    results_path.unlink(missing_ok=True)

    # 2. Redirect stdout and kickoff
    with open(log_path, "w", encoding="utf-8", errors="replace") as log_file:
        import contextlib
        with contextlib.redirect_stdout(log_file):
            try:
                print("⚙️ Initializing multi-agent workflows...")
                result = run_crew(csv_path, session_id=session_id)
                
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
                preview_data = result["dataframe"].head(100).to_dict(orient="records")
                serializable_result["preview"] = preview_data

                with open(results_path, "w", encoding="utf-8") as f:
                    json.dump(serializable_result, f, indent=2)
                
                print("\n✅ Analysis complete! Ready to render dashboard.")

            except Exception as e:
                import traceback
                print(f"\n❌ Pipeline failed: {e}", file=sys.stderr)
                traceback.print_exc(file=log_file)
                
                error_result = {"error": str(e)}
                with open(results_path, "w", encoding="utf-8") as f:
                    json.dump(error_result, f, indent=2)
            finally:
                # Write done sentinel to stop EventSource streams
                with open(done_path, "w") as f:
                    f.write("done")


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Uploads the dataset and registers a unique user session ID."""
    session_id = uuid.uuid4().hex[:12]
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    file_path = session_dir / "original_upload.csv"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Pre-configure fresh log files
    log_path = session_dir / "stdout.log"
    with open(log_path, "w") as f:
        f.write("Dataset uploaded successfully.\n")

    return {
        "session_id": session_id,
        "filename": file.filename,
        "size": file_path.stat().st_size
    }


@app.post("/api/analyze")
async def trigger_analysis(
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
    provider: str = Form(...),
    model: str = Form(...),
    api_key: Optional[str] = Form(""),
    cooldown: int = Form(5)
):
    """Launches the CrewAI analysis process in the background."""
    session_dir = SESSIONS_DIR / session_id
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

    # Spawn thread-safe background execution
    background_tasks.add_task(
        run_crew_in_background,
        session_id=session_id,
        csv_path=str(csv_path),
        provider=provider,
        model=model,
        api_key=api_key,
        env_key_name=env_key_name,
        cooldown=cooldown
    )

    return {"status": "started", "session_id": session_id}


@app.get("/api/analyze/stream")
async def stream_analysis_logs(session_id: str):
    """Streams running stdout log lines using Server-Sent Events (SSE)."""
    session_dir = SESSIONS_DIR / session_id
    log_path = session_dir / "stdout.log"

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
                    clean_line = line.replace("\n", "").replace("\r", "")
                    yield f"data: {clean_line}\n\n"
                else:
                    # Look for done flag
                    done_path = session_dir / "done.txt"
                    if done_path.exists():
                        # Read final trailing lines
                        for trail_line in f.readlines():
                            clean_trail = trail_line.replace("\n", "").replace("\r", "")
                            yield f"data: {clean_trail}\n\n"
                        yield "data: [EOF]\n\n"
                        break
                    await asyncio.sleep(0.1)

    return StreamingResponse(log_generator(), media_type="text/event-stream")


@app.get("/api/results")
async def get_results(session_id: str):
    """Retrieves cached JSON results containing stats, insights, and charts."""
    results_path = SESSIONS_DIR / session_id / "results.json"
    if not results_path.exists():
        raise HTTPException(status_code=404, detail="Results not ready or not found.")

    with open(results_path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/copilot")
async def ask_copilot(
    session_id: str = Form(...),
    query: str = Form(...),
    provider: str = Form(...),
    model: str = Form(...),
    api_key: Optional[str] = Form("")
):
    """Runs a natural language query against the dataset using the Copilot agent."""
    # Match API key settings
    if provider == "ollama":
        env_key_name = "OLLAMA_BASE_URL"
    elif provider in ("nvidia", "minimax"):
        env_key_name = "NVIDIA_API_KEY"
    else:
        env_key_name = f"{provider.upper()}_API_KEY"

    # Inject variables before execution
    os.environ["LLM_PROVIDER"] = provider
    os.environ["LLM_MODEL"]    = model
    if api_key:
        os.environ[env_key_name] = api_key

    csv_path = SESSIONS_DIR / session_id / "cleaned.csv"
    output_dir = OUTPUTS_DIR / session_id

    if not csv_path.exists():
        # Fall back to original upload if cleaning hasn't run or completed
        csv_path = SESSIONS_DIR / session_id / "original_upload.csv"

    if not csv_path.exists():
        raise HTTPException(status_code=400, detail="Dataset not uploaded.")

    # Call copilot model runner
    res = run_copilot_query(query, str(csv_path), str(output_dir))

    # Re-map absolute plot path to relative HTTP endpoint URL
    plot_url = None
    if res.get("plot_path"):
        plot_filename = Path(res["plot_path"]).name
        plot_url = f"/api/charts/{session_id}/{plot_filename}"

    return {
        "success": res["success"],
        "text":    res["text"],
        "plot_url": plot_url
    }


@app.get("/api/export-pdf")
async def get_pdf_report(session_id: str):
    """Generates and streams back the executive PDF report."""
    results_path = SESSIONS_DIR / session_id / "results.json"
    cleaned_csv = SESSIONS_DIR / session_id / "cleaned.csv"

    if not results_path.exists() or not cleaned_csv.exists():
        raise HTTPException(status_code=400, detail="Data analysis results not available.")

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Format result structure for reportlab builder
    df = pd.read_csv(cleaned_csv)
    report_dict = {
        "dataframe":      df,
        "cleaning_steps": data["cleaning_steps"],
        "relations":      data["relations"],
        "insights":       data["insights"],
        "code":           data.get("code", ""),
        "output_dir":     str(OUTPUTS_DIR / session_id),
    }

    try:
        pdf_bytes = export_pdf(report_dict)
        return StreamingResponse(
            BytesIO_iterator(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=data_report_{session_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


@app.get("/api/charts/{session_id}/{filename}")
async def serve_chart(session_id: str, filename: str):
    """Serves the generated PNG visual charts."""
    chart_path = OUTPUTS_DIR / session_id / filename
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
# Frontend Static Mounts
# ---------------------------------------------------------------------------

# Mount custom SPA frontend
web_dir = Path("web")
web_dir.mkdir(exist_ok=True)

# Mount statics (served at /app.js, /style.css, etc.)
app.mount("/", StaticFiles(directory="web", html=True), name="web")


# ── Server Boot ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    # Start server on 8000
    print("\n" + "=" * 50)
    print("Agentic Data Analyst Web Platform")
    print("Local URL: http://localhost:8000")
    print("=" * 50 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
