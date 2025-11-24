"""
Centralized LLM Configuration

This file allows you to easily switch between different LLM providers
without modifying individual agent files.

Supported providers:
- groq: Groq cloud API (fast, recommended)
- openai: OpenAI API
- ollama: Local Ollama server
- anthropic: Anthropic Claude API
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ========================
# LLM PROVIDER CONFIGURATION
# ========================
# Change this to switch providers: "groq", "openai", "ollama", "anthropic"
PROVIDER = os.getenv("LLM_PROVIDER", "groq")

# ========================
# PROVIDER CONFIGURATIONS
# ========================

GROQ_CONFIG = {
    "model": "groq/llama-3.3-70b-versatile",
    "api_key": os.getenv("GROQ_API_KEY"),
}

OPENAI_CONFIG = {
    "model": "gpt-4o-mini",
    "api_key": os.getenv("OPENAI_API_KEY"),
}

OLLAMA_CONFIG = {
    "model": "ollama/llama3",
    "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
}

ANTHROPIC_CONFIG = {
    "model": "claude-3-5-sonnet-20241022",
    "api_key": os.getenv("ANTHROPIC_API_KEY"),
}

# ========================
# PROVIDER MAP
# ========================
PROVIDER_CONFIGS = {
    "groq": GROQ_CONFIG,
    "openai": OPENAI_CONFIG,
    "ollama": OLLAMA_CONFIG,
    "anthropic": ANTHROPIC_CONFIG,
}


def get_llm_config():
    """
    Get the current LLM configuration based on PROVIDER setting.
    
    Returns:
        dict: Configuration dictionary with model and api_key/base_url
    """
    if PROVIDER not in PROVIDER_CONFIGS:
        raise ValueError(
            f"Invalid LLM provider: {PROVIDER}. "
            f"Choose from: {', '.join(PROVIDER_CONFIGS.keys())}"
        )
    
    config = PROVIDER_CONFIGS[PROVIDER]
    
    # Validate that required credentials are present
    if PROVIDER in ["groq", "openai", "anthropic"]:
        if not config.get("api_key"):
            raise ValueError(
                f"{PROVIDER.upper()}_API_KEY environment variable is not set. "
                f"Please add it to Replit Secrets."
            )
    
    return config


def get_llm_params():
    """
    Get LLM parameters ready for CrewAI LLM initialization.
    
    Returns:
        dict: Parameters to pass to LLM() constructor
    """
    config = get_llm_config()
    
    params = {"model": config["model"]}
    
    if "api_key" in config and config["api_key"]:
        params["api_key"] = config["api_key"]
    
    if "base_url" in config:
        params["base_url"] = config["base_url"]
    
    return params


# ========================
# USAGE INSTRUCTIONS
# ========================
"""
HOW TO USE:

1. In your .env file or Replit Secrets, set:
   LLM_PROVIDER=groq  (or openai, ollama, anthropic)
   GROQ_API_KEY=your_key_here
   
2. In your agent files, import and use:
   from crewai import Agent, LLM
   from config.llm_config import get_llm_params
   
   my_agent = Agent(
       name="My Agent",
       role="My Role",
       goal="My Goal",
       backstory="My Backstory",
       llm=LLM(**get_llm_params()),
       verbose=True
   )

3. To switch providers, just change LLM_PROVIDER in your .env file!

EXAMPLES:

# Use Groq (default)
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...

# Use OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Use local Ollama
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434

# Use Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
"""
