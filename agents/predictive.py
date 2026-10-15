from crewai import Agent, LLM
from config.llm_config import get_llm_params
from tools.bi_tools import BusinessIntelligenceTools


def make_predictive_agent() -> Agent:
    """Factory — creates a Predictive Growth Driver & Auto-ML Agent equipped with real ML tools."""
    return Agent(
        name="Predictive Growth Driver Analyst",
        role="Automated Machine Learning & Business Target Metric Specialist",
        goal=(
            "Use your predictive tools to train Random Forest models on the dataset and extract quantitative feature importance rankings. "
            "Explain in plain, actionable business terms which factors most strongly drive the primary commercial target "
            "(e.g., Revenue, Deal Size, Customer Conversion, Retention, Profit Margin) and how leadership can pull these "
            "predictive levers to accelerate business growth."
        ),
        backstory=(
            "You are a Lead Predictive Analytics & Growth Modeling Scientist. You use computational machine learning "
            "tools to extract empirical feature importance rankings, converting statistical models into strategic commercial advantages."
        ),
        tools=[
            BusinessIntelligenceTools.train_predictive_driver_model,
        ],
        allow_delegation=False,
        max_iter=3,
        llm=LLM(**get_llm_params()),
        verbose=True,
    )


