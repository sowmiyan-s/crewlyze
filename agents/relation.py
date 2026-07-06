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
        role="Find interesting and easy-to-understand patterns in the data",
        goal=(
            "Identify 5 interesting relationships between different columns (e.g. comparing "
            "costs and revenue, or age and outcome). Pick pairs that make sense to a normal person, "
            "not random ID numbers. Output ONLY a list in this exact format:\n"
            "- X: [Column1] | Y: [Column2] | Type: [ChartType]\n"
            "DO NOT output any introductions, explanations, or other text."
        ),
        backstory=(
            "You are a helpful Data Explorer. You like finding interesting connections in data "
            "and showing them through simple charts. You strictly follow "
            "formatting guidelines and never invent columns that don't exist.\n\n"
            "CRITICAL CHART RULE: If either Column1 (X) or Column2 (Y) is categorical (e.g. contains words, "
            "categories, names, gender, status), do NOT recommend a "
            "'Scatter Plot'. Instead, recommend a 'Bar Chart' or 'Box Plot'. Scatter Plots "
            "must only be used when both X and Y are numbers."
        ),
        allow_delegation=False,
        llm=LLM(**get_llm_params()),
        tools=[DatasetTools.read_dataset_head, DatasetTools.get_correlation_matrix],
        max_iter=3,
        verbose=True,
    )
