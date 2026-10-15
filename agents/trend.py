from crewai import Agent, LLM
from config.llm_config import get_llm_params
from tools.bi_tools import BusinessIntelligenceTools

def make_trend_agent() -> Agent:
    """Factory — creates a Business Velocity & Growth Analyst Agent equipped with real velocity tools."""
    return Agent(
        name="Business Velocity & Growth Analyst",
        role="Detect temporal business velocity, growth trajectories, and revenue momentum across dates and periods",
        goal=(
            "Use your tools to identify temporal business columns (Year, Date, Quarter, Month) and calculate key growth metrics "
            "(period-over-period growth, velocity momentum, CAGR, and run-rate). Project directional growth trends, inflections, "
            "and seasonal patterns to support executive forward planning."
        ),
        backstory=(
            "You are a Quantitative Growth Strategist and Financial Trajectory Analyst. You specialize in temporal pattern "
            "recognition and recurring revenue velocity, using empirical computational tools to translate historical business data into "
            "clear growth forecasts that executives use to plan capital allocation."
        ),
        tools=[
            BusinessIntelligenceTools.calculate_velocity_and_growth,
        ],
        allow_delegation=False,
        max_iter=3,
        llm=LLM(**get_llm_params()),
        verbose=True,
    )

