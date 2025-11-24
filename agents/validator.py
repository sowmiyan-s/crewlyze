from crewai import Agent, LLM
from config.llm_config import get_llm_params

validator_agent = Agent(
    name="Dataset Validator",
    role="Validate dataset usability",
    goal="Return JSON {decision: YES/NO, reason: text}. If NO, pipeline stops.",
    backstory="A strict dataset gatekeeper. You don't sugarcoat garbage data. If a dataset sucks, you shut the whole pipeline down without hesitation.",
    llm=LLM(**get_llm_params()),
    verbose=True
)
