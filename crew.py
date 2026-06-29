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
import traceback
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

# Monkey patch crewai caching to avoid Nvidia NIM / LiteLLM validation errors
try:
    import crewai.llms.cache as _crewai_cache
    _crewai_cache.mark_cache_breakpoint = lambda msg: msg
except Exception:
    pass

try:
    from crewai import Crew
except ImportError as exc:
    print(f"ERROR: {exc}\nRun: pip install crewai")
    sys.exit(1)

from tools.dataset_tools import build_dataset_profile, generate_plotly_charts, read_csv_robust
from workflows.pipeline import make_pipeline


# ---------------------------------------------------------------------------
# Visualizer Fallback Generator (Pure Python, no LLM)
# ---------------------------------------------------------------------------

def _run_auto_visualizer_fallback(csv_path: Path, output_dir: Path, relations_text: str = "") -> str:
    """
    Pure Python statistical visualizer fallback that runs when the agent fails to save PNGs.
    Uses discovered relation pairs first (relation-aware), then falls back to generic charts.
    Creates structured, premium plots with consistent layout styles.
    """
    import re
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns

    try:
        df = read_csv_robust(csv_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

        generated = []
        # Dark-themed premium style
        sns.set_theme(style="darkgrid", palette="deep")
        BG_DARK = "#0f172a"
        BG_CARD = "#1e293b"
        TEXT_COLOR = "#e2e8f0"
        GRID_COLOR = "#334155"
        colors = ["#818cf8", "#22d3ee", "#f472b6", "#34d399", "#fb923c"]

        def _apply_dark_style(fig, ax_list):
            fig.patch.set_facecolor(BG_DARK)
            for ax in (ax_list if isinstance(ax_list, list) else [ax_list]):
                ax.set_facecolor(BG_CARD)
                ax.tick_params(colors=TEXT_COLOR)
                ax.xaxis.label.set_color(TEXT_COLOR)
                ax.yaxis.label.set_color(TEXT_COLOR)
                ax.title.set_color(TEXT_COLOR)
                for spine in ax.spines.values():
                    spine.set_edgecolor(GRID_COLOR)
                ax.grid(color=GRID_COLOR, linewidth=0.5)

        # ── PHASE 1: Parse relation pairs from agent output ────────────────────
        relation_pairs = []
        if relations_text:
            for line in relations_text.split("\n"):
                line = line.strip()
                if not (line and "|" in line and "X:" in line):
                    continue
                try:
                    parts = [p.strip() for p in line.lstrip("- ").split("|")]
                    x_col = parts[0].split(":", 1)[1].strip()
                    y_col = parts[1].split(":", 1)[1].strip()
                    ptype = parts[2].split(":", 1)[1].strip().lower() if len(parts) > 2 else "scatter"
                    if x_col in df.columns and y_col in df.columns and x_col != y_col:
                        relation_pairs.append((x_col, y_col, ptype))
                except (IndexError, ValueError):
                    continue

        # ── PHASE 2: Generate relation-based charts ────────────────────────────
        for i, (x_col, y_col, ptype) in enumerate(relation_pairs[:5]):
            color = colors[i % len(colors)]
            try:
                sample = df[[x_col, y_col]].dropna().head(2000)
                if sample.empty:
                    continue

                fig, ax = plt.subplots(figsize=(10, 6))

                x_is_num = pd.api.types.is_numeric_dtype(df[x_col])
                y_is_num = pd.api.types.is_numeric_dtype(df[y_col])

                if "bar" in ptype:
                    agg = sample.groupby(x_col)[y_col].mean().reset_index().head(20)
                    sns.barplot(data=agg, x=x_col, y=y_col, color=color, ax=ax)
                    plt.xticks(rotation=40, ha="right", color=TEXT_COLOR)
                    title = f"{y_col} by {x_col}"
                elif "line" in ptype:
                    sns.lineplot(data=sample.sort_values(x_col), x=x_col, y=y_col, color=color, ax=ax)
                    title = f"{y_col} over {x_col}"
                elif "box" in ptype:
                    if not x_is_num:
                        top_cats = df[x_col].value_counts().head(8).index
                        sample = sample[sample[x_col].isin(top_cats)]
                    sns.boxplot(data=sample, x=x_col if not x_is_num else None,
                                y=y_col, color=color, ax=ax)
                    title = f"Distribution of {y_col}"
                elif "hist" in ptype:
                    sns.histplot(sample[x_col].dropna(), kde=True, color=color, ax=ax)
                    title = f"Distribution of {x_col}"
                else:
                    if x_is_num and y_is_num:
                        sns.scatterplot(data=sample, x=x_col, y=y_col,
                                        color=color, alpha=0.7, ax=ax)
                    else:
                        top_cats = df[x_col].value_counts().head(15).index
                        sub = sample[sample[x_col].isin(top_cats)]
                        sns.boxplot(data=sub, x=x_col, y=y_col, color=color, ax=ax)
                        plt.xticks(rotation=40, ha="right", color=TEXT_COLOR)
                    title = f"{x_col} vs {y_col} Relationship"

                ax.set_title(title, fontsize=13, fontweight="bold", pad=14)
                _apply_dark_style(fig, ax)
                plt.tight_layout()
                safe_name = re.sub(r"[^\w]+", "_", f"relation_{x_col}_vs_{y_col}").lower()
                dest = output_dir / f"{safe_name}.png"
                plt.savefig(dest, dpi=150, bbox_inches="tight", facecolor=BG_DARK)
                plt.close()
                generated.append(dest.name)
                print(f"Relation chart saved: {dest.name}")

            except Exception as chart_err:
                print(f"Relation chart error ({x_col} vs {y_col}): {chart_err}")
                plt.close()
                continue

        # ── PHASE 3: Generic fallback charts if no relation charts were made ───
        if not generated:
            # Correlation heatmap
            if len(numeric_cols) >= 2:
                try:
                    fig, ax = plt.subplots(figsize=(10, 8))
                    corr = df[numeric_cols].corr()
                    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f",
                                square=True, cbar_kws={"shrink": .8}, ax=ax,
                                annot_kws={"color": TEXT_COLOR})
                    ax.set_title("Correlation Matrix", fontsize=14, fontweight="bold", pad=14)
                    _apply_dark_style(fig, ax)
                    plt.tight_layout()
                    dest = output_dir / "correlation_matrix.png"
                    plt.savefig(dest, dpi=150, bbox_inches="tight", facecolor=BG_DARK)
                    plt.close()
                    generated.append(dest.name)
                except Exception:
                    plt.close()

            # Distribution of first numeric col
            if numeric_cols:
                try:
                    col = numeric_cols[0]
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.histplot(df[col].dropna(), kde=True, color=colors[0], ax=ax)
                    ax.set_title(f"Distribution of {col}", fontsize=13, fontweight="bold", pad=14)
                    _apply_dark_style(fig, ax)
                    plt.tight_layout()
                    dest = output_dir / f"distribution_{col}.png"
                    plt.savefig(dest, dpi=150, bbox_inches="tight", facecolor=BG_DARK)
                    plt.close()
                    generated.append(dest.name)
                except Exception:
                    plt.close()

            # First scatter pair
            if len(numeric_cols) >= 2:
                try:
                    x, y = numeric_cols[0], numeric_cols[1]
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.scatterplot(data=df.head(2000), x=x, y=y, color=colors[1], alpha=0.7, ax=ax)
                    ax.set_title(f"{x} vs {y} Relationship", fontsize=13, fontweight="bold", pad=14)
                    _apply_dark_style(fig, ax)
                    plt.tight_layout()
                    dest = output_dir / f"scatter_{x}_vs_{y}.png"
                    plt.savefig(dest, dpi=150, bbox_inches="tight", facecolor=BG_DARK)
                    plt.close()
                    generated.append(dest.name)
                except Exception:
                    plt.close()

            # Categorical bar
            if categorical_cols and numeric_cols:
                try:
                    cat, num = categorical_cols[0], numeric_cols[0]
                    top_cats = df[cat].value_counts().head(10).index
                    sub_df = df[df[cat].isin(top_cats)]
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.barplot(data=sub_df, x=cat, y=num, errorbar=None, color=colors[2], ax=ax)
                    ax.set_title(f"Average {num} by {cat} (Top 10)", fontsize=13, fontweight="bold", pad=14)
                    plt.xticks(rotation=45, ha="right", color=TEXT_COLOR)
                    _apply_dark_style(fig, ax)
                    plt.tight_layout()
                    dest = output_dir / f"bar_{cat}_vs_{num}.png"
                    plt.savefig(dest, dpi=150, bbox_inches="tight", facecolor=BG_DARK)
                    plt.close()
                    generated.append(dest.name)
                except Exception:
                    plt.close()

        return f"Generated {len(generated)} chart(s) ({len(relation_pairs)} from relations, rest generic)."
    except Exception as e:
        return f"Fallback visualization failed: {e}"


# ---------------------------------------------------------------------------
# Session cleanup helper
# ---------------------------------------------------------------------------

def _cleanup_old_sessions(max_age_hours: int = 24) -> None:
    """Remove session directories older than *max_age_hours*.
    Also enforces a strict disk quota limit: if the total combined size of sessions and
    outputs exceeds 1.0 GB, it prunes the oldest folders until the size is under 400 MB.
    """
    sessions_root = Path("data") / "sessions"
    outputs_root  = Path("outputs")

    # 1. Clean based on age
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

    # 2. Clean based on disk quota (max 1.0 GB combined)
    def get_dir_size(path: Path) -> int:
        if not path.exists():
            return 0
        return sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())

    total_size = get_dir_size(sessions_root) + get_dir_size(outputs_root)
    max_quota_bytes = 1000 * 1024 * 1024  # 1.0 GB
    target_quota_bytes = 400 * 1024 * 1024 # 400 MB

    if total_size > max_quota_bytes:
        print(f"Disk quota exceeded: {total_size / (1024*1024):.1f}MB. Pruning oldest sessions...")
        # Collect all session subfolders and outputs with their mtimes
        subfolders = []
        for root in (sessions_root, outputs_root):
            if root.exists():
                for folder in root.iterdir():
                    if folder.is_dir():
                        subfolders.append((folder, folder.stat().st_mtime))
        
        # Sort oldest first
        subfolders.sort(key=lambda x: x[1])

        for folder, _ in subfolders:
            try:
                shutil.rmtree(folder, ignore_errors=True)
                # Recalculate
                total_size = get_dir_size(sessions_root) + get_dir_size(outputs_root)
                if total_size <= target_quota_bytes:
                    print(f"Disk footprint successfully reduced to {total_size / (1024*1024):.1f}MB.")
                    break
            except Exception as e:
                print(f"Error pruning session folder {folder}: {e}")


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
        cache=False,
        verbose=True,
    )
    mini.kickoff()
    return task


# ---------------------------------------------------------------------------
# Output extractor
# ---------------------------------------------------------------------------

def _safe_output(task) -> str:
    """Safely extract raw string output and error diagnostics from a completed CrewAI task."""
    if task is None:
        return ""

    output_parts = []
    if hasattr(task, "output") and task.output is not None:
        output_parts.append(str(task.output.raw if hasattr(task.output, "raw") else task.output))

    for attr_name in ("error", "exception", "traceback", "trace"):  # best-effort diagnostics
        if hasattr(task, attr_name):
            attr_value = getattr(task, attr_name)
            if attr_value:
                output_parts.append(f"[{attr_name}] {attr_value}")

    if not output_parts and hasattr(task, "__dict__"):
        # Fallback: include any candidate diagnostic attributes from the task object
        for key in ("status", "state", "result", "message"):
            if hasattr(task, key):
                value = getattr(task, key)
                if value:
                    output_parts.append(f"[{key}] {value}")

    return "\n\n".join(output_parts).strip()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_crew(
    csv_path:    str,
    session_id:  str = "default",
    on_progress: Optional[Callable[[str, object], None]] = None,
    selected_tasks: Optional[list[str]] = None,
    deep_analysis: bool = False,
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
        df = read_csv_robust(csv_path)
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

    os.environ["CURRENT_SESSION_CSV"] = str(cleaned_path)
    os.environ["CURRENT_SESSION_OUTPUT_DIR"] = str(session_output_dir)

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

    # Determine requested task stages and deep analysis mode
    if selected_tasks is None:
        env_raw = os.getenv("SELECTED_TASKS", "")
        selected_tasks = [t.strip() for t in env_raw.split(",") if t.strip()]

    if not deep_analysis:
        deep_analysis = os.getenv("DEEP_ANALYSIS", "false").lower() in {"true", "1", "yes", "on"}

    env_tasks = selected_tasks or []
    if not env_tasks:
        env_tasks = ["cleaning", "relations", "insights", "visualization"]
    do_cleaning = "cleaning" in env_tasks
    do_relations = "relations" in env_tasks
    do_insights = "insights" in env_tasks
    do_visualization = "visualization" in env_tasks

    # Load goal, title, and existing tweaked relations if available
    project_goal = ""
    report_title = ""
    existing_relations = ""
    try:
        import json
        meta_path = Path("data/sessions") / session_id / "metadata.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                project_goal = meta.get("optimized_goal") or meta.get("goal") or ""
                report_title = meta.get("report_title") or ""
                
        # Load tweaked relations from results.json
        results_path = Path("data/sessions") / session_id / "results.json"
        if results_path.exists():
            with open(results_path, "r", encoding="utf-8") as f:
                res_data = json.load(f)
                existing_relations = res_data.get("relations") or ""
    except Exception as e:
        print(f"Warning: Could not read metadata or results cache: {e}")

    # ── Build fresh agents + tasks ────────────────────────────────────────────
    agents, tasks = make_pipeline(
        session_id,
        profile=profile,
        selected_tasks=env_tasks,
        deep_analysis=deep_analysis,
        project_goal=project_goal,
        report_title=report_title,
        existing_relations=existing_relations,
    )
    # tasks = [clean_task, relation_task, insight_task, visualize_task]

    # ════════════════════════════════════════════════════════════════════════
    # STAGE 1 — Clean (sequential, must run before anything else)
    # ════════════════════════════════════════════════════════════════════════
    clean_output = "Data cleaning was skipped by user selection."

    if do_cleaning:
        print("\n[Stage 1/4] Running Data Cleaner ...")
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
            traceback.print_exc()
            raise

        clean_output = _safe_output(tasks[0])
        _progress("cleaning", clean_output)
        print("[Stage 1/4] ✅ Cleaning complete.\n")
    else:
        print("\n[Stage 1/4] Skipping Data Cleaner (user selection).\n")
        _progress("cleaning", clean_output)

    # ════════════════════════════════════════════════════════════════════════
    # STAGE 2 — Relations + Insights (PARALLEL)
    # ════════════════════════════════════════════════════════════════════════
    relation_output = "Relationship mapping was skipped by user selection."
    insights_output = "Business insights generation was skipped by user selection."

    if do_relations or do_insights:
        print("[Stage 2/4] Running Relation Analyst + BI Analyst ...")
        try:
            if do_relations and do_insights:
                import contextvars
                ctx = contextvars.copy_context()
                with ThreadPoolExecutor(max_workers=2, thread_name_prefix="crew") as executor:
                    rel_future = executor.submit(
                        ctx.run, _run_single_task, agents[1], tasks[1], 8
                    )
                    ins_future = executor.submit(
                        ctx.run, _run_single_task, agents[2], tasks[2], 8
                    )
                    tasks[1] = rel_future.result()
                    tasks[2] = ins_future.result()
            elif do_relations:
                rel_crew = Crew(agents=[agents[1]], tasks=[tasks[1]], max_rpm=15, cache=True, verbose=True)
                rel_crew.kickoff()
            elif do_insights:
                ins_crew = Crew(agents=[agents[2]], tasks=[tasks[2]], max_rpm=15, cache=True, verbose=True)
                ins_crew.kickoff()

            if do_relations:
                relation_output = _safe_output(tasks[1])
            if do_insights:
                insights_output = _safe_output(tasks[2])

        except Exception as exc:
            # Parallel execution failed — fall back to sequential
            print(f"Relation/Insight execution error: {exc}. Falling back to sequential ...")
            traceback.print_exc()
            try:
                if do_relations:
                    rel_crew = Crew(agents=[agents[1]], tasks=[tasks[1]], max_rpm=15, cache=True, verbose=True)
                    rel_crew.kickoff()
                    relation_output = _safe_output(tasks[1])
                if do_insights:
                    ins_crew = Crew(agents=[agents[2]], tasks=[tasks[2]], max_rpm=15, cache=True, verbose=True)
                    ins_crew.kickoff()
                    insights_output = _safe_output(tasks[2])
            except Exception as exc2:
                print(f"Sequential fallback also failed: {exc2}")
                traceback.print_exc()
                raise

    _progress("relations", relation_output)
    _progress("insights", insights_output)
    print("[Stage 2/4] ✅ Relations + Insights complete.\n")

    # ════════════════════════════════════════════════════════════════════════
    # STAGE 3 — Visualize (sequential, receives actual outputs as context)
    # ════════════════════════════════════════════════════════════════════════
    visualize_output = "Visualization was skipped by user selection."

    if do_visualization:
        print("[Stage 3/4] Running Data Visualizer ...")

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
            visualize_output = _safe_output(viz_task)
        except Exception as exc:
            print(f"Visualization Agent error: {exc}. Activating auto-healing visualizer fallback...")
            traceback.print_exc()
            visualize_output = f"Visualization Agent encountered error: {exc}"

        # Auto-healing fallback check: if no PNG charts were successfully saved
        png_files = list(session_output_dir.glob("*.png"))
        if not png_files:
            print("No PNG charts generated by agent. Running relation-aware visualizer fallback...")
            fallback_msg = _run_auto_visualizer_fallback(
                cleaned_path, session_output_dir, relations_text=relation_output
            )
            visualize_output = f"{visualize_output}\n\n[Auto-Healing Fallback Status]: {fallback_msg}"
            print(fallback_msg)
    else:
        print("[Stage 3/4] Skipping Data Visualizer (user selection).\n")

    _progress("visualization", visualize_output)
    print("[Stage 3/4] ✅ Visualization complete.\n")

    # ── Generate interactive Plotly charts (pure Python, no LLM) ─────────────
    print("[Stage 4/4] Building interactive Plotly charts ...")
    plotly_charts = generate_plotly_charts(
        csv_path=str(cleaned_path),
        relations_text=relation_output,
    )
    _progress("plotly", plotly_charts)
    print(f"Generated {len(plotly_charts)} interactive chart(s).\n")

    # ── Reload cleaned dataframe ──────────────────────────────────────────────
    try:
        cleaned_df = read_csv_robust(cleaned_path)
    except Exception:
        print("WARNING: Could not load cleaned CSV. Falling back to original data.")
        cleaned_df = df

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
