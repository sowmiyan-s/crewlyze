# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

from crewai import Task
from agents.cleaner import cleaner_agent
from agents.relation import relation_agent
from agents.insights import insights_agent
from agents.visualizer import visualizer_agent


def task_cooldown(task_output):
    import time
    import os
    cooldown = int(os.getenv("API_COOLDOWN", "15"))
    if cooldown > 0:
        print(f"\nTask completed. Cooldown active: sleeping for {cooldown} seconds to prevent rate limits...")
        time.sleep(cooldown)


clean_task = Task(
    agent=cleaner_agent,
    description="Analyze the dataset at 'data/cleaned_csv.csv' using read_dataset_head and get_dataset_info. Identify quality issues, then write and run Python cleaning code using 'Clean Dataset with Python Code' to fix them. Ensure the data is clean. Return a plain-text bulleted list of the cleaning steps performed.",
    expected_output="A plain text bulleted list of cleaning steps. Example:\n- Imputed missing values in Column A with mean\n- Dropped duplicate rows",
    callback=task_cooldown
)

relation_task = Task(
    agent=relation_agent,
    description="Analyze the columns and sample data of the cleaned dataset at 'data/cleaned_csv.csv'. Identify 5 key relationships that can show business meaning. Format the output strictly as:\n- X: [Column1] | Y: [Column2] | Type: [PlotType]",
    expected_output="Strictly formatted list of relationships. Example:\n- X: Age | Y: Income | Type: Scatter Plot",
    callback=task_cooldown
)

insight_task = Task(
    agent=insights_agent,
    description="Synthesize findings from the cleaned dataset 'data/cleaned_csv.csv' and the relationships. Generate 5 key business insights. List them as numbered points.",
    expected_output="Plain text numbered list of 5 business insights.",
    callback=task_cooldown
)

visualize_task = Task(
    agent=visualizer_agent,
    description="Based on the identified relationships and key business insights, write and execute Python code using 'Execute Visualization Code' to generate plots. The Python code must read from 'data/cleaned_csv.csv' and save PNG plots to the 'outputs' directory. Generate all possible meaningful plots. Ensure the code handles matplotlib layout correctly and does not fail.",
    expected_output="Summary of generated and saved visualization plots.",
    context=[relation_task, insight_task]
)

# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License
