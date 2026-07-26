# Crewlyze Environment & Directory Manager
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

USER_HOME_DIR = Path.home() / ".crewlyze"
PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent

DEFAULT_ENV_CONTENT = """# Crewlyze Configuration File
# Autonomous Multi-Agent BI Platform

# ── LLM Configuration ────────────────────────────────────────────────────────
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=
OPENAI_API_KEY=
GROQ_API_KEY=
GEMINI_API_KEY=
ANTHROPIC_API_KEY=
LLM_MODEL=nvidia_nim/meta/llama-3.1-8b-instruct

# ── Workspace Directories ────────────────────────────────────────────────────
LOG_LEVEL=INFO
CREWAI_TELEMETRY_OPT_OUT=true
OTEL_SDK_DISABLED=true
"""

def ensure_env_loaded():
    """
    Ensures environment variables and .env files are initialized properly across any environment.
    Searches ~/.crewlyze/.env, project root .env, and CWD .env.
    Auto-creates ~/.crewlyze/.env if missing.
    """
    try:
        USER_HOME_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[Warning] Could not create home directory {USER_HOME_DIR}: {e}")

    # Create home .env template if missing
    home_env = USER_HOME_DIR / ".env"
    if not home_env.exists():
        try:
            with open(home_env, "w", encoding="utf-8") as f:
                f.write(DEFAULT_ENV_CONTENT)
        except Exception as e:
            print(f"[Warning] Could not write default .env to {home_env}: {e}")

    # Load order: Home .env -> Project .env -> CWD .env (later overrides earlier)
    load_dotenv(dotenv_path=home_env, override=False)
    
    project_env = PROJECT_ROOT_DIR / ".env"
    if project_env.exists():
        load_dotenv(dotenv_path=project_env, override=True)

    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists() and cwd_env.resolve() != project_env.resolve():
        load_dotenv(dotenv_path=cwd_env, override=True)

    # Set default runtime environment fallback variables if missing
    os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "true")
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    os.environ.setdefault("LOG_LEVEL", "INFO")
    
    if "CREWLYZE_DATA_DIR" not in os.environ:
        os.environ["CREWLYZE_DATA_DIR"] = str(USER_HOME_DIR / "data")
    if "CREWLYZE_OUTPUTS_DIR" not in os.environ:
        os.environ["CREWLYZE_OUTPUTS_DIR"] = str(USER_HOME_DIR / "outputs")

    # Ensure runtime data and outputs subdirectories exist
    try:
        Path(os.environ["CREWLYZE_DATA_DIR"]).mkdir(parents=True, exist_ok=True)
        (Path(os.environ["CREWLYZE_DATA_DIR"]) / "sessions").mkdir(parents=True, exist_ok=True)
        Path(os.environ["CREWLYZE_OUTPUTS_DIR"]).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[Warning] Could not initialize runtime directories: {e}")

    return {
        "user_home": USER_HOME_DIR,
        "data_dir": Path(os.environ["CREWLYZE_DATA_DIR"]),
        "outputs_dir": Path(os.environ["CREWLYZE_OUTPUTS_DIR"]),
    }
