# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Pipeline factory.

Performance improvements in this version:
- make_pipeline() accepts a pre-computed `profile` string and embeds it
  directly into each task description. This eliminates the 6-8 LLM tool-call
  round-trips agents would otherwise spend reading the dataset before acting.
- visualize_task no longer uses context=[...] — the caller (run_crew) injects
  relation output into the task description after the relation stage completes.
- Adaptive cooldown: sleeps only when a rate-limit error is detected; otherwise
  uses a configurable minimum delay (default 5s, 0 for self-hosted providers).

Quality improvements:
- Insight task mandates an ex-McKinsey/BCG format: Observation ➔ Implication ➔ Strategy.
- Visualizer task mandates corporate styling guidelines (Grid, Hex Palette, Tight Layout, DPI).
"""

import os
import time
from pathlib import Path
from typing import Optional

from crewai import Task

from agents.cleaner    import make_cleaner_agent
from agents.relation   import make_relation_agent
from agents.insights   import make_insights_agent
from agents.visualizer import make_visualizer_agent
from agents.predictive import make_predictive_agent
from agents.anomaly    import make_anomaly_agent
from agents.trend      import make_trend_agent


# ---------------------------------------------------------------------------
# Adaptive cooldown callback
# ---------------------------------------------------------------------------

_RATE_LIMIT_SIGNALS = ("rate limit", "429", "too many requests", "quota")
_failures_count = 0

def cooldown_task_callback(task_output) -> None:
    """
    Module-level task callback that applies a minimal rest interval between tasks.
    Prevents false-positive backoff sleeps triggered by business report wording.
    """
    from config.context import current_cooldown
    ctx_cooldown = current_cooldown.get()
    min_sleep = int(ctx_cooldown) if ctx_cooldown is not None else int(os.getenv("API_COOLDOWN", "1"))
    if min_sleep > 0:
        time.sleep(min_sleep)


def make_cooldown_callback(min_sleep: int = 1):
    """
    Return the module-level task callback for backward compatibility.
    """
    return cooldown_task_callback


# ---------------------------------------------------------------------------
# Pipeline factory
# ---------------------------------------------------------------------------

def make_pipeline(
    session_id: str,
    profile: str = "",
    selected_tasks: Optional[list[str]] = None,
    deep_analysis: bool = False,
    project_goal: str = "",
    report_title: str = "",
    existing_relations: str = "",
    coercion_summary: str = "",
) -> tuple[list, list]:
    """
    Build and return (agents, tasks) for a single analysis run.
    """
    user_home = Path.home() / ".crewlyze"
    sessions_dir = Path(os.getenv("CREWLYZE_DATA_DIR", str(user_home / "data"))) / "sessions"
    outputs_dir_base = Path(os.getenv("CREWLYZE_OUTPUTS_DIR", str(user_home / "outputs")))

    csv_path   = str((sessions_dir / session_id / "cleaned.csv").resolve())
    output_dir = str((outputs_dir_base / session_id).resolve())

    meta_path = sessions_dir / session_id / "metadata.json"
    clean_rules = []
    if meta_path.exists():
        try:
            import json
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                rules_str = meta.get("clean_rules", "")
                if rules_str:
                    clean_rules = [r.strip().lower() for r in rules_str.split(",") if r.strip()]
        except Exception as e:
            print(f"Error loading metadata inside pipeline: {e}")

    rules_list = []
    if "date_format" in clean_rules:
        rules_list.append("- Standardize all date values in the dataset to YYYY-MM-DD format.")
    if "fill_numeric" in clean_rules:
        rules_list.append("- Impute/fill all missing numeric cell values automatically using their column medians.")
    if "drop_duplicates" in clean_rules:
        rules_list.append("- Drop duplicate row records across the entire dataset to ensure record uniqueness.")
    if "strip_strings" in clean_rules:
        rules_list.append("- Normalize string/text columns by trimming trailing/leading spaces and standardizing case where appropriate.")

    rules_block = ""
    if rules_list:
        rules_block = "\n\nSpecific cleaning rules applied:\n" + "\n".join(rules_list)

    from config.context import current_cooldown
    ctx_cooldown = current_cooldown.get()
    cooldown = int(ctx_cooldown) if ctx_cooldown is not None else int(os.getenv("API_COOLDOWN", "1"))
    cb = make_cooldown_callback(min_sleep=cooldown)

    selected_tasks = [task.strip().lower() for task in (selected_tasks or []) if task.strip()]
    if not selected_tasks:
        selected_tasks = ["cleaning", "relations", "insights", "visualization"]

    profile_block = (
        f"\n\n--- DATASET PROFILE ---\n{profile}\n---"
        if profile else ""
    )

    # Fresh agents — LLM config is read NOW, not at import time
    cleaner_agent    = make_cleaner_agent()
    relation_agent   = make_relation_agent()
    insights_agent   = make_insights_agent()
    visualizer_agent = make_visualizer_agent()
    predictive_agent = make_predictive_agent()
    anomaly_agent    = make_anomaly_agent()
    trend_agent      = make_trend_agent()

    deep_prompt = "\n\nIf deep analysis mode is enabled, provide richer reasoning, deeper causal exploration, and more detailed business implications for each recommendation." if deep_analysis else ""
    
    if deep_analysis:
        relation_deep_prompt = "\n\nDEEP ANALYSIS MODE IS ACTIVE. Map at least 5-6 key relationships."
        insight_deep_prompt = "\n\nDEEP ANALYSIS MODE IS ACTIVE. Provide detailed causal analysis."
        visualize_deep_prompt = "\n\nDEEP ANALYSIS MODE IS ACTIVE. Provide thorough executive chart narratives."
    else:
        relation_deep_prompt = "\n\nSTANDARD ANALYSIS MODE IS ACTIVE. Map 3-4 key relationships concisely."
        insight_deep_prompt = "\n\nSTANDARD ANALYSIS MODE IS ACTIVE. Provide a concise high-level summary."
        visualize_deep_prompt = "\n\nSTANDARD ANALYSIS MODE IS ACTIVE. Provide concise chart notes."

    goal_context = f"\nThe user has set the following goal for this project: '{project_goal}'." if project_goal else ""
    
    coercion_block = (
        f"\n\n--- AUTOMATIC TYPE CONVERSIONS PERFORMED ---\n{coercion_summary}\n"
        "Explain the business rationale of these automatic type conversions in your report."
        if coercion_summary else ""
    )

    clean_task = Task(
        agent=cleaner_agent,
        description=f"The dataset working copy is at '{csv_path}'. {goal_context} {coercion_block}{rules_block}\nExplain data cleaning actions and validations in concise executive bullet points.",
        expected_output="Bulleted list of cleaning steps explaining the business purpose.",
        callback=cb,
    )

    relation_task = Task(
        agent=relation_agent,
        description=f"Identify key column relationships aligned with goal '{project_goal}'. Format strictly as: - X: [Col1] | Y: [Col2] | Type: [Plot] | Details: [Info]{profile_block}{relation_deep_prompt}",
        expected_output="List of relationships formatted strictly as - X: [Col1] | Y: [Col2] | Type: [Plot] | Details: [Info].",
        callback=cb,
    )

    relations_context = f"\n\n--- VERIFIED RELATIONSHIPS ---\n{existing_relations}\n---" if existing_relations else ""

    insight_task = Task(
        agent=insights_agent,
        description=f"Generate structured executive report focusing on strategic business context. Align with goal: '{project_goal}'.{insight_deep_prompt}{relations_context}",
        expected_output="Structured markdown report containing Objectives, Statistics, Strategic Insights, and Warnings.",
        callback=cb,
    )

    visualize_task = Task(
        agent=visualizer_agent,
        description=f"Review the generated visualizations and verified relationships saved to '{output_dir}'.{visualize_deep_prompt}{relations_context}",
        expected_output="Bulleted summary of custom visualization charts and executive takeaways.",
        callback=cb,
    )

    predictive_task = Task(
        agent=predictive_agent,
        description=f"Review candidate target features and explain top 3 predictive feature importance drivers in plain business terms.",
        expected_output="Executive summary of top 3 predictive drivers influencing the primary target metric.",
        callback=cb,
    )

    anomaly_task = Task(
        agent=anomaly_agent,
        description=f"Audit dataset distributions for statistical outliers (IQR/Z-score) and provide operational risk safeguards.",
        expected_output="Statistical outlier and risk report with executive mitigation recommendations.",
        callback=cb,
    )

    trend_task = Task(
        agent=trend_agent,
        description=f"Review temporal metrics (growth rate, YoY, CAGR) and project strategic trajectory trends.",
        expected_output="Time-series trajectory and forward growth projections.",
        callback=cb,
    )

    agents = [cleaner_agent, relation_agent, insights_agent, visualizer_agent, predictive_agent, anomaly_agent, trend_agent]
    tasks  = [clean_task, relation_task, insight_task, visualize_task, predictive_task, anomaly_task, trend_task]

    return agents, tasks
