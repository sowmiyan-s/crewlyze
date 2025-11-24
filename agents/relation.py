from crewai import Agent, LLM
from config.llm_config import get_llm_params

relation_agent = Agent(
    name="Analyst",
    role="Analyze dataset and identify key relationships",
    goal="Read data/input.csv and find numerical columns to visualize. Return JSON: [{'x':'col','y':'col','type':'scatter'}]",
    backstory="Data analysis expert. Fast and direct.",
    allow_delegation=False,
    llm=LLM(**get_llm_params()),
    verbose=True
)
