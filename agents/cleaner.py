# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

from crewai import Agent, LLM
from config.llm_config import get_llm_params
from tools.dataset_tools import DatasetTools


def make_cleaner_agent() -> Agent:
    """Factory — creates a fresh Data Cleaner agent with the current LLM config."""
    return Agent(
        name="Data Cleaner",
        role="Dataset cleaning expert & Data Type Inspector",
        backstory=(
            "You are an expert data cleaning specialist. First, analyze the dataset schema and 4-5 actual sample data rows "
            "for each column. Carefully inspect column contents to identify hidden numeric or date values disguised as strings/objects "
            "(e.g. formatted currency '$1,000', percentages '95%', trailing spaces, or numbers stored as strings). "
            "Write a Python script using 'Clean Dataset with Python Code' to convert these columns into true numeric (int64/float64) "
            "or datetime types so that downstream visualizers plot continuous numeric scales rather than discrete character labels."
        ),
        goal=(
            "Inspect sample data rows (4-5 rows) for every column, fix quality issues (missing values, duplicates, bad formatting), "
            "and convert all text-disguised numbers into true numeric dtypes using pd.to_numeric(). "
            "Execute Python code using 'Clean Dataset with Python Code' and return a concise bulleted list of cleaning actions."
        ),
        llm=LLM(**get_llm_params()),
        tools=[
            DatasetTools.read_dataset_head,
            DatasetTools.get_dataset_info,
            DatasetTools.clean_dataset_with_python,
        ],
        max_iter=5,
        verbose=True,
    )
