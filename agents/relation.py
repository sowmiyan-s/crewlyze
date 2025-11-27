# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

from crewai import Agent, LLM
from config.llm_config import get_llm_params

relation_agent = Agent(
    name="Analyst",
    role="Analyze dataset and identify key relationships",
    goal="Identify key relationships between columns for visualization. List them strictly in this format:\n- X: Column1 | Y: Column2 | Type: Scatter Plot\n- X: Column1 | Y: None | Type: Histogram",
    backstory="You are a Senior Data Analyst who reads CSV files carefully. You ALWAYS use the ACTUAL column names from df.columns, never invented names. You know that different data requires different charts and you select the right visualization type for each relationship.",
    allow_delegation=False,
    llm=LLM(**get_llm_params()),
    verbose=True
)

# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License
