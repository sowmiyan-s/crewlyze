# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

from crewai import Agent, LLM
from config.llm_config import get_llm_params


def make_cleaner_agent() -> Agent:
    """Factory — creates a fresh Data Cleaner agent with the current LLM config."""
    return Agent(
        name="Data Cleaner",
        role="Dataset Hygiene & Data Quality Specialist",
        backstory=(
            "You are an expert data hygiene specialist. You review data type conversions, missing value handling, "
            "and schema validation performed on the dataset. You summarize data quality improvements in clear, "
            "professional terms so non-technical executives understand how their data was sanitized."
        ),
        goal=(
            "Review the dataset profile and automated type conversions performed. Output a concise bulleted list "
            "explaining the data cleaning actions, type coercions, and quality validations in business-friendly terms."
        ),
        llm=LLM(**get_llm_params()),
        max_iter=1,
        verbose=True,
    )

