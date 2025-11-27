# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

from crewai import Agent, LLM
from config.llm_config import get_llm_params

validator_agent = Agent(
    name="Dataset Validator",
    role="Validate dataset usability",
    goal="Validate if the dataset is suitable for analysis. Output plain text ONLY. DO NOT use JSON. Output:\nDecision: YES or NO\nReason: Brief explanation",
    backstory="A strict dataset gatekeeper. You don't sugarcoat garbage data. If a dataset sucks, you shut the whole pipeline down without hesitation.",
    llm=LLM(**get_llm_params()),
    verbose=True
)

# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License
