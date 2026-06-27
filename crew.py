# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Main crew orchestration module.

Key improvements over the original:
- Per-session isolated paths (data/sessions/<id>/ and outputs/<id>/)
- Original CSV backed up before the cleaner agent runs
- Agent/task factory pattern — fresh LLM config on every call
- importlib.reload() hack removed entirely
- Unused webbrowser import removed
- Bare-except replaced with specific handling
"""

import logging
import os
import shutil
import sys
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Suppress noisy loggers
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("opentelemetry").setLevel(logging.ERROR)

# Disable CrewAI telemetry
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

try:
    from crewai import Crew
except ImportError as exc:
    print(f"ERROR: {exc}\nRun: pip install crewai")
    sys.exit(1)

from workflows.pipeline import make_pipeline


# ---------------------------------------------------------------------------
# Session cleanup helper
# ---------------------------------------------------------------------------

def _cleanup_old_sessions(max_age_hours: int = 24) -> None:
    """Remove session directories older than *max_age_hours*."""
    sessions_root = Path("data") / "sessions"
    outputs_root  = Path("outputs")

    for root in (sessions_root, outputs_root):
        if not root.exists():
            continue
        cutoff = time.time() - max_age_hours * 3600
        for session_dir in root.iterdir():
            if session_dir.is_dir():
                try:
                    if session_dir.stat().st_mtime < cutoff:
                        shutil.rmtree(session_dir, ignore_errors=True)
                except OSError:
                    pass


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_crew(csv_path: str, session_id: str = "default") -> dict:
    """
    Run the full multi-agent analysis pipeline on *csv_path*.

    Parameters
    ----------
    csv_path   : Path to the uploaded CSV file.
    session_id : Unique identifier for this session (isolates files/outputs).

    Returns
    -------
    dict with keys: dataframe, cleaning_steps, relations, insights, code, output_dir
    """
    _cleanup_old_sessions()

    # ── Per-session directories ───────────────────────────────────────────────
    session_data_dir   = Path("data") / "sessions" / session_id
    session_output_dir = Path("outputs") / session_id
    session_data_dir.mkdir(parents=True, exist_ok=True)
    session_output_dir.mkdir(parents=True, exist_ok=True)

    # Clean up previous visualizations for this session only
    for existing_png in session_output_dir.glob("*.png"):
        existing_png.unlink(missing_ok=True)

    print("=" * 50)
    print("Multi Agent Data Analysis with Crew AI")
    print("=" * 50)

    # ── Load original dataset ─────────────────────────────────────────────────
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Upload not found at: {csv_path}")

    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    cols_preview = ", ".join(df.columns[:10])
    if len(df.columns) > 10:
        cols_preview += "..."
    print(f"Columns: {cols_preview}")

    # ── Backup original before agents touch it ────────────────────────────────
    original_backup = session_data_dir / "original.csv"
    cleaned_path    = session_data_dir / "cleaned.csv"

    df.to_csv(original_backup, index=False)
    df.to_csv(cleaned_path, index=False)
    print(f"Original backed up -> {original_backup}")
    print(f"Working copy created -> {cleaned_path}\n")

    # ── Build fresh agents + tasks ────────────────────────────────────────────
    agents, tasks = make_pipeline(session_id)

    crew = Crew(
        agents=agents,
        tasks=tasks,
        max_rpm=15,
        cache=True,
        verbose=True,
    )

    # ── Run the crew ──────────────────────────────────────────────────────────
    try:
        crew.kickoff()
    except Exception as exc:
        print(f"Crew execution error: {exc}")
        raise  # Let the Streamlit layer catch and display it properly

    # ── Extract task outputs ──────────────────────────────────────────────────
    def _safe_output(task) -> str:
        if task.output is None:
            return ""
        return str(task.output.raw if hasattr(task.output, "raw") else task.output)

    clean_output     = _safe_output(tasks[0])
    relation_output  = _safe_output(tasks[1])
    insights_output  = _safe_output(tasks[2])
    visualize_output = _safe_output(tasks[3])

    # ── Reload cleaned dataframe ──────────────────────────────────────────────
    try:
        cleaned_df = pd.read_csv(cleaned_path)
    except Exception:
        # Fall back to original with explicit warning — never silently
        print("WARNING: Could not load cleaned CSV. Falling back to original data.")
        cleaned_df = df

    return {
        "dataframe":      cleaned_df,
        "cleaning_steps": clean_output,
        "relations":      relation_output,
        "insights":       insights_output,
        "code":           visualize_output,
        "output_dir":     str(session_output_dir),
    }


# ---------------------------------------------------------------------------
# CLI entry point (unchanged behaviour)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    default_path = (Path.cwd() / "data" / "TB_Burden_Country.csv").resolve()
    path = input(f"Enter the path to your CSV file (default: {default_path.name}): ") or str(default_path)
    report = run_crew(path, session_id="cli")
    if report:
        print("\nAnalysis Complete.")
        print("Multi Agent Data Analysis with Crew AI")
        print("Prithiv.A.K  Sebin.S  Sowmiyan.S")
