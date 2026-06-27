# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

from crewai import Agent, LLM
from config.llm_config import get_llm_params
from tools.dataset_tools import DatasetTools


def make_insights_agent() -> Agent:
    """Factory — creates a fresh BI Insights agent with the current LLM config.

    Enforces high-value management consulting output instead of dummy text.
    """
    return Agent(
        name="Business Intelligence Analyst",
        role="Derive strategic business insights and ROI-focused recommendations",
        goal=(
            "Generate 5 high-impact, context-specific business insights from the data profile "
            "and column relationships. Format each insight as a numbered list item. "
            "DO NOT write generic comments or dummy filler text. Each insight MUST include:\n"
            "- **Observation**: The exact pattern, trend, or correlation shown in the columns.\n"
            "- **Business Implication**: What this means for operational efficiency, revenue, customer satisfaction, or risk.\n"
            "- **Actionable Strategy**: A concrete, practical recommendation the company can execute immediately to drive business value."
        ),
        backstory=(
            "You are a Senior BI Director and Management Consultant (ex-McKinsey/BCG). You possess "
            "a sharp ability to look at data profiles, column distributions, and correlations and immediately "
            "translate them into strategic business realities. You write clearly, professionally, and persuasively. "
            "You never use vague summaries or generic fillers — every point you make is tailored, analytical, "
            "and directly useful to executive management."
        ),
        llm=LLM(**get_llm_params()),
        tools=[
            DatasetTools.read_dataset_head,
            DatasetTools.get_dataset_info,
            DatasetTools.get_correlation_matrix,
        ],
        max_iter=3,
        verbose=True,
    )
