# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

from crewai import Agent, LLM
from config.llm_config import get_llm_params

from tools.dataset_tools import DatasetTools

visualizer_agent = Agent(
    name="Data Visualizer",
    role="Visualization & Plotting Expert",
    backstory="You are an expert data visualization specialist who creates beautiful and clear charts to extract business intelligence. You analyze the dataset columns, sample data, identified relationships, and key business insights, then write and execute Python visualization scripts to save the charts as PNG images in the 'outputs' folder.",
    goal="Generate Python code using matplotlib/seaborn to produce meaningful visualizations for the insights and relations, then run the code using the 'Execute Visualization Code' tool. Save all plots to the 'outputs' directory.",
    llm=LLM(**get_llm_params()),
    tools=[DatasetTools.read_dataset_head, DatasetTools.get_dataset_info, DatasetTools.execute_visualization_code],
    verbose=True
)

# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License
