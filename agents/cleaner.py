# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

from crewai import Agent, LLM
from config.llm_config import get_llm_params
from tools.dataset_tools import DatasetTools


def make_cleaner_agent() -> Agent:
    """Factory — creates a fresh Data Cleaner agent with the current LLM config.

    max_iter=5: read profile (already in task desc) → write cleaning code →
    call clean_dataset_with_python → verify → final answer. 5 steps is enough.
    """
    return Agent(
        name="Data Cleaner",
        role="Dataset cleaning expert",
        backstory=(
            "You are an expert data cleaning specialist. The task description already "
            "contains a full dataset profile (shape, dtypes, missing %, sample rows). "
            "Use that profile to immediately identify quality issues and write cleaning "
            "code — DO NOT call read_dataset_head or get_dataset_info first."
        ),
        goal=(
            "Clean the dataset at the given file path by executing a Python script using "
            "'Clean Dataset with Python Code'. When done, return a concise plain-text "
            "bulleted list of the cleaning actions you took."
        ),
        llm=LLM(**get_llm_params()),
        tools=[
            DatasetTools.read_dataset_head,    # fallback only
            DatasetTools.get_dataset_info,     # fallback only
            DatasetTools.clean_dataset_with_python,
        ],
        max_iter=5,
        verbose=True,
    )
