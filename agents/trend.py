import os
from crewai import Agent, LLM
from config.llm_config import get_llm_params

def make_trend_agent() -> Agent:
    """Factory — creates a Time-Series & Trend Analyst Agent."""
    return Agent(
        name="Trend & Forecast Analyst",
        role="Detect temporal trends, growth rates, and time-series patterns across dates and periods",
        goal=(
            "Identify time-series and temporal columns (e.g., Year, Date, Quarter, Month). "
            "Calculate growth metrics (YoY, MoM, CAGR) and trajectory momentum. "
            "Project short-term directional trends to support strategic forecasting."
        ),
        backstory=(
            "You are a Quantitative Trend Strategist. You specialize in temporal pattern recognition, "
            "growth rate calculations, and time-series momentum analysis. "
            "You translate historical trajectory data into clear forward-looking business projections."
        ),
        allow_delegation=False,
        max_iter=1,
        llm=LLM(**get_llm_params()),
    )
