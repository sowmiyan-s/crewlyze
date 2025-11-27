# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

from crewai import Agent, LLM
from config.llm_config import get_llm_params

insights_agent = Agent(
    name="Business Intelligence Analyst",
    role="Derive actionable insights from data analysis results",
    goal="Generate 5 key business insights from the data analysis. List them as numbered points. DO NOT use JSON. Example:\n1. First insight\n2. Second insight\n...",
    backstory="You are a seasoned BI Analyst. You don't need to see every row to understand the story. You look at the column names, the identified relationships, and the data quality report to infer the underlying trends and business implications.",
    llm=LLM(**get_llm_params()),
    verbose=True
)

# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License
