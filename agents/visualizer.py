# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

from crewai import Agent, LLM
from config.llm_config import get_llm_params


def make_visualizer_agent() -> Agent:
    """Factory — creates an Executive BI Visualizer agent with the current LLM config."""
    return Agent(
        name="Executive BI Visualizer",
        role="Executive Business Intelligence & Growth Dashboard Visualizer",
        backstory=(
            "You are a master of executive BI dashboards and board-level presentation graphics. "
            "You evaluate discovered business relationships, KPI breakdowns, and growth charts, translating "
            "plots into sharp, high-level executive takeaways and decision focus areas for leadership."
        ),
        goal=(
            "Review the verified growth relationship charts and visual figures generated for this dataset. Provide a concise, "
            "bulleted executive summary of each visualization: stating the chart title, the key business growth pattern shown, "
            "and a 1-sentence decision interpretation for leadership."
        ),
        llm=LLM(**get_llm_params()),
        max_iter=1,
        verbose=True,
    )

