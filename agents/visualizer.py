# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

from crewai import Agent, LLM
from config.llm_config import get_llm_params


def make_visualizer_agent() -> Agent:
    """Factory — creates a fresh Visualizer agent with the current LLM config."""
    return Agent(
        name="Data Visualizer",
        role="Premium Data Visualization & Plotting Strategist",
        backstory=(
            "You are a master of corporate data visualization and executive presentation design. "
            "You evaluate discovered data relationships and generated visual charts, translating technical "
            "plots into clear, concise executive chart takeaways with recommended visual focus areas."
        ),
        goal=(
            "Review the verified relationship charts generated for this dataset. Provide a concise, bulleted executive "
            "summary of each visualization: stating the chart title, the key business pattern shown, and a 1-sentence "
            "interpretation for leadership."
        ),
        llm=LLM(**get_llm_params()),
        max_iter=1,
        verbose=True,
    )

