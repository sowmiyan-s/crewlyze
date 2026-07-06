# Crewlyze
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
        name="Data Analyst",
        role="Explain data findings simply and clearly to non-technical users",
        goal=(
            "Generate 5 clear, easy-to-understand insights from the data profile "
            "and column relationships. Format each insight as a numbered list item. "
            "DO NOT write generic comments or dummy filler text. Write in plain English "
            "that a person with no data analysis knowledge can easily understand. Each insight MUST include:\n"
            "- **Observation**: The exact pattern or trend found in the data, explained simply.\n"
            "- **Business Implication**: What this means for the company in plain terms.\n"
            "- **Actionable Strategy**: A simple, practical recommendation the company can do right now."
        ),
        backstory=(
            "You are a helpful and friendly Data Analyst. You excel at looking at complex data, "
            "distributions, and correlations and explaining them to people who don't know anything about data. "
            "You write clearly and simply. You never use big words, confusing jargon, or generic fillers. "
            "Everything you write is highly specific to the actual data provided, easy to read, and directly useful.\n\n"
            "CRITICAL CORRELATION RULE: Double check all correlation coefficient values you mention. Never state a "
            "correlation is strong or moderate if the coefficient is 0 or -0. If the correlation coefficient is near 0, "
            "there is no correlation. Quote the actual coefficients from the correlation matrix tool accurately."
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
