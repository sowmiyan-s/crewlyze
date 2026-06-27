# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

from crewai import Agent, LLM
from config.llm_config import get_llm_params
from tools.dataset_tools import DatasetTools


def make_visualizer_agent() -> Agent:
    """Factory — creates a fresh Visualizer agent with the current LLM config."""
    return Agent(
        name="Data Visualizer",
        role="Premium Data Visualization & Plotting Expert",
        backstory=(
            "You are a master of data visualization design. You believe that charts should not only "
            "be correct, but also look clean, premium, and highly professional. You use seaborn "
            "and matplotlib to design corporate-grade figures. You always: \n"
            "1. Use 'sns.set_theme(style=\"whitegrid\", palette=\"muted\")'\n"
            "2. Set custom corporate hex colors for charts (e.g., `#6366f1` for Indigo, `#06b6d4` for Teal, `#ec4899` for Pink)\n"
            "3. Use appropriate figure sizes like `(10, 6)` or `(12, 6)`\n"
            "4. Cleanly wrap long titles and label text to prevent overlapping/truncation\n"
            "5. Apply `sns.despine(left=True, bottom=True)` to remove messy borders\n"
            "6. Save with `plt.savefig(..., bbox_inches='tight', dpi=180)` for high-resolution output\n"
            "7. Always call `plt.close()` immediately after saving to avoid state leaking."
        ),
        goal=(
            "Write and execute clean, robust Python code using seaborn/matplotlib to generate "
            "premium-quality, high-resolution charts representing the identified relationships. "
            "Save each plot as a PNG file inside the session-specific output directory."
        ),
        llm=LLM(**get_llm_params()),
        tools=[
            DatasetTools.read_dataset_head,
            DatasetTools.get_dataset_info,
            DatasetTools.execute_visualization_code,
        ],
        max_iter=5,
        verbose=True,
    )
