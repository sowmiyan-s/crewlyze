import contextvars

# Thread-safe request-scoped context variables
current_session_id = contextvars.ContextVar("current_session_id", default="")
current_session_csv = contextvars.ContextVar("current_session_csv", default="")
current_session_output_dir = contextvars.ContextVar("current_session_output_dir", default="")

# Thread-safe LLM credentials context
current_llm_provider = contextvars.ContextVar("current_llm_provider", default="")
current_llm_model = contextvars.ContextVar("current_llm_model", default="")
current_llm_api_key = contextvars.ContextVar("current_llm_api_key", default="")
current_llm_env_key_name = contextvars.ContextVar("current_llm_env_key_name", default="")

# Analysis execution parameters context
current_cooldown = contextvars.ContextVar("current_cooldown", default=5)
current_deep_analysis = contextvars.ContextVar("current_deep_analysis", default=False)
