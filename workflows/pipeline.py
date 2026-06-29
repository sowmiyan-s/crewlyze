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

def make_pipeline(
    session_id: str,
    profile: str = "",
    selected_tasks: Optional[list[str]] = None,
    deep_analysis: bool = False,
    project_goal: str = "",
    report_title: str = "",
    existing_relations: str = "",
) -> tuple[list, list]:
    """
    Build and return (agents, tasks) for a single analysis run.

    Every call creates fresh agent instances (picks up the latest LLM config)
    and embeds the session-specific CSV and output paths + dataset profile
    into each task description.
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
    
    goal_context = f"\nThe user has set the following goal for this project: '{project_goal}'." if project_goal else ""
    
    cleaning_prompt = (
        f"The dataset working copy is at '{csv_path}'. "
        f"{goal_context} "
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

    relation_prompt = (
        f"First, examine the 5 sample rows and column details in the dataset profile of '{csv_path}'. "
        "Identify the data type of each column (e.g. Unique ID, Categorical, Continuous Numeric, Timestamp, Key Column). "
        f"Then, identify 5 key column relationships with high business relevance, focusing on correlations or connections that align with the user's project goal: '{project_goal}'. "
        "Format the output STRICTLY as:\n"
        "- X: [Column1] | Y: [Column2] | Type: [PlotType] | Details: [Relationship details, data type mapping of both columns, and business relevance]\n"
        "Output NOTHING else."
        f"{profile_block}"
    )

    relation_task = Task(
        agent=relation_agent,
        description=relation_prompt,
        expected_output=(
            "Strictly formatted list of relationships. Example:\n"
            "- X: Age | Y: Income | Type: Scatter Plot | Details: Age (Continuous Numeric) vs Income (Continuous Numeric). Displays moderate positive correlation, key for targeting demographics."
        ),
        callback=cb,
    )

    relations_context = f"\n\n--- TWEAKED SCHEMA & VERIFIED RELATIONSHIPS (use these verified columns & relationships to guide your analysis) ---\n{existing_relations}\n---" if existing_relations else ""

    goal_prompt = f"Align all insights and strategies directly to address the project goal: '{project_goal}'." if project_goal else ""
    insight_prompt = (
        "Using the dataset profile and identified relationships provided below, "
        "generate a structured report. "
        f"{goal_prompt}\n"
        "Format the report using markdown headers EXACTLY as follows:\n\n"
        "### Objectives & Goals\n"
        "[Describe the primary objective and business goals of this analysis based on the project goal and dataset profile]\n\n"
        "### Dataset Statistics\n"
        "- Total rows: [row count]\n"
        "- Total columns: [col count]\n"
        "- Numeric columns: [list numeric columns and their min/max values]\n"
        "- Categorical columns: [list categorical columns]\n\n"
        "### Strategic Insights\n"
        "Generate 5 key business insights. Each insight MUST strictly use this structure:\n"
        "1. **Observation**: [Describe the exact trend, anomaly, or correlation from the data]\n"
        "   **Business Implication**: [Explain how this impacts profitability, risk, operation, or customers]\n"
        "   **Actionable Strategy**: [Outline a concrete recommendation that the organization should implement immediately]\n\n"
        "### Warnings & Alerts\n"
        "[List any warning or alert (e.g. data quality issues, outlier presence, class imbalance, missing values, declining trends) that a data scientist or business user should be aware of]"
        f"{relations_context}"
        f"{profile_block}"
    )

    insight_task = Task(
        agent=insights_agent,
        description=insight_prompt,
        expected_output="A structured report in markdown format containing Objectives & Goals, Dataset Statistics, Strategic Insights, and Warnings & Alerts.",
        callback=cb,
    )

    viz_goal_prompt = f"\nFocus visualizations on answering or addressing the project goal: '{project_goal}'." if project_goal else ""
    visualize_prompt = (
        "Examine the columns and data types from the profile below. Using your AI reasoning, select "
        "the 3-4 most insightful relationships, trends, or distributions that characterize this specific dataset.\n"
        f"{viz_goal_prompt}\n"
        "Then, write and execute Python plotting code using 'Execute Visualization Code'.\n\n"
        "ENVIRONMENT NOTE:\n"
        "- The pandas DataFrame is pre-loaded as `df` in your execution environment.\n"
        "- Pre-defined variable `OUTPUT_DIR` contains the target output folder path.\n"
        "- A helper function `save_chart(filename_string)` is available to save the current figure.\n"
        "- Matplotlib and Seaborn are pre-imported. Do NOT load CSVs or create folders yourself!\n\n"
        "CODE REQUIREMENTS:\n"
        "- Set style theme: 'sns.set_theme(style=\"whitegrid\", palette=\"muted\")'\n"
        "- Use high-end palette hex colors (e.g. `#6366f1` for Indigo, `#06b6d4` for Teal, `#ec4899` for Pink, `#10b981` for Emerald).\n"
        "- Set figure size to `(10, 6)` or `(12, 6)`.\n"
        "- Set clear, descriptive titles and wrap long titles: 'plt.title(textwrap.fill(title, 40))'.\n"
        "- Apply 'sns.despine(left=True, bottom=True)' to remove borders.\n"
        "- Save each plot with: `save_chart('chart_name')`.\n"
        "- Call `plt.close()` immediately after each save to clear the state."
        f"{relations_context}"
        f"{profile_block}"
    )

    visualize_task = Task(
        agent=visualizer_agent,
        description=visualize_prompt,
        expected_output="Summary of the 3-4 custom visualization plots generated and saved.",
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
