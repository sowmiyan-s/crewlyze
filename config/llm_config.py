# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# NVIDIA NIM OpenAI-compatible endpoint (required for LiteLLM / CrewAI)
NVIDIA_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Keys accepted by crewai.LLM constructor.
_LLM_VALID_KEYS = {"model", "api_key", "base_url", "temperature", "max_retries", "timeout"}


def _sync_nvidia_env(api_key: str) -> None:
    """Keep NVIDIA env vars in sync for LiteLLM and direct HTTP clients."""
    if api_key:
        os.environ["NVIDIA_API_KEY"] = api_key
        os.environ["NVIDIA_NIM_API_KEY"] = api_key


def get_llm_config() -> dict:
    """Return the raw provider config dict (may contain extra keys)."""
    from config.context import current_llm_provider, current_llm_api_key
    provider = current_llm_provider.get() or os.getenv("LLM_PROVIDER", "nvidia")

    configs = {
        "nvidia": {
            "model":    "nvidia_nim/meta/llama-3.1-8b-instruct",
            "api_key":  current_llm_api_key.get() or os.getenv("NVIDIA_API_KEY"),
            "base_url": NVIDIA_NIM_BASE_URL,
        },
        "minimax": {
            "model":      "nvidia_nim/minimaxai/minimax-m3",
            "api_key":    current_llm_api_key.get() or os.getenv("NVIDIA_API_KEY"),
            "base_url":   NVIDIA_NIM_BASE_URL,
            "max_tokens": 8192,
            "temperature": 1.00,
            "top_p":      0.95,
            "multimodal": True,
        },
        "groq": {
            "model":   "groq/llama-3.1-8b-instant",
            "api_key": current_llm_api_key.get() or os.getenv("GROQ_API_KEY"),
        },
        "openai": {
            "model":   "gpt-4o-mini",
            "api_key": current_llm_api_key.get() or os.getenv("OPENAI_API_KEY"),
        },
        "ollama": {
            "model":    "ollama/llama3",
            "base_url": current_llm_api_key.get() or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        },
        "anthropic": {
            "model":   "claude-3-5-sonnet-20241022",
            "api_key": current_llm_api_key.get() or os.getenv("ANTHROPIC_API_KEY"),
        },
        "huggingface": {
            "model":   "huggingface/HuggingFaceH4/zephyr-7b-beta",
            "api_key": current_llm_api_key.get() or os.getenv("HUGGINGFACE_API_KEY"),
        },
        "mistral": {
            "model":   "mistral/mistral-tiny",
            "api_key": current_llm_api_key.get() or os.getenv("MISTRAL_API_KEY"),
        },
        "gemini": {
            "model":   "gemini/gemini-pro",
            "api_key": current_llm_api_key.get() or os.getenv("GEMINI_API_KEY"),
        },
        "cohere": {
            "model":   "cohere/command-r-plus",
            "api_key": current_llm_api_key.get() or os.getenv("COHERE_API_KEY"),
        },
        "together": {
            "model":   "together_ai/meta-llama/Llama-3-70b-chat-hf",
            "api_key": current_llm_api_key.get() or os.getenv("TOGETHER_API_KEY"),
        },
        "openrouter": {
            "model":   "openrouter/google/gemma-2-9b-it",
            "api_key": current_llm_api_key.get() or os.getenv("OPENROUTER_API_KEY"),
        },
        "deepseek": {
            "model":   "deepseek/deepseek-chat",
            "api_key": current_llm_api_key.get() or os.getenv("DEEPSEEK_API_KEY"),
        },
        "perplexity": {
            "model":   "perplexity/llama-3-sonar-large-32k-chat",
            "api_key": current_llm_api_key.get() or os.getenv("PERPLEXITY_API_KEY"),
        },
    }

    if provider not in configs:
        raise ValueError(
            f"Invalid LLM provider: '{provider}'. "
            f"Choose from: {', '.join(configs.keys())}"
        )

    config = configs[provider]

    requires_key = {
        "groq", "openai", "anthropic", "huggingface", "mistral", "gemini", "nvidia", "minimax",
        "cohere", "together", "openrouter", "deepseek", "perplexity"
    }
    if provider in requires_key and not config.get("api_key"):
        raise ValueError(
            f"{provider.upper()}_API_KEY is not set. "
            "Enter your API key in the sidebar and click Test Connection."
        )

    if provider in ("nvidia", "minimax") and config.get("api_key"):
        _sync_nvidia_env(config["api_key"])

    return config


def get_llm_params() -> dict:
    """Return keyword args safe to pass directly to crewai.LLM(**...)."""
    from config.context import current_llm_model
    config = get_llm_config()
    model = current_llm_model.get() or os.getenv("LLM_MODEL") or config["model"]

    params: dict = {
        "model":       model,
        "temperature": config.get("temperature", 0.1),
        "max_retries": 5,
    }

    if config.get("api_key"):
        params["api_key"] = config["api_key"]

    if config.get("base_url"):
        params["base_url"] = config["base_url"]

    return {k: v for k, v in params.items() if k in _LLM_VALID_KEYS}


def apply_runtime_llm_settings(
    provider: str,
    model: str,
    api_key: str = "",
    env_key_name: str = "",
) -> None:
    """Inject provider/model/key into context variables and fallback env before agent execution."""
    from config.context import current_llm_provider, current_llm_model, current_llm_api_key, current_llm_env_key_name
    current_llm_provider.set(provider)
    current_llm_model.set(model)
    current_llm_api_key.set(api_key)
    current_llm_env_key_name.set(env_key_name)

    os.environ["LLM_PROVIDER"] = provider
    os.environ["LLM_MODEL"] = model

    if not api_key:
        return

    key_name = env_key_name or f"{provider.upper()}_API_KEY"
    if provider == "ollama":
        os.environ["OLLAMA_BASE_URL"] = api_key
    elif provider in ("nvidia", "minimax"):
        _sync_nvidia_env(api_key)
    else:
        os.environ[key_name] = api_key


def validate_llm_connection(provider: str, model: str, api_key: str = "") -> dict:
    """
    Ping the configured LLM with a minimal prompt.
    Returns {"valid": bool, "message": str}.
    """
    if provider == "ollama":
        env_key_name = "OLLAMA_BASE_URL"
    elif provider in ("nvidia", "minimax"):
        env_key_name = "NVIDIA_API_KEY"
    else:
        env_key_name = f"{provider.upper()}_API_KEY"

    if provider != "ollama" and not api_key.strip():
        return {
            "valid": False,
            "message": f"Please enter your {provider.upper()} API key.",
        }

    apply_runtime_llm_settings(provider, model, api_key.strip(), env_key_name)

    # Fast path for NVIDIA: direct HTTP avoids spinning up full CrewAI stack
    if provider in ("nvidia", "minimax"):
        try:
            response = requests.post(
                f"{NVIDIA_NIM_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key.strip()}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model.replace("nvidia_nim/", "") if model.startswith("nvidia_nim/") else model,
                    "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
                    "max_tokens": 8,
                    "temperature": 0.1,
                },
                timeout=30,
            )
            if response.status_code == 401:
                return {"valid": False, "message": "Invalid NVIDIA API key (401 Unauthorized)."}
            if response.status_code == 404:
                return {
                    "valid": False,
                    "message": (
                        f"Model not found on NVIDIA NIM: {model}. "
                        "Try another model from the dropdown."
                    ),
                }
            response.raise_for_status()
            data = response.json()
            preview = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "OK")
            )
            return {
                "valid": True,
                "message": "NVIDIA NIM connection successful.",
                "preview": str(preview)[:120],
            }
        except requests.RequestException as exc:
            detail = str(exc)
            if hasattr(exc, "response") and exc.response is not None:
                try:
                    detail = exc.response.json().get("detail", detail)
                except Exception:
                    detail = exc.response.text[:200] or detail
            return {"valid": False, "message": f"NVIDIA API error: {detail}"}

    try:
        from crewai import LLM

        llm = LLM(**get_llm_params())
        result = llm.call([{"role": "user", "content": "Reply with exactly: OK"}])
        preview = result if isinstance(result, str) else str(result)
        return {
            "valid": True,
            "message": f"{provider.upper()} connection successful.",
            "preview": preview[:120],
        }
    except Exception as exc:
        return {"valid": False, "message": str(exc)}


def call_minimax_m3(messages: list, stream: bool = False, **kwargs) -> dict:
    """
    Direct HTTP client for MiniMax-M3 via NVIDIA NIM.
    """
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY environment variable is not set.")

    invoke_url = f"{NVIDIA_NIM_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream" if stream else "application/json",
    }
    payload = {
        "model":       "minimaxai/minimax-m3",
        "messages":    messages,
        "max_tokens":  kwargs.get("max_tokens", 8192),
        "temperature": kwargs.get("temperature", 1.00),
        "top_p":       kwargs.get("top_p", 0.95),
        "stream":      stream,
    }

    response = requests.post(invoke_url, headers=headers, json=payload, stream=stream, timeout=60)
    response.raise_for_status()

    if stream:
        return response
    return response.json()
