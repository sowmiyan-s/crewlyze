from crewai import Agent, LLM
from config.llm_config import get_llm_params

code_gen_agent = Agent(
    name="Code Generator",
    role="Write visualization code",
    goal="Generate matplotlib code for the provided chart relations.",
    backstory="Python developer focused on matplotlib.",
    allow_delegation=False,
    llm=LLM(**get_llm_params()),
    verbose=True
)
