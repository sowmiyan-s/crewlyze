# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

from crewai import Agent, LLM
from config.llm_config import get_llm_params


def make_cleaner_agent() -> Agent:
    """Factory — creates a fresh Data Quality & Hygiene Auditor agent with the current LLM config."""
    return Agent(
        name="Data Quality Auditor",
        role="Senior Data Hygiene & Quality Governance Specialist",
        backstory=(
            "You are a seasoned data governance and data hygiene specialist. You rigorously audit "
            "dataset completeness, type conversions, missingness distributions, and structural anomalies. "
            "You translate technical data transformations into executive-grade data health assessments, "
            "clearly articulating the business risks of unhygienic data and the strategic reliability of the cleaned dataset."
        ),
        goal=(
            "Audit the dataset profile, data quality health, and automated transformations performed. Output a structured "
            "executive data quality audit highlighting data completeness, schema coercions, reliability guarantees, "
            "and business context in clear, professional terms."
        ),
        llm=LLM(**get_llm_params()),
        max_iter=1,
        verbose=True,
    )

