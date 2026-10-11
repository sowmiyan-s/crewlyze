import pytest
from config.llm_config import _format_model_name, get_llm_params, _LLM_VALID_KEYS


def test_format_model_name():
    assert _format_model_name("nvidia", "meta/llama-3.1-70b-instruct") == "nvidia_nim/meta/llama-3.1-70b-instruct"
    assert _format_model_name("nvidia", "nvidia_nim/meta/llama-3.1-70b-instruct") == "nvidia_nim/meta/llama-3.1-70b-instruct"
    assert _format_model_name("groq", "llama-3.3-70b-versatile") == "groq/llama-3.3-70b-versatile"
    assert _format_model_name("ollama", "llama3.1") == "ollama/llama3.1"
    assert _format_model_name("gemini", "gemini-1.5-flash") == "gemini/gemini-1.5-flash"


def test_get_llm_params_contract():
    params = get_llm_params()
    assert isinstance(params, dict)
    assert "model" in params
    # Ensure every key is valid for crewai.LLM constructor
    for k in params:
        assert k in _LLM_VALID_KEYS, f"Key '{k}' is not allowed in crewai.LLM params"
