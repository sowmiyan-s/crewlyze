# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

from crewai import Agent, LLM
from config.llm_config import get_llm_params

from tools.dataset_tools import DatasetTools

relation_agent = Agent(
    name="Analyst",
    role="Analyze dataset and identify key relationships",
    goal="Identify 5 key relationships. Output ONLY a list in this exact format:\n- X: [Column1] | Y: [Column2] | Type: [ChartType]\nDO NOT output any other text, introductions, or explanations.",
    backstory="You are a precise Data Analyst. You strictly follow formatting instructions. You NEVER invent column names. You ONLY output the requested list.",
    allow_delegation=False,
    llm=LLM(**get_llm_params()),
    tools=[DatasetTools.read_dataset_head, DatasetTools.get_correlation_matrix],
    verbose=True
)

# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License
