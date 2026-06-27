# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

from crewai import Agent, LLM
from config.llm_config import get_llm_params
from tools.dataset_tools import DatasetTools


def make_cleaner_agent() -> Agent:
    """Factory — creates a fresh Data Cleaner agent with the current LLM config.

    Called on every run_crew() invocation so that sidebar provider / model
    changes are always reflected without requiring a module reload.
    """
    return Agent(
        name="Data Cleaner",
        role="Dataset cleaning expert",
        backstory=(
            "You are an expert data cleaning specialist. You analyze columns and "
            "sample data of a dataset, identify data quality problems (like missing "
            "values, duplicates, wrong data types, or inconsistent columns), and then "
            "write and execute Python code using your tool to clean the dataset directly."
        ),
        goal=(
            "Clean the dataset at the given file path by executing a Python script using "
            "'Clean Dataset with Python Code'. When done, return a concise plain-text "
            "bulleted list of the cleaning actions you took."
        ),
        llm=LLM(**get_llm_params()),
        tools=[
            DatasetTools.read_dataset_head,
            DatasetTools.get_dataset_info,
            DatasetTools.clean_dataset_with_python,
        ],
        verbose=True,
    )
