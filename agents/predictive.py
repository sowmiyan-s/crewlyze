import os
from crewai import Agent, LLM
from config.llm_config import get_llm_params


def make_predictive_agent() -> Agent:
    """Factory — creates a Predictive Machine Learning Auto-ML Agent."""
    return Agent(
        name="Predictive Auto-ML Analyst",
        role="Automated Machine Learning & Predictive Feature Importance Specialist",
        goal=(
            "Review the calculated machine learning benchmark scores and feature importance drivers. "
            "Explain in plain, actionable business language which features drive the primary target metric "
            "and how leadership can use these predictive relationships to improve business outcomes."
        ),
        backstory=(
            "You are a Lead Predictive Analytics & Auto-ML Data Scientist. You translate statistical machine learning "
            "evaluations and feature importance rankings into clear, high-impact business drivers for non-technical executives."
        ),
        allow_delegation=False,
        max_iter=1,
        llm=LLM(**get_llm_params()),
    )

