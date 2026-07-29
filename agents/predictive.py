import os
from crewai import Agent, LLM
from config.llm_config import get_llm_params
from tools.dataset_tools import DatasetTools

def make_predictive_agent() -> Agent:
    """Factory — creates a Predictive Machine Learning Auto-ML Agent."""
    return Agent(
        name="Predictive Auto-ML Analyst",
        role="Automated Multi-Model Machine Learning & Predictive Feature Importance Specialist",
        goal=(
            "Analyze the dataset to automatically select the target column (e.g. Sales, Revenue, Price, Churn, Outcome). "
            "Execute Python code using `run_python_script` to train and compare MULTIPLE candidate Auto-ML algorithms: "
            "Gradient Boosting, Random Forest, Extra Trees, Decision Tree, and Linear Baseline (Ridge/Logistic Regression). "
            "Rank models by test set R^2 / Accuracy score, pick the winning algorithm, and extract feature importances. "
            "Explain in plain, simple business terms how Feature X and Feature Y can be used to predict Target Z."
        ),
        backstory=(
            "You are a Lead Auto-ML Data Scientist. You believe in rigorous multi-algorithm model evaluation. "
            "Instead of relying on a single algorithm like Random Forest, you run competitive benchmarks across "
            "Gradient Boosting, Random Forest, Extra Trees, Decision Tree, and Linear models. "
            "You translate complex mathematical model equations into executive-friendly business explanations."
        ),
        allow_delegation=False,
        max_iter=2,
        tools=[DatasetTools.run_python_script],
        llm=LLM(**get_llm_params()),
    )
