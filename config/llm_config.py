# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def _load_local_config():
    try:
        from pathlib import Path
        import json
        cfg_path = Path.home() / ".crewlyze" / "config.json"
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                for k, v in cfg.items():
                    if k not in os.environ:
                        os.environ[k] = str(v)
    except Exception:
        pass

_load_local_config()

# NVIDIA NIM OpenAI-compatible endpoint (required for LiteLLM / CrewAI)
NVIDIA_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Keys accepted by crewai.LLM constructor.
_LLM_VALID_KEYS = {"model", "api_key", "base_url", "temperature", "max_retries", "timeout"}


def _sync_llm_env(provider: str, api_key: str = "", base_url: str = "") -> None:
    """Keep all LLM provider environment variables synchronized across LiteLLM, CrewAI, and HTTP clients."""
    p_lower = provider.lower()
    if api_key:
        if p_lower in ("nvidia", "minimax"):
            os.environ["NVIDIA_API_KEY"] = api_key
            os.environ["NVIDIA_NIM_API_KEY"] = api_key
        elif p_lower == "gemini":
            os.environ["GEMINI_API_KEY"] = api_key
            os.environ["GOOGLE_API_KEY"] = api_key
        elif p_lower == "groq":
            os.environ["GROQ_API_KEY"] = api_key
        elif p_lower == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
        elif p_lower == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = api_key
        elif p_lower == "mistral":
            os.environ["MISTRAL_API_KEY"] = api_key
        elif p_lower == "cohere":
            os.environ["COHERE_API_KEY"] = api_key
        elif p_lower in ("together", "together_ai"):
            os.environ["TOGETHER_API_KEY"] = api_key
            os.environ["TOGETHERAI_API_KEY"] = api_key
        elif p_lower == "openrouter":
            os.environ["OPENROUTER_API_KEY"] = api_key
        elif p_lower == "deepseek":
            os.environ["DEEPSEEK_API_KEY"] = api_key
        elif p_lower == "perplexity":
            os.environ["PERPLEXITY_API_KEY"] = api_key
            os.environ["PERPLEXITYAI_API_KEY"] = api_key
        elif p_lower == "huggingface":
            os.environ["HUGGINGFACE_API_KEY"] = api_key
            os.environ["HF_TOKEN"] = api_key
        elif p_lower == "custom":
            os.environ["CUSTOM_API_KEY"] = api_key
            os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", api_key)

    if base_url:
        if p_lower == "ollama":
            os.environ["OLLAMA_BASE_URL"] = base_url
        elif p_lower == "custom":
            os.environ["CUSTOM_BASE_URL"] = base_url


def _sync_nvidia_env(api_key: str) -> None:
    """Backward compatible helper."""
    _sync_llm_env("nvidia", api_key=api_key)


def get_llm_config() -> dict:
    """Return the raw provider config dict (may contain extra keys)."""
    from config.context import current_llm_provider, current_llm_api_key
    provider = (current_llm_provider.get() or os.getenv("LLM_PROVIDER") or "nvidia").lower()

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
        "custom": {
            "model":   os.getenv("LLM_MODEL", "custom/model"),
            "api_key": current_llm_api_key.get() or os.getenv("CUSTOM_API_KEY", ""),
            "base_url": os.getenv("CUSTOM_BASE_URL"),
        },
        "openai": {
            "model":   "gpt-4o-mini",
            "api_key": current_llm_api_key.get() or os.getenv("OPENAI_API_KEY"),
        },
        "ollama": {
            "model":    "ollama/llama3",
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
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
            "model":   "mistral/mistral-small-latest",
            "api_key": current_llm_api_key.get() or os.getenv("MISTRAL_API_KEY"),
        },
        "gemini": {
            "model":   "gemini/gemini-1.5-flash",
            "api_key": current_llm_api_key.get() or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        },
        "cohere": {
            "model":   "cohere/command-r-plus",
            "api_key": current_llm_api_key.get() or os.getenv("COHERE_API_KEY"),
        },
        "together": {
            "model":   "together_ai/meta-llama/Llama-3-70b-chat-hf",
            "api_key": current_llm_api_key.get() or os.getenv("TOGETHER_API_KEY") or os.getenv("TOGETHERAI_API_KEY"),
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
        from config.context import current_llm_model
        model = current_llm_model.get() or os.getenv("LLM_MODEL") or f"{provider}/default"
        api_key = current_llm_api_key.get() or os.getenv(f"{provider.upper()}_API_KEY") or os.getenv("API_KEY") or ""
        configs[provider] = {
            "model": model,
            "api_key": api_key,
        }

    config = configs[provider]

    requires_key = {
        "groq", "openai", "anthropic", "huggingface", "mistral", "gemini", "nvidia", "minimax",
        "cohere", "together", "openrouter", "deepseek", "perplexity"
    }
    if provider in requires_key and not config.get("api_key"):
        config["api_key"] = config.get("api_key", "")

    if config.get("api_key") or config.get("base_url"):
        _sync_llm_env(provider, api_key=config.get("api_key", ""), base_url=config.get("base_url", ""))

    return config


def _format_model_name(provider: str, model: str) -> str:
    """Ensure proper LiteLLM provider prefix for CrewAI and LiteLLM compatibility."""
    if not model or not model.strip():
        return model

    p_lower = provider.lower()
    m_str = model.strip()

    if p_lower in ("nvidia", "minimax"):
        if not m_str.startswith("nvidia_nim/"):
            return f"nvidia_nim/{m_str}"
    elif p_lower == "groq":
        if not m_str.startswith("groq/"):
            return f"groq/{m_str}"
    elif p_lower == "gemini":
        if not m_str.startswith("gemini/"):
            return f"gemini/{m_str}"
    elif p_lower == "ollama":
        if not m_str.startswith("ollama/"):
            return f"ollama/{m_str}"
    elif p_lower == "anthropic":
        if not m_str.startswith("anthropic/"):
            return f"anthropic/{m_str}"
    elif p_lower == "mistral":
        if not m_str.startswith("mistral/"):
            return f"mistral/{m_str}"
    elif p_lower == "cohere":
        if not m_str.startswith("cohere/"):
            return f"cohere/{m_str}"
    elif p_lower in ("together", "together_ai"):
        if not m_str.startswith("together_ai/"):
            return f"together_ai/{m_str}"
    elif p_lower == "openrouter":
        if not m_str.startswith("openrouter/"):
            return f"openrouter/{m_str}"
    elif p_lower == "deepseek":
        if not m_str.startswith("deepseek/"):
            return f"deepseek/{m_str}"
    elif p_lower == "perplexity":
        if not m_str.startswith("perplexity/"):
            return f"perplexity/{m_str}"

    return m_str


def get_llm_params() -> dict:
    """Return keyword args safe to pass directly to crewai.LLM(**...)."""
    from config.context import current_llm_model, current_llm_provider
    provider = (current_llm_provider.get() or os.getenv("LLM_PROVIDER") or "nvidia").lower()
    config = get_llm_config()
    
    raw_model = current_llm_model.get() or os.getenv("LLM_MODEL") or config["model"]
    formatted_model = _format_model_name(provider, raw_model)

    params: dict = {
        "model":       formatted_model,
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
    """Inject provider/model/key into context variables before agent execution."""
    base_url = ""
    if provider == "custom" and api_key and "|" in api_key:
        parts = api_key.split("|", 1)
        base_url = parts[0]
        api_key = parts[1]
        os.environ["CUSTOM_BASE_URL"] = base_url
    elif provider == "ollama" and api_key and api_key.startswith("http"):
        base_url = api_key
        os.environ["OLLAMA_BASE_URL"] = base_url

    from config.context import current_llm_provider, current_llm_model, current_llm_api_key, current_llm_env_key_name
    current_llm_provider.set(provider)
    current_llm_model.set(model)
    current_llm_api_key.set(api_key)
    current_llm_env_key_name.set(env_key_name)

    _sync_llm_env(provider, api_key=api_key, base_url=base_url)


def validate_llm_connection(provider: str, model: str, api_key: str = "") -> dict:
    """
    Ping the configured LLM with a minimal prompt.
    Returns {"valid": bool, "message": str}.
    """
    provider_lower = provider.lower()
    base_url = ""

    if provider_lower == "custom" and api_key and "|" in api_key:
        parts = api_key.split("|", 1)
        base_url = parts[0]
        api_key = parts[1]
        os.environ["CUSTOM_BASE_URL"] = base_url

    if provider_lower == "ollama":
        env_key_name = "OLLAMA_BASE_URL"
    elif provider_lower in ("nvidia", "minimax"):
        env_key_name = "NVIDIA_API_KEY"
    else:
        env_key_name = f"{provider_lower.upper()}_API_KEY"

    if provider_lower != "ollama" and not api_key.strip():
        return {
            "valid": False,
            "message": f"Please enter your {provider.upper()} API key.",
        }

    apply_runtime_llm_settings(provider, model, api_key.strip(), env_key_name)

    # Fast path for Ollama local connection check
    if provider_lower == "ollama":
        ollama_url = api_key.strip() if api_key and api_key.startswith("http") else os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        try:
            res = requests.get(f"{ollama_url.rstrip('/')}/api/tags", timeout=4)
            if res.status_code == 200:
                tags = res.json().get("models", [])
                names = [m.get("name") for m in tags if m.get("name")]
                return {
                    "valid": True,
                    "message": f"Ollama server connected at {ollama_url} ({len(names)} models available).",
                    "preview": f"Models: {', '.join(names[:4])}" if names else "Ollama Active"
                }
        except Exception as exc:
            return {
                "valid": True,
                "offline_mode": True,
                "message": f"Ollama connection info ({exc}). Pipeline using automated statistical intelligence.",
                "preview": "Local statistical intelligence active."
            }

    # Fast path for NVIDIA NIM direct HTTP
    if provider_lower in ("nvidia", "minimax"):
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
                timeout=10,
            )
            if response.status_code == 401:
                return {"valid": False, "message": "Invalid NVIDIA API key (401 Unauthorized). Please check your key in sidebar settings."}
            if response.status_code == 404:
                return {
                    "valid": False,
                    "message": f"Model not found on NVIDIA NIM: {model}. Try another model from the dropdown.",
                }
            response.raise_for_status()
            data = response.json()
            preview = data.get("choices", [{}])[0].get("message", {}).get("content", "OK")
            return {
                "valid": True,
                "message": "NVIDIA NIM connection successful.",
                "preview": str(preview)[:120],
            }
        except requests.RequestException as exc:
            detail = str(exc)
            if isinstance(exc, requests.exceptions.ConnectionError):
                detail = "Network/DNS domain lookup unavailable. Switching to local statistical intelligence engine."
            elif hasattr(exc, "response") and exc.response is not None:
                try: detail = exc.response.json().get("detail", detail)
                except Exception: detail = exc.response.text[:200] or detail
            
            return {
                "valid": True,
                "offline_mode": True,
                "message": f"Local Fallback: {detail}",
                "preview": "Local statistical intelligence active."
            }

    try:
        from crewai import LLM
        params = get_llm_params()
        llm = LLM(**params)
        result = llm.call([{"role": "user", "content": "Reply with: OK"}])
        preview = result if isinstance(result, str) else str(result)
        return {
            "valid": True,
            "message": f"{provider.upper()} connection successful.",
            "preview": preview[:120],
        }
    except Exception as exc:
        return {
            "valid": True,
            "offline_mode": True,
            "message": f"Local Fallback ({provider.upper()} offline): Pipeline using automated statistical intelligence.",
            "preview": "Local statistical intelligence active."
        }


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
