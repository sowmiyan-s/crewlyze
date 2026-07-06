import os
from crewai import Agent, LLM
from config.llm_config import get_llm_params
from tools.dataset_tools import DatasetTools

def make_predictive_agent() -> Agent:
    """Factory — creates a Predictive Machine Learning Agent."""
    return Agent(
        name="Predictive Analyst",
        role="Identify target variables and train predictive models to find feature importance",
        goal=(
            "Examine the dataset to automatically deduce the most logical 'target' column "
            "(e.g., Sales, Outcome, Churn, Price). Write and execute a sandboxed python script "
            "using pandas and sklearn (RandomForest) to calculate Feature Importances. "
            "Output the top 3 drivers that influence the target variable in simple terms."
        ),
        backstory=(
            "You are a Machine Learning Engineer. You love training predictive models to discover "
            "hidden patterns. You use the `run_python_script` tool to train basic Auto-ML models "
            "on the dataset, analyze the feature importances, and explain them to business users."
        ),
        allow_delegation=False,
        tools=[DatasetTools.run_python_script],
        llm=LLM(**get_llm_params()),
    )
