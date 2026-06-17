# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License


import logging
import sys
import os
from pathlib import Path
import pandas as pd
import webbrowser
from dotenv import load_dotenv

load_dotenv()

# Disable CrewAI Telemetry to prevent timeouts
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("opentelemetry").setLevel(logging.ERROR)

# API key validation is now handled by the LLM config module

try:
    from crewai import Crew
except ImportError as e:
    print(f"ERROR: {e}\nRun: pip install crewai")
    sys.exit(1)


def run_crew(csv_path: str):
    
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Cleanup existing visualizations
    for existing_file in output_dir.glob("*.png"):
        existing_file.unlink()
    print("Cleaned up previous visualizations.")
    
    print("=" * 50)
    print("Multi Agent Data Analysis with Crew AI")
    print("=" * 50)
    
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: File not found at {csv_path}")
        return None

    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"Columns: {', '.join(df.columns[:10])}...")

    # Data Cleaning - delegate to cleaner agent
    print("\n--- Copying original dataset to data/cleaned_csv.csv for Agent Cleaning ---")
    cleaned_file_path = Path("data") / "cleaned_csv.csv"
    cleaned_file_path.parent.mkdir(exist_ok=True)
    df.to_csv(cleaned_file_path, index=False)
    print("Dataset copied. Cleaner agent will clean this file.\n")
    
    import importlib
    import sys

    # Reload modules if already loaded to ensure fresh initialization with current env vars
    for module_name in ['agents.cleaner', 'agents.relation', 'agents.insights', 'agents.visualizer', 'workflows.pipeline']:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])

    from agents.cleaner import cleaner_agent
    from agents.relation import relation_agent
    from agents.insights import insights_agent
    from agents.visualizer import visualizer_agent
    from workflows.pipeline import (
        clean_task,
        relation_task,
        insight_task,
        visualize_task,
    )

    crew = Crew(
        agents=[
            cleaner_agent,
            relation_agent,
            insights_agent,
            visualizer_agent,
        ],
        tasks=[
            clean_task,
            relation_task,
            insight_task,
            visualize_task,
        ],
        max_rpm=15,
        cache=True,
        verbose=True,
    )

    try:
        result = crew.kickoff()
    except Exception as e:
        print(f"Error during crew execution: {e}")
        return {
            'dataframe': df,
            'cleaning_steps': "Error during analysis",
            'validation': "N/A",
            'relations': "Error during analysis",
            'code': "Error during analysis",
            'insights': f"Analysis failed: {str(e)}",
            'output_dir': output_dir
        }
    
    # Extract outputs safely based on sequence order
    clean_output = ""
    relation_output = ""
    insights_output = ""
    visualize_output = ""
    
    if len(crew.tasks) >= 4:
        clean_output = str(crew.tasks[0].output.raw if hasattr(crew.tasks[0].output, 'raw') else crew.tasks[0].output)
        relation_output = str(crew.tasks[1].output.raw if hasattr(crew.tasks[1].output, 'raw') else crew.tasks[1].output)
        insights_output = str(crew.tasks[2].output.raw if hasattr(crew.tasks[2].output, 'raw') else crew.tasks[2].output)
        visualize_output = str(crew.tasks[3].output.raw if hasattr(crew.tasks[3].output, 'raw') else crew.tasks[3].output)

    # Reload the dataframe since it was cleaned in-place by the cleaner agent
    try:
        cleaned_df = pd.read_csv(cleaned_file_path)
    except Exception:
        cleaned_df = df

    # Return structured data
    return {
        'dataframe': cleaned_df,
        'cleaning_steps': clean_output,
        'validation': "Skipped - replaced by visualization workflow",
        'relations': relation_output,
        'code': visualize_output,
        'insights': insights_output,
        'output_dir': output_dir
    }


if __name__ == "__main__":
    default_path = (Path.cwd() / "data" / "TB_Burden_Country.csv").resolve()
    a = input(f"Enter the path to your CSV file (default: {default_path.name}): ") or str(default_path)
    report = run_crew(a)
    if report:
        print("\nAnalysis Complete.")
        print("Multi Agent Data Analysis with Crew AI")
        print("Prithiv.A.K  Sebin.S  Sowmiyan.s")
