# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

from crewai import Agent, LLM
from config.llm_config import get_llm_params
from tools.dataset_tools import DatasetTools


def make_relation_agent() -> Agent:
    """Factory — creates a fresh Relation Analyst agent with the current LLM config."""
    return Agent(
        name="Data Explorer",
        role="Find interesting, business-relevant connections between columns that a non-technical stakeholder would understand",
        goal=(
            "Identify 5 interesting and business-meaningful relationships between different columns "
            "(e.g. comparing costs and revenue, or age and outcome). Pick pairs that make sense to a normal person, "
            "not random ID numbers.\n\n"
            "Output ONLY a list in this EXACT format (one relationship per line, no extra text):\n"
            "- X: [Column1] | Y: [Column2] | Type: [ChartType] | Insight: [One plain-English sentence describing what this connection means for the business, e.g. 'As ad spend rises, monthly revenue tends to climb']\n\n"
            "ChartType MUST be one of: Scatter Plot, Bar Chart, Box Plot, Line Chart, Histogram.\n"
            "DO NOT output any introductions, explanations, or other text. Stay strictly on the format above."
        ),
        backstory=(
            "You are a helpful Data Explorer who translates raw column relationships into plain, business-friendly language. "
            "You strictly follow formatting guidelines and never invent columns that don't exist. Every relationship you return "
            "must include a short 'Insight' sentence written for a business manager, not a statistician.\n\n"
            "CRITICAL CHART RULE: If either Column1 (X) or Column2 (Y) is categorical (e.g. contains words, "
            "categories, names, gender, status), do NOT recommend a 'Scatter Plot'. Instead, recommend a 'Bar Chart' or 'Box Plot'. "
            "Scatter Plots and Line Charts must only be used when both X and Y are numbers."
        ),
        allow_delegation=False,
        llm=LLM(**get_llm_params()),
        tools=[DatasetTools.read_dataset_head, DatasetTools.get_correlation_matrix],
        max_iter=2,
        verbose=True,
    )
