# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Pipeline factory.

Tasks are no longer module-level singletons. Call make_pipeline(session_id)
inside run_crew() to get a fresh set of agents + tasks that embed the correct
session-specific file paths and use the current LLM config.
"""

import os
import time

from crewai import Task

from agents.cleaner    import make_cleaner_agent
from agents.relation   import make_relation_agent
from agents.insights   import make_insights_agent
from agents.visualizer import make_visualizer_agent


def _task_cooldown(task_output) -> None:
    """Sleep between tasks to respect provider rate limits."""
    cooldown = int(os.getenv("API_COOLDOWN", "15"))
    if cooldown > 0:
        print(f"\nTask completed. Cooldown: sleeping {cooldown}s to prevent rate limits...")
        time.sleep(cooldown)


def make_pipeline(session_id: str) -> tuple[list, list]:
    """
    Build and return (agents, tasks) for a single analysis run.

    Every call creates fresh agent instances (picks up the latest LLM config)
    and embeds the session-specific CSV and output paths into each task.

    Parameters
    ----------
    session_id:
        Short unique string (e.g. UUID hex) used to isolate per-user data.

    Returns
    -------
    agents : list[Agent]
    tasks  : list[Task]
    """
    csv_path    = f"data/sessions/{session_id}/cleaned.csv"
    output_dir  = f"outputs/{session_id}"

    # Fresh agents — LLM config is read NOW, not at import time
    cleaner_agent    = make_cleaner_agent()
    relation_agent   = make_relation_agent()
    insights_agent   = make_insights_agent()
    visualizer_agent = make_visualizer_agent()

    clean_task = Task(
        agent=cleaner_agent,
        description=(
            f"Analyze the dataset at '{csv_path}' using read_dataset_head and "
            "get_dataset_info. Identify quality issues, then write and run Python "
            "cleaning code using 'Clean Dataset with Python Code' to fix them. "
            "Return a plain-text bulleted list of the cleaning steps performed."
        ),
        expected_output=(
            "A plain-text bulleted list of cleaning steps. Example:\n"
            "- Imputed missing values in Column A with mean\n"
            "- Dropped duplicate rows"
        ),
        callback=_task_cooldown,
    )

    relation_task = Task(
        agent=relation_agent,
        description=(
            f"Analyze the columns and sample data of the cleaned dataset at '{csv_path}'. "
            "Identify 5 key relationships that can show business meaning. "
            "Format the output strictly as:\n"
            "- X: [Column1] | Y: [Column2] | Type: [PlotType]"
        ),
        expected_output=(
            "Strictly formatted list of relationships. Example:\n"
            "- X: Age | Y: Income | Type: Scatter Plot"
        ),
        callback=_task_cooldown,
    )

    insight_task = Task(
        agent=insights_agent,
        description=(
            f"Synthesize findings from the cleaned dataset '{csv_path}' and the "
            "identified relationships. Generate 5 key business insights. "
            "List them as numbered points."
        ),
        expected_output="Plain-text numbered list of 5 business insights.",
        callback=_task_cooldown,
    )

    visualize_task = Task(
        agent=visualizer_agent,
        description=(
            "Based on the identified relationships and key business insights, write and "
            "execute Python code using 'Execute Visualization Code' to generate plots. "
            f"The Python code must read from '{csv_path}' and save PNG plots to "
            f"'{output_dir}'. "
            "Use matplotlib.use('Agg') before importing pyplot. "
            "Generate all possible meaningful plots. Ensure the code handles matplotlib "
            "layout correctly and does not fail."
        ),
        expected_output="Summary of generated and saved visualization plots.",
        context=[relation_task, insight_task],
        callback=_task_cooldown,
    )

    agents = [cleaner_agent, relation_agent, insights_agent, visualizer_agent]
    tasks  = [clean_task, relation_task, insight_task, visualize_task]
    return agents, tasks
