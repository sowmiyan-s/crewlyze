# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

import os
import requests
from dotenv import load_dotenv

load_dotenv()


# ========================
# LLM PROVIDER CONFIGURATION & DETAILS
# ========================

# Keys accepted by crewai.LLM constructor.
# Extra keys (e.g. max_tokens, top_p, multimodal) are stripped before passing.
_LLM_VALID_KEYS = {"model", "api_key", "base_url", "temperature", "max_retries", "timeout"}


def get_llm_config() -> dict:
    """Return the raw provider config dict (may contain extra keys)."""
    provider = os.getenv("LLM_PROVIDER", "nvidia")

    configs = {
        "nvidia": {
            "model":   "nvidia_nim/mistralai/mistral-medium-3.5-128b",
            "api_key": os.getenv("NVIDIA_API_KEY"),
        },
        "minimax": {
            "model":      "minimaxai/minimax-m3",
            "api_key":    os.getenv("NVIDIA_API_KEY"),   # served via NVIDIA NIM
            "base_url":   "https://integrate.api.nvidia.com/v1",
            # Extra metadata — NOT forwarded to LLM() constructor
            "max_tokens": 8192,
            "temperature": 1.00,
            "top_p":      0.95,
            "multimodal": True,
        },
        "groq": {
            "model":   "groq/llama-3.1-8b-instant",
            "api_key": os.getenv("GROQ_API_KEY"),
        },
        "openai": {
            "model":   "gpt-4o-mini",
            "api_key": os.getenv("OPENAI_API_KEY"),
        },
        "ollama": {
            "model":    "ollama/llama3",
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        },
        "anthropic": {
            "model":   "claude-3-5-sonnet-20241022",
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
        },
        "huggingface": {
            "model":   "huggingface/HuggingFaceH4/zephyr-7b-beta",
            "api_key": os.getenv("HUGGINGFACE_API_KEY"),
        },
        "mistral": {
            "model":   "mistral/mistral-tiny",
            "api_key": os.getenv("MISTRAL_API_KEY"),
        },
        "gemini": {
            "model":   "gemini/gemini-pro",
            "api_key": os.getenv("GEMINI_API_KEY"),
        },
    }

    if provider not in configs:
        raise ValueError(
            f"Invalid LLM provider: '{provider}'. "
            f"Choose from: {', '.join(configs.keys())}"
        )

    config = configs[provider]

    # Validate required credentials
    requires_key = {"groq", "openai", "anthropic", "huggingface", "mistral", "gemini", "nvidia", "minimax"}
    if provider in requires_key and not config.get("api_key"):
        raise ValueError(
            f"{provider.upper()}_API_KEY environment variable is not set. "
            "Please enter your API key in the sidebar configuration."
        )

    return config


def get_llm_params() -> dict:
    """Return a dict of keyword args safe to pass directly to crewai.LLM(**...).

    Extra provider-specific keys (max_tokens, top_p, multimodal, etc.) are
    filtered out so crewai.LLM never receives unexpected kwargs.
    """
    config = get_llm_config()

    model = os.getenv("LLM_MODEL") or config["model"]

    params: dict = {
        "model":       model,
        "temperature": config.get("temperature", 0.1),
        "max_retries": 5,
    }

    if config.get("api_key"):
        params["api_key"] = config["api_key"]

    if config.get("base_url"):
        params["base_url"] = config["base_url"]

    # Strip any keys that crewai.LLM does not accept
    return {k: v for k, v in params.items() if k in _LLM_VALID_KEYS}


# ========================
# MINIMAX-M3 DIRECT CLIENT
# ========================

def call_minimax_m3(messages: list, stream: bool = False, **kwargs) -> dict:
    """
    Direct HTTP client for MiniMax-M3 via NVIDIA NIM.

    MiniMax-M3 is multimodal — messages content can be a list of parts:
        [{"type": "text", "text": "Describe this."},
         {"type": "image_url", "image_url": {"url": "https://..."}},
         {"type": "video_url", "video_url": {"url": "https://..."}}]

    Args:
        messages: List of {"role": ..., "content": ...} dicts.
        stream:   If True, returns raw streaming response.
        **kwargs: Override max_tokens, temperature, top_p, etc.

    Returns:
        Parsed JSON dict (non-stream) or requests.Response (stream).
    """
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY environment variable is not set.")

    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream" if stream else "application/json",
    }
    payload = {
        "model":       "minimaxai/minimax-m3",
        "messages":    messages,
        "max_tokens":  kwargs.get("max_tokens",  8192),
        "temperature": kwargs.get("temperature", 1.00),
        "top_p":       kwargs.get("top_p",       0.95),
        "stream":      stream,
    }

    response = requests.post(invoke_url, headers=headers, json=payload, stream=stream)
    response.raise_for_status()

    if stream:
        return response  # Caller iterates response.iter_lines()
    return response.json()
