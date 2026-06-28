# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Pipeline factory.

Performance improvements in this version:
- make_pipeline() accepts a pre-computed `profile` string and embeds it
  directly into each task description. This eliminates the 6-8 LLM tool-call
  round-trips agents would otherwise spend reading the dataset before acting.
- visualize_task no longer uses context=[...] — the caller (run_crew) injects
  relation + insight outputs into the task description after parallel execution.
- Adaptive cooldown: sleeps only when a rate-limit error is detected; otherwise
  uses a configurable minimum delay (default 5s, 0 for self-hosted providers).

Quality improvements:
- Insight task mandates an ex-McKinsey/BCG format: Observation ➔ Implication ➔ Strategy.
- Visualizer task mandates corporate styling guidelines (Grid, Hex Palette, Tight Layout, DPI).
"""

import os
import time
from typing import Optional

from crewai import Task

from agents.cleaner    import make_cleaner_agent
from agents.relation   import make_relation_agent
from agents.insights   import make_insights_agent
from agents.visualizer import make_visualizer_agent


# ---------------------------------------------------------------------------
# Adaptive cooldown callback
# ---------------------------------------------------------------------------

_RATE_LIMIT_SIGNALS = ("rate limit", "429", "too many requests", "quota")

def make_cooldown_callback(min_sleep: int = 5):
    """
    Return a task callback that sleeps adaptively based on API feedback.

    - If the task output contains rate-limit signals → exponential back-off
      starting at max(min_sleep, 10) seconds.
    - Otherwise → sleep min_sleep seconds (0 = no wait, ideal for Ollama).

    Args:
        min_sleep: Base sleep in seconds between tasks (from API_COOLDOWN env var).
    """
    state = {"failures": 0}

    def _callback(task_output) -> None:
        output_str = str(task_output).lower() if task_output else ""
        hit_rate_limit = any(sig in output_str for sig in _RATE_LIMIT_SIGNALS)

        if hit_rate_limit:
            state["failures"] += 1
            delay = min(max(min_sleep, 10) * (2 ** (state["failures"] - 1)), 120)
            print(f"\n⚠️  Rate-limit detected. Back-off sleep: {delay}s ...")
            time.sleep(delay)
        elif min_sleep > 0:
            state["failures"] = max(0, state["failures"] - 1)  # cool down error count
            print(f"\nTask complete. Cooldown: {min_sleep}s ...")
            time.sleep(min_sleep)
        else:
            print("\nTask complete. No cooldown (min_sleep=0).")

    return _callback


# ---------------------------------------------------------------------------
# Pipeline factory
# ---------------------------------------------------------------------------

def make_pipeline(session_id: str, profile: str = "", selected_tasks: Optional[list[str]] = None, deep_analysis: bool = False) -> tuple[list, list]:
    """
    Build and return (agents, tasks) for a single analysis run.

    Every call creates fresh agent instances (picks up the latest LLM config)
    and embeds the session-specific CSV and output paths + dataset profile
    into each task description.

    Parameters
    ----------
    session_id : Short unique string used to isolate per-user data.
    profile    : Pre-computed dataset profile string from build_dataset_profile().

    Returns
    -------
    agents : list[Agent]
    tasks  : list[Task]
    """
    csv_path   = f"data/sessions/{session_id}/cleaned.csv"
    output_dir = f"outputs/{session_id}"

    cooldown = int(os.getenv("API_COOLDOWN", "5"))
    cb = make_cooldown_callback(min_sleep=cooldown)

    selected_tasks = [task.strip().lower() for task in (selected_tasks or []) if task.strip()]
    if not selected_tasks:
        selected_tasks = ["cleaning", "relations", "insights", "visualization"]

    profile_block = (
        f"\n\n--- DATASET PROFILE (use this — do NOT call read_dataset_head or "
        f"get_dataset_info first) ---\n{profile}\n---"
        if profile else ""
    )

    # Fresh agents — LLM config is read NOW, not at import time
    cleaner_agent    = make_cleaner_agent()
    relation_agent   = make_relation_agent()
    insights_agent   = make_insights_agent()
    visualizer_agent = make_visualizer_agent()

    deep_prompt = "\n\nIf deep analysis mode is enabled, provide richer reasoning, deeper causal exploration, and more detailed business implications for each recommendation." if deep_analysis else ""
    cleaning_prompt = (
        f"The dataset working copy is at '{csv_path}'. "
        "Identify data quality issues from the profile below, then write and run "
        "Python cleaning code using 'Clean Dataset with Python Code' to fix them. "
        "Explain the business rationale of each cleaning step in the final report."
        f"{deep_prompt}{profile_block}"
    )

    clean_task = Task(
        agent=cleaner_agent,
        description=cleaning_prompt,
        expected_output=(
            "A plain-text bulleted list of cleaning steps explaining the business purpose. Example:\n"
            "- Imputed missing revenue values with median to prevent statistical skew in sales reports\n"
            "- Standardized country names to enable consistent geographic breakdown"
        ),
        callback=cb,
    )

    relation_task = Task(
        agent=relation_agent,
        description=(
            f"Using the dataset profile below, identify 5 key relationships among the "
            f"columns of '{csv_path}' that carry significant business meaning. "
            "Format the output STRICTLY as:\n"
            "- X: [Column1] | Y: [Column2] | Type: [PlotType]\n"
            "Output NOTHING else."
            f"{profile_block}"
        ),
        expected_output=(
            "Strictly formatted list of relationships. Example:\n"
            "- X: Age | Y: Income | Type: Scatter Plot"
        ),
        callback=cb,
    )

    insight_task = Task(
        agent=insights_agent,
        description=(
            "Using the dataset profile and identified relationships provided below, "
            "generate 5 key business insights. Each insight MUST strictly use this structure:\n"
            "1. **Observation**: [Describe the exact trend, anomaly, or correlation from the data]\n"
            "   **Business Implication**: [Explain how this impacts profitability, risk, operation, or customers]\n"
            "   **Actionable Strategy**: [Outline a concrete recommendation that the organization should implement immediately]\n"
            "Provide highly context-specific, professional management-consultant level insights. Avoid generic fillers."
            f"{profile_block}"
        ),
        expected_output="Plain-text numbered list of 5 business insights in the mandated structure.",
        callback=cb,
    )

    visualize_task = Task(
        agent=visualizer_agent,
        description=(
            "Write and execute Python visualization code using 'Execute Visualization Code'. "
            f"Read data from '{csv_path}' and save PNG plots to '{output_dir}'.\n\n"
            "CODE REQUIREMENT:\n"
            "- Always call matplotlib.use('Agg') before importing pyplot.\n"
            "- Set theme: 'sns.set_theme(style=\"whitegrid\", palette=\"muted\")'\n"
            "- Use hex colors (e.g. `#6366f1` for Indigo, `#06b6d4` for Teal, `#ec4899` for Pink).\n"
            "- Set figure size to `(10, 6)` or `(12, 6)`.\n"
            "- Set clear, descriptive titles and wrap long text using 'textwrap.fill(title, 40)'.\n"
            "- Apply 'sns.despine(left=True, bottom=True)' to remove borders.\n"
            "- Save each plot using: `plt.savefig(..., bbox_inches='tight', dpi=180)`.\n"
            "- Call `plt.close()` immediately after each save."
        ),
        expected_output="Summary of generated and saved visualization plots.",
        callback=cb,
    )

    agents = [cleaner_agent, relation_agent, insights_agent, visualizer_agent]
    tasks  = [clean_task, relation_task, insight_task, visualize_task]

    # If a stage is disabled, return placeholder tasks for safe indexing.
    if "cleaning" not in selected_tasks:
        tasks[0] = clean_task
    if "relations" not in selected_tasks:
        tasks[1] = relation_task
    if "insights" not in selected_tasks:
        tasks[2] = insight_task
    if "visualization" not in selected_tasks:
        tasks[3] = visualize_task

    return agents, tasks
