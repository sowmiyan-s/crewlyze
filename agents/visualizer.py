# Crewlyze
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
            "You are a master of data visualization design and analytics. You believe that charts must be "
            "both statistically correct AND visually stunning. You use seaborn and matplotlib to design "
            "corporate-grade, light-themed figures that executives love.\n\n"
            "You have access to a sandbox execution tool 'Execute Visualization Code' where the pandas DataFrame "
            "is already loaded as `df` and a helper function `save_chart(filename)` is pre-defined for you.\n\n"
            "CRITICAL RULE: You will be given a 'RELATIONSHIPS TO VISUALIZE' section in your task. You MUST "
            "generate charts for EXACTLY those specified column pairs (X and Y columns listed). Do NOT invent "
            "different columns. Do NOT skip any pair. Use the chart Type hint given for each pair.\n\n"
            "DATA TYPE CASTING SAFETY: Before plotting any numeric variable (e.g. for scatter, line, histogram, or bar chart value axis), "
            "always ensure it is converted using `df[col] = pd.to_numeric(df[col], errors='coerce')` so numbers are never plotted as discrete string ticks on continuous axes.\n\n"
            "Apply a clean white theme: set figure facecolor to 'white', axes facecolor to '#f8fafc', "
            "tick/label colors to '#334155'. Use high-contrast corporate colors like '#4f46e5', '#06b6d4', '#ec4899', '#10b981'."
        ),
        goal=(
            "Generate premium seaborn/matplotlib charts for EACH relationship pair listed in the "
            "'RELATIONSHIPS TO VISUALIZE' section. Execute Python code using 'Execute Visualization Code' "
            "for every pair, saving each chart with save_chart(). Apply dark-themed professional styling. "
            "If a pair fails, try an alternative chart type before giving up. Must generate at least 3 charts."
        ),
        llm=LLM(**get_llm_params()),
        tools=[
            DatasetTools.read_dataset_head,
            DatasetTools.get_dataset_info,
            DatasetTools.execute_visualization_code,
        ],
        max_iter=2,
        verbose=True,
    )
