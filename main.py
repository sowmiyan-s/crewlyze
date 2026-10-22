# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
FastAPI Server backend for the Crewlyze application.
Orchestrates modular APIRouters, serves static web assets, and provides CLI entrypoints.
"""

import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import json
from pathlib import Path
from contextlib import asynccontextmanager

# Initialize central environment loader
try:
    from config.env_loader import ensure_env_loaded
    env_info = ensure_env_loaded()
except Exception as e:
    print(f"[Warning] Environment initialization failed: {e}")

try:
    from config.cli_formatter import print_banner, log_info, log_success, log_warn, log_error, print_server_ready
except Exception:
    pass

# Suppress telemetry noise
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Import dependencies and shared state
from api.dependencies import (
    USER_HOME,
    DATA_DIR,
    SESSIONS_DIR,
    OUTPUTS_DIR,
    CURRENT_APP_VERSION,
    is_safe_id,
    is_safe_filename,
    validate_project_id,
    get_safe_session_dir,
    get_safe_output_dir,
    get_project_metadata,
    save_project_metadata,
    get_local_config_path,
    parse_bool,
    is_valid_url,
    clean_log_message,
    log_stream_states,
    load_crew_modules,
)

# Import modular routers
from api.routers import config, projects, chat, export, analysis

# ---------------------------------------------------------------------------
# Server Lifespan & Crash Recovery Watchdog
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Scan all session metadata files on boot and reset any stale projects stuck in running status."""
    try:
        if SESSIONS_DIR.exists() and SESSIONS_DIR.is_dir():
            for session_dir in SESSIONS_DIR.iterdir():
                if session_dir.is_dir():
                    metadata_path = session_dir / "metadata.json"
                    if metadata_path.exists():
                        try:
                            with open(metadata_path, "r", encoding="utf-8") as f:
                                meta = json.load(f)
                            if meta.get("status") == "running":
                                meta["status"] = "interrupted"
                                meta["error"] = "Process interrupted by server restart."
                                done_path = session_dir / "done.txt"
                                if not done_path.exists():
                                    with open(done_path, "w", encoding="utf-8") as df:
                                        df.write("done")
                                with open(metadata_path, "w", encoding="utf-8") as f:
                                    json.dump(meta, f, indent=2)
                                print(f"Reset stale running session: {session_dir.name}")
                        except Exception as e:
                            print(f"Failed to reset metadata for {session_dir.name}: {e}")
    except Exception as e:
        print(f"Error during startup stale session cleanup: {e}")
    yield

# ---------------------------------------------------------------------------
# FastAPI App Initialization
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Crewlyze API",
    description="Autonomous Multi-Agent Business Intelligence and Data Engineering Platform",
    version=CURRENT_APP_VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional Enterprise Auth
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
# Mount Routers
# ---------------------------------------------------------------------------

app.include_router(config.router)
app.include_router(projects.router)
app.include_router(chat.router)
app.include_router(export.router)
app.include_router(analysis.router)

# ---------------------------------------------------------------------------
# Frontend Static Mounts
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
web_dir = BASE_DIR / "web"
assets_dir = BASE_DIR / "assets"

web_dir.mkdir(parents=True, exist_ok=True)
assets_dir.mkdir(parents=True, exist_ok=True)

if not list(assets_dir.glob("*")):
    alt_assets = web_dir / "assets"
    if alt_assets.exists() and list(alt_assets.glob("*")):
        assets_dir = alt_assets

app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")

# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def cli_main():
    """CLI entry point for global crewlyze command and python main.py execution."""
    _user_home = os.environ.get("USERPROFILE")
    if _user_home:
        _venv_python = os.path.join(_user_home, ".crewlyze", "venv", "Scripts", "python.exe")
        if os.path.isfile(_venv_python):
            try:
                if os.path.abspath(sys.executable).lower() != os.path.abspath(_venv_python).lower():
                    import subprocess
                    _cmd = [_venv_python] + sys.argv
                    sys.exit(subprocess.call(_cmd))
            except Exception:
                pass

    import uvicorn
    import webbrowser
    import threading
    import time

    try:
        from config.cli_formatter import print_banner, print_server_ready
        print_banner()
        print_server_ready("http://127.0.0.1:8000", 8000)
    except Exception:
        print("Crewlyze server running at http://127.0.0.1:8000")

    def _open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open("http://127.0.0.1:8000")
        except Exception:
            pass

    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run("main:app", host="127.0.0.1", port=8000)

if __name__ == "__main__":
    cli_main()
