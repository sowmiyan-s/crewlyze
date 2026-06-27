# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Main crew orchestration module.

Performance improvements in this version:
- build_dataset_profile() computes a rich data summary before agents start,
  eliminating 6-8 LLM tool-call round-trips across the pipeline.
- Large files (> 10 000 rows) are sampled to 5 000 rows for profiling;
  the cleaner still operates on the full dataset.
- relation_task and insight_task run in PARALLEL via ThreadPoolExecutor,
  saving the time of one full sequential task slot.
- visualize_task receives the actual relation + insight outputs injected
  into its description (rather than relying on CrewAI's context= mechanism
  which requires all tasks to live in the same Crew instance).
- on_progress callback allows the caller (app.py) to surface intermediate
  results in the UI as each stage completes.
"""

import logging
import os
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Suppress noisy loggers
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("opentelemetry").setLevel(logging.ERROR)

# Disable CrewAI telemetry
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"]        = "true"

try:
    from crewai import Crew
except ImportError as exc:
    print(f"ERROR: {exc}\nRun: pip install crewai")
    sys.exit(1)

from tools.dataset_tools import build_dataset_profile, generate_plotly_charts
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
# Parallel task execution helper
# ---------------------------------------------------------------------------

def _run_single_task(agent, task, max_rpm: int = 8) -> object:
    """Run a single CrewAI task in its own isolated mini-Crew.

    Used to execute relation_task and insight_task concurrently.
    Each call creates a separate Crew instance — no shared state.

    Returns the task object (with .output populated by kickoff).
    """
    mini = Crew(
        agents=[agent],
        tasks=[task],
        max_rpm=max_rpm,
        cache=True,
        verbose=True,
    )
    mini.kickoff()
    return task


# ---------------------------------------------------------------------------
# Output extractor
# ---------------------------------------------------------------------------

def _safe_output(task) -> str:
    """Safely extract raw string output from a completed CrewAI task."""
    if task is None or task.output is None:
        return ""
    return str(task.output.raw if hasattr(task.output, "raw") else task.output)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_crew(
    csv_path:    str,
    session_id:  str = "default",
    on_progress: Optional[Callable[[str, object], None]] = None,
) -> dict:
    """
    Run the full multi-agent analysis pipeline on *csv_path*.

    Pipeline stages
    ---------------
    1. Clean      (sequential)                     — Data Cleaner agent
    2. Relations  (parallel with Insights)         — Relationship Analyst agent
    2. Insights   (parallel with Relations)        — BI Analyst agent
    3. Visualize  (sequential, after 1 + 2)        — Data Visualizer agent
    4. Plotly     (pure Python, no LLM)            — generate_plotly_charts()

    Parameters
    ----------
    csv_path    : Path to the uploaded CSV file.
    session_id  : Unique identifier for this session (isolates files/outputs).
    on_progress : Optional callback(stage: str, data: object) called after
                  each stage completes. Stages: "profiling", "cleaning",
                  "relations", "insights", "visualization", "plotly".

    Returns
    -------
    dict with keys:
        dataframe, cleaning_steps, relations, insights, code,
        output_dir, plotly_charts
    """
    _cleanup_old_sessions()

    def _progress(stage: str, data: object = None) -> None:
        if on_progress:
            on_progress(stage, data)

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

    n_rows, n_cols = df.shape
    print(f"Loaded {n_rows:,} rows, {n_cols} columns")
    cols_preview = ", ".join(df.columns[:10])
    if n_cols > 10:
        cols_preview += "..."
    print(f"Columns: {cols_preview}")

    # ── Backup original before agents touch it ────────────────────────────────
    original_backup = session_data_dir / "original.csv"
    cleaned_path    = session_data_dir / "cleaned.csv"

    df.to_csv(original_backup, index=False)
    df.to_csv(cleaned_path, index=False)
    print(f"Original backed up → {original_backup}")
    print(f"Working copy created → {cleaned_path}\n")

    # ── Pre-compute dataset profile (eliminates 6-8 agent tool-call round-trips)
    # Large files are sampled; the cleaner still operates on the full dataset.
    profile_max_rows = 5000 if n_rows > 10_000 else n_rows
    if n_rows > 10_000:
        print(f"Large file detected ({n_rows:,} rows). "
              f"Profiling on {profile_max_rows:,}-row sample ...")
    print("Building dataset profile ...")
    profile = build_dataset_profile(str(cleaned_path), max_rows=profile_max_rows)
    _progress("profiling", profile)
    print("Profile ready.\n")

    # ── Build fresh agents + tasks ────────────────────────────────────────────
    agents, tasks = make_pipeline(session_id, profile=profile)
    # tasks = [clean_task, relation_task, insight_task, visualize_task]

    # ════════════════════════════════════════════════════════════════════════
    # STAGE 1 — Clean (sequential, must run before anything else)
    # ════════════════════════════════════════════════════════════════════════
    print("\n[Stage 1/3] Running Data Cleaner ...")
    clean_crew = Crew(
        agents=[agents[0]],
        tasks=[tasks[0]],
        max_rpm=15,
        cache=True,
        verbose=True,
    )
    try:
        clean_crew.kickoff()
    except Exception as exc:
        print(f"Cleaning error: {exc}")
        raise

    clean_output = _safe_output(tasks[0])
    _progress("cleaning", clean_output)
    print("[Stage 1/3] ✅ Cleaning complete.\n")

    # ════════════════════════════════════════════════════════════════════════
    # STAGE 2 — Relations + Insights (PARALLEL)
    # ════════════════════════════════════════════════════════════════════════
    print("[Stage 2/3] Running Relation Analyst + BI Analyst in parallel ...")
    relation_output = ""
    insights_output = ""

    try:
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="crew") as executor:
            rel_future = executor.submit(
                _run_single_task, agents[1], tasks[1], 8
            )
            ins_future = executor.submit(
                _run_single_task, agents[2], tasks[2], 8
            )
            # Collect results — callbacks execute in main thread after futures complete
            tasks[1] = rel_future.result()
            tasks[2] = ins_future.result()

        relation_output = _safe_output(tasks[1])
        insights_output = _safe_output(tasks[2])

    except Exception as exc:
        # Parallel execution failed — fall back to sequential
        print(f"Parallel execution error ({exc}). Falling back to sequential ...")
        try:
            rel_crew = Crew(agents=[agents[1]], tasks=[tasks[1]],
                            max_rpm=15, cache=True, verbose=True)
            rel_crew.kickoff()
            relation_output = _safe_output(tasks[1])

            ins_crew = Crew(agents=[agents[2]], tasks=[tasks[2]],
                            max_rpm=15, cache=True, verbose=True)
            ins_crew.kickoff()
            insights_output = _safe_output(tasks[2])
        except Exception as exc2:
            print(f"Sequential fallback also failed: {exc2}")
            raise exc2

    _progress("relations", relation_output)
    _progress("insights", insights_output)
    print("[Stage 2/3] ✅ Relations + Insights complete.\n")

    # ════════════════════════════════════════════════════════════════════════
    # STAGE 3 — Visualize (sequential, receives actual outputs as context)
    # ════════════════════════════════════════════════════════════════════════
    print("[Stage 3/3] Running Data Visualizer ...")

    # Inject relation + insight outputs directly into the task description
    # so the visualizer has full context without relying on CrewAI's
    # cross-crew context= mechanism.
    viz_task = tasks[3]
    viz_task.description += (
        f"\n\nRELATIONSHIPS TO VISUALIZE:\n{relation_output}"
        f"\n\nKEY INSIGHTS FOR CONTEXT:\n{insights_output}"
    )

    viz_crew = Crew(
        agents=[agents[3]],
        tasks=[viz_task],
        max_rpm=15,
        cache=True,
        verbose=True,
    )
    try:
        viz_crew.kickoff()
    except Exception as exc:
        print(f"Visualization error: {exc}")
        raise

    visualize_output = _safe_output(viz_task)
    _progress("visualization", visualize_output)
    print("[Stage 3/3] ✅ Visualization complete.\n")

    # ── Reload cleaned dataframe ──────────────────────────────────────────────
    try:
        cleaned_df = pd.read_csv(cleaned_path)
    except Exception:
        print("WARNING: Could not load cleaned CSV. Falling back to original data.")
        cleaned_df = df

    # ── Generate interactive Plotly charts (pure Python, no LLM) ─────────────
    print("Building interactive Plotly charts ...")
    plotly_charts = generate_plotly_charts(
        csv_path=str(cleaned_path),
        relations_text=relation_output,
    )
    _progress("plotly", plotly_charts)
    print(f"Generated {len(plotly_charts)} interactive chart(s).\n")

    return {
        "dataframe":      cleaned_df,
        "cleaning_steps": clean_output,
        "relations":      relation_output,
        "insights":       insights_output,
        "code":           visualize_output,
        "output_dir":     str(session_output_dir),
        "plotly_charts":  plotly_charts,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    default_path = (Path.cwd() / "data" / "TB_Burden_Country.csv").resolve()
    path = input(
        f"Enter the path to your CSV file (default: {default_path.name}): "
    ) or str(default_path)
    report = run_crew(path, session_id="cli")
    if report:
        print("\nAnalysis Complete.")
        print("Multi Agent Data Analysis with Crew AI")
        print("Prithiv.A.K  Sebin.S  Sowmiyan.S")
