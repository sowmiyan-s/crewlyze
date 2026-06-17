
# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

import os
from dotenv import load_dotenv

load_dotenv()


# ========================
# LLM PROVIDER CONFIGURATION & DETAILS
# ========================

def get_llm_config():
    # Retrieve provider dynamically at runtime
    provider = os.getenv("LLM_PROVIDER", "nvidia")
    
    configs = {
        "nvidia": {
            "model": "nvidia_nim/mistralai/mistral-medium-3.5-128b",
            "api_key": os.getenv("NVIDIA_API_KEY", "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"),
        },
        "groq": {
            "model": "groq/llama-3.1-8b-instant",
            "api_key": os.getenv("GROQ_API_KEY"),
        },
        "openai": {
            "model": "gpt-4o-mini",
            "api_key": os.getenv("OPENAI_API_KEY"),
        },
        "ollama": {
            "model": "ollama/llama3",
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        },
        "anthropic": {
            "model": "claude-3-5-sonnet-20241022",
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
        },
        "huggingface": {
            "model": "huggingface/HuggingFaceH4/zephyr-7b-beta",
            "api_key": os.getenv("HUGGINGFACE_API_KEY"),
        },
        "mistral": {
            "model": "mistral/mistral-tiny",
            "api_key": os.getenv("MISTRAL_API_KEY"),
        },
        "gemini": {
            "model": "gemini/gemini-pro",
            "api_key": os.getenv("GEMINI_API_KEY"),
        },
    }
    
    if provider not in configs:
        raise ValueError(
            f"Invalid LLM provider: {provider}. "
            f"Choose from: {', '.join(configs.keys())}"
        )
    
    config = configs[provider]
    
    # Validate that required credentials are present
    if provider in ["groq", "openai", "anthropic", "huggingface", "mistral", "gemini", "nvidia"]:
        if not config.get("api_key"):
            raise ValueError(
                f"{provider.upper()}_API_KEY environment variable is not set. "
                f"Please enter your API key in the sidebar configuration."
            )
    
    return config


def get_llm_params():
    config = get_llm_config()
    
    # Check if a specific model is requested via env var
    model = os.getenv("LLM_MODEL")
    if not model:
        model = config["model"]
        
    params = {
        "model": model,
        "temperature": 0.1,
        "max_retries": 5
    }
    
    if "api_key" in config and config["api_key"]:
        params["api_key"] = config["api_key"]
    
    if "base_url" in config:
        params["base_url"] = config["base_url"]
    
    return params


# ========================
# USAGE INSTRUCTIONS
# ========================

# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

