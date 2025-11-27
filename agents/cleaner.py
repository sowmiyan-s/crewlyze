# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

from crewai import Agent, LLM
from config.llm_config import get_llm_params

cleaner_agent = Agent(
    name="Data Cleaner",
    role="Clean dataset",
    backstory="A no-nonsense data mechanic who hates messy CSVs. You grew up debugging trash datasets and built a rep for turning corrupt data into clean, analysis-ready gold.",
    goal="List the data cleaning steps performed, one per line. Be concise. DO NOT use JSON. Example:\n- Removed duplicates\n- Filled missing values",
    llm=LLM(**get_llm_params()),
    verbose=True
)

# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License
