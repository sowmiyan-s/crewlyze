import os
import sys
import re
import json
import time
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Form

from api.dependencies import (
    DATA_DIR,
    CURRENT_APP_VERSION,
    get_local_config_path,
    config_lock,
    parse_bool,
    load_crew_modules,
)

router = APIRouter()

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

@router.post("/api/validate-key")
async def validate_api_key(
    provider: str = Form(...),
    model: str = Form(...),
    api_key: Optional[str] = Form(""),
):
    """Validate LLM provider credentials before starting analysis."""
    modules = load_crew_modules()
    _validate_llm_connection = modules["validate_llm_connection"]
    if not _validate_llm_connection:
        raise HTTPException(status_code=503, detail="LLM configuration service unavailable.")
    result = _validate_llm_connection(provider, model, api_key or "")
    if not result.get("valid"):
        raise HTTPException(status_code=400, detail=result.get("message", "Validation failed."))
    return result

# ---------------------------------------------------------------------------
# Metrics & Configurations APIs
# ---------------------------------------------------------------------------

@router.get("/api/metrics")
async def get_performance_metrics():
    from config.metrics_tracker import get_metrics
    return get_metrics()

@router.get("/api/config")
async def get_local_config():
    async with config_lock:
        cfg_path = get_local_config_path()
        cfg = {}
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except Exception:
                pass
        
        if "CREWLYZE_DATA_DIR" not in cfg:
            cfg["CREWLYZE_DATA_DIR"] = str(DATA_DIR)
        if "LOG_LEVEL" not in cfg:
            cfg["LOG_LEVEL"] = os.getenv("LOG_LEVEL", "INFO")
        
        return cfg

@router.post("/api/config")
async def save_local_config(
    request: Request,
    provider: Optional[str] = Form(None),
    api_key: Optional[str] = Form(""),
    base_url: Optional[str] = Form("")
):
    async with config_lock:
        cfg_path = get_local_config_path()
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg = {}
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except Exception:
                pass
        
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                payload = await request.json()
                if isinstance(payload, dict):
                    for k, v in payload.items():
                        if v is not None:
                            cfg[k] = v
                        else:
                            cfg.pop(k, None)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {e}")
        else:
            if not provider:
                raise HTTPException(status_code=400, detail="Missing 'provider' form parameter.")
            
            if provider == "ollama":
                key_name = "OLLAMA_BASE_URL"
                cfg[key_name] = base_url.strip()
            elif provider in ("nvidia", "minimax"):
                key_name = "NVIDIA_API_KEY"
            else:
                key_name = f"{provider.upper()}_API_KEY"

            if provider != "ollama":
                if api_key.strip():
                    if not api_key.endswith("..."):
                        cfg[key_name] = api_key.strip()
                        if provider == "gemini":
                            cfg["GOOGLE_API_KEY"] = api_key.strip()
                        elif provider in ("nvidia", "minimax"):
                            cfg["NVIDIA_NIM_API_KEY"] = api_key.strip()
                else:
                    cfg.pop(key_name, None)
                    if provider == "gemini":
                        cfg.pop("GOOGLE_API_KEY", None)
                    elif provider in ("nvidia", "minimax"):
                        cfg.pop("NVIDIA_NIM_API_KEY", None)
                    
            if base_url.strip() and provider == "custom":
                cfg["CUSTOM_BASE_URL"] = base_url.strip()
            
        try:
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
            for k, v in cfg.items():
                os.environ[k] = str(v)
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to write config: {e}")
        return {"status": "success"}

@router.post("/api/config/automation")
async def save_automation_config(
    automation_email_enabled: Optional[str] = Form("false"),
    smtp_host: Optional[str] = Form(""),
    smtp_port: Optional[str] = Form(""),
    smtp_user: Optional[str] = Form(""),
    smtp_password: Optional[str] = Form(""),
    smtp_sender: Optional[str] = Form(""),
    smtp_recipient: Optional[str] = Form(""),
    smtp_secure: Optional[str] = Form("true"),
    automation_slack_enabled: Optional[str] = Form("false"),
    slack_webhook_url: Optional[str] = Form(""),
    slack_send_summary: Optional[str] = Form("true"),
    automation_discord_enabled: Optional[str] = Form("false"),
    discord_webhook_url: Optional[str] = Form(""),
    discord_username: Optional[str] = Form(""),
    discord_avatar_url: Optional[str] = Form(""),
    discord_embed_color: Optional[str] = Form(""),
    discord_mention_role: Optional[str] = Form(""),
    discord_toggle_stats: Optional[str] = Form("true"),
    discord_toggle_warnings: Optional[str] = Form("true"),
    discord_send_summary: Optional[str] = Form("true"),
    discord_attach_pdf: Optional[str] = Form("true"),
    discord_attach_charts: Optional[str] = Form("false"),
    discord_separate_channels: Optional[str] = Form("false"),
    discord_cleaning_url: Optional[str] = Form(""),
    discord_cleaning_enabled: Optional[str] = Form("false"),
    discord_relations_url: Optional[str] = Form(""),
    discord_relations_enabled: Optional[str] = Form("false"),
    discord_insights_url: Optional[str] = Form(""),
    discord_insights_enabled: Optional[str] = Form("false"),
    discord_visualization_url: Optional[str] = Form(""),
    discord_visualization_enabled: Optional[str] = Form("false"),
    automation_webhook_enabled: Optional[str] = Form("false"),
    outbound_webhook_url: Optional[str] = Form(""),
    webhook_send_json: Optional[str] = Form("true"),
    webhook_attach_pdf: Optional[str] = Form("true")
):
    async with config_lock:
        cfg_path = get_local_config_path()
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg = {}
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except Exception:
                pass
                
        cfg["AUTOMATION_EMAIL_ENABLED"] = parse_bool(automation_email_enabled)
        cfg["SMTP_HOST"] = smtp_host.strip() if smtp_host else ""
        cfg["SMTP_PORT"] = int(smtp_port) if smtp_port and smtp_port.strip().isdigit() else 587
        cfg["SMTP_USER"] = smtp_user.strip() if smtp_user else ""
        
        if smtp_password and smtp_password != "********" and not smtp_password.endswith("..."):
            cfg["SMTP_PASSWORD"] = smtp_password.strip()
        elif not smtp_password:
            cfg["SMTP_PASSWORD"] = ""
            
        cfg["SMTP_SENDER"] = smtp_sender.strip() if smtp_sender else ""
        cfg["SMTP_RECIPIENT"] = smtp_recipient.strip() if smtp_recipient else ""
        cfg["SMTP_SECURE"] = parse_bool(smtp_secure)
        
        cfg["AUTOMATION_SLACK_ENABLED"] = parse_bool(automation_slack_enabled)
        cfg["SLACK_WEBHOOK_URL"] = slack_webhook_url.strip() if slack_webhook_url else ""
        cfg["SLACK_SEND_SUMMARY"] = parse_bool(slack_send_summary)

        cfg["AUTOMATION_DISCORD_ENABLED"] = parse_bool(automation_discord_enabled)
        cfg["DISCORD_WEBHOOK_URL"] = discord_webhook_url.strip() if discord_webhook_url else ""
        cfg["DISCORD_USERNAME"] = discord_username.strip() if discord_username else ""
        cfg["DISCORD_AVATAR_URL"] = discord_avatar_url.strip() if discord_avatar_url else ""
        cfg["DISCORD_EMBED_COLOR"] = discord_embed_color.strip() if discord_embed_color else "#5865F2"
        cfg["DISCORD_MENTION_ROLE"] = discord_mention_role.strip() if discord_mention_role else ""
        cfg["DISCORD_TOGGLE_STATS"] = parse_bool(discord_toggle_stats)
        cfg["DISCORD_TOGGLE_WARNINGS"] = parse_bool(discord_toggle_warnings)
        cfg["DISCORD_SEND_SUMMARY"] = parse_bool(discord_send_summary)
        cfg["DISCORD_ATTACH_PDF"] = parse_bool(discord_attach_pdf)
        cfg["DISCORD_ATTACH_CHARTS"] = parse_bool(discord_attach_charts)
        
        cfg["DISCORD_SEPARATE_CHANNELS"] = parse_bool(discord_separate_channels)
        cfg["DISCORD_CLEANING_URL"] = discord_cleaning_url.strip() if discord_cleaning_url else ""
        cfg["DISCORD_CLEANING_ENABLED"] = parse_bool(discord_cleaning_enabled)
        cfg["DISCORD_RELATIONS_URL"] = discord_relations_url.strip() if discord_relations_url else ""
        cfg["DISCORD_RELATIONS_ENABLED"] = parse_bool(discord_relations_enabled)
        cfg["DISCORD_INSIGHTS_URL"] = discord_insights_url.strip() if discord_insights_url else ""
        cfg["DISCORD_INSIGHTS_ENABLED"] = parse_bool(discord_insights_enabled)
        cfg["DISCORD_VISUALIZATION_URL"] = discord_visualization_url.strip() if discord_visualization_url else ""
        cfg["DISCORD_VISUALIZATION_ENABLED"] = parse_bool(discord_visualization_enabled)
        
        cfg["AUTOMATION_WEBHOOK_ENABLED"] = parse_bool(automation_webhook_enabled)
        cfg["OUTBOUND_WEBHOOK_URL"] = outbound_webhook_url.strip() if outbound_webhook_url else ""
        cfg["WEBHOOK_SEND_JSON"] = parse_bool(webhook_send_json)
        cfg["WEBHOOK_ATTACH_PDF"] = parse_bool(webhook_attach_pdf)
        
        try:
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
            for k, v in cfg.items():
                os.environ[k] = str(v)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to write config: {e}")
        return {"status": "success"}

# ---------------------------------------------------------------------------
# LLM Providers & Models
# ---------------------------------------------------------------------------

_CACHED_PROVIDERS = None
_CACHED_MODEL_COST = None

@router.get("/api/llm/providers")
async def get_llm_providers():
    global _CACHED_PROVIDERS
    if _CACHED_PROVIDERS is not None:
        return {"providers": _CACHED_PROVIDERS}

    try:
        import litellm

        model_cost = getattr(litellm, "model_cost", {})
        if not model_cost:
            try:
                backup_path = os.path.join(os.path.dirname(litellm.__file__), "model_prices_and_context_window_backup.json")
                with open(backup_path, "r", encoding="utf-8") as f:
                    model_cost = json.load(f)
            except Exception:
                pass

        providers = set()
        for model_name, info in model_cost.items():
            if not isinstance(info, dict):
                continue
            prov = info.get("litellm_provider")
            if prov:
                providers.add(str(prov).lower())
            if "/" in model_name:
                prefix = model_name.split("/")[0].lower()
                if prefix and prefix not in ("1024-x-1024", "256-x-256", "512-x-512"):
                    providers.add(prefix)

        def clean_provider_name(p: str) -> bool:
            p = p.lower().strip()
            if not p:
                return False
            if any(x in p for x in ("http", "docs.litellm", " ", "/", "cost", "token", "image", "audio", "video", "speech", "tts", "embed", "pixel")):
                return False
            if "-" in p:
                parts = p.split("-")
                if all(part.isdigit() for part in parts if part):
                    return False
                if any(part.isdigit() for part in parts):
                    if any(x in parts for x in ("x", "w", "h")):
                        return False
            if p in ("hd", "high", "low", "medium", "standard", "v0", "sample_spec", "fallback_generalizations", "max-x-max"):
                return False
            return True

        clean_providers = sorted(list(set(p for p in providers if clean_provider_name(p))))
        
        standard_fallbacks = ["openai", "anthropic", "nvidia", "groq", "gemini", "ollama", "cohere", "mistral", "vertex_ai", "bedrock", "openrouter", "deepinfra", "together_ai", "xai"]
        for sf in standard_fallbacks:
            if sf not in clean_providers:
                clean_providers.append(sf)

        _CACHED_PROVIDERS = sorted(clean_providers)
        return {"providers": _CACHED_PROVIDERS}
    except Exception as e:
        fallback_list = ["openai", "anthropic", "nvidia", "groq", "gemini", "ollama", "cohere", "mistral", "vertex_ai", "bedrock", "openrouter", "deepinfra", "together_ai", "xai"]
        _CACHED_PROVIDERS = fallback_list
        return {"providers": fallback_list, "error": str(e)}

def _is_text_generation_model(model_name: str, info: Optional[dict] = None) -> bool:
    low_name = model_name.lower()
    _EXCLUDE_SUBSTRINGS = (
        "embed", "ada-002", "dall-e", "stable-diffusion", "diffusion", "imagen", "image-generation",
        "tts", "whisper", "audio", "speech", "realtime", "moderation", "content-filter",
        "shield", "guard", "rerank", "clip", "vit", "siglip", "transcription", "translation",
        "vector_store", "search-", "encoder", "ocr", "video_generation", "image_edit",
        "deplot", "starcoder", "codeclippy", "fuyu", "neva", "kosmos", "paligemma", "nvaie", "canvas"
    )
    if any(sub in low_name for sub in _EXCLUDE_SUBSTRINGS):
        return False
        
    if info:
        non_text_keys = (
            "input_cost_per_image", "output_cost_per_image",
            "input_cost_per_audio_per_second", "input_cost_per_audio_token", "output_cost_per_audio_token",
            "ocr_cost_per_page", "annotation_cost_per_page", "input_cost_per_pixel", "output_cost_per_pixel",
            "input_cost_per_video_per_second", "output_cost_per_video_per_second"
        )
        if any(k in info for k in non_text_keys):
            return False
            
        mode = info.get("mode")
        if mode not in ("chat", "completion", None):
            return False
            
    return True

@router.get("/api/ollama-models")
async def list_ollama_models(base_url: str = "http://localhost:11434"):
    """Fetches list of local Ollama models from the local Ollama service tags API."""
    import requests
    try:
        url = base_url.rstrip("/") + "/api/tags"
        response = requests.get(url, timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            if models:
                prefixed = [f"ollama/{m}" if not m.startswith("ollama/") else m for m in models]
                return {"models": prefixed}
    except Exception:
        pass
    return {"models": ["ollama/llama3", "ollama/mistral", "ollama/gemma2"]}

@router.get("/api/llm/providers/{provider}/models")
async def get_llm_models(provider: str, api_key: Optional[str] = None):
    """Returns only text-to-text (chat/completion) models for a provider."""
    if not api_key or not api_key.strip() or api_key.endswith("..."):
        cfg_path = get_local_config_path()
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if provider == "ollama":
                        api_key = cfg.get("OLLAMA_BASE_URL", "")
                    elif provider in ("nvidia", "minimax"):
                        api_key = cfg.get("NVIDIA_API_KEY", "")
                    else:
                        api_key = cfg.get(f"{provider.upper()}_API_KEY", "")
            except Exception:
                pass

    models = []
    fetched_successfully = False

    if api_key and api_key.strip() and not api_key.endswith("..."):
        import requests
        clean_key = api_key.strip()
        try:
            if provider == "nvidia":
                res = requests.get(
                    "https://integrate.api.nvidia.com/v1/models",
                    headers={"Authorization": f"Bearer {clean_key}"},
                    timeout=4
                )
                if res.status_code == 200:
                    models = [f"nvidia_nim/{m['id']}" for m in res.json().get("data", [])]
                    fetched_successfully = True
            elif provider == "groq":
                res = requests.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {clean_key}"},
                    timeout=4
                )
                if res.status_code == 200:
                    models = [f"groq/{m['id']}" for m in res.json().get("data", [])]
                    fetched_successfully = True
            elif provider == "openai":
                res = requests.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {clean_key}"},
                    timeout=4
                )
                if res.status_code == 200:
                    models = [m['id'] for m in res.json().get("data", [])]
                    fetched_successfully = True
            elif provider == "ollama":
                base_url = clean_key if clean_key.startswith("http") else os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                res = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=3)
                if res.status_code == 200:
                    tags = res.json().get("models", [])
                    raw_names = [m.get("name") for m in tags if m.get("name")]
                    models = [f"ollama/{name}" if not name.startswith("ollama/") else name for name in raw_names]
                    fetched_successfully = True
        except Exception:
            pass

    if provider == "ollama" and not fetched_successfully:
        try:
            import requests
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            res = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=3)
            if res.status_code == 200:
                tags = res.json().get("models", [])
                raw_names = [m.get("name") for m in tags if m.get("name")]
                if raw_names:
                    models = [f"ollama/{name}" if not name.startswith("ollama/") else name for name in raw_names]
                    fetched_successfully = True
        except Exception:
            pass

    global _CACHED_MODEL_COST
    if _CACHED_MODEL_COST is None:
        try:
            import litellm
            _CACHED_MODEL_COST = getattr(litellm, "model_cost", {})
            if not _CACHED_MODEL_COST:
                backup_path = os.path.join(os.path.dirname(litellm.__file__), "model_prices_and_context_window_backup.json")
                with open(backup_path, "r", encoding="utf-8") as f:
                    _CACHED_MODEL_COST = json.load(f)
        except Exception:
            _CACHED_MODEL_COST = {}

    model_cost = _CACHED_MODEL_COST
    provider_models = []
    
    if fetched_successfully and models:
        for model in models:
            info = model_cost.get(model)
            if _is_text_generation_model(model, info):
                provider_models.append(model)
    else:
        for model_name, info in model_cost.items():
            if not isinstance(info, dict):
                continue
            prov = info.get("litellm_provider", "")
            prov_lower = prov.lower() if prov else ""
            req_prov_lower = provider.lower()
            
            is_match = False
            if prov_lower == req_prov_lower:
                is_match = True
            elif req_prov_lower == "nvidia" and prov_lower == "nvidia_nim":
                is_match = True
            elif req_prov_lower == "cohere" and prov_lower == "cohere_chat":
                is_match = True
            elif req_prov_lower == "bedrock" and prov_lower in ("bedrock_converse", "bedrock_mantle"):
                is_match = True
            elif model_name.startswith(f"{provider}/"):
                is_match = True
            elif provider.lower() == "openai" and "gpt-" in model_name and "/" not in model_name:
                is_match = True

            if is_match:
                if _is_text_generation_model(model_name, info):
                    provider_models.append(model_name)

        try:
            import litellm
            if hasattr(litellm, "model_list"):
                extra = [m for m in litellm.model_list if m.startswith(f"{provider}/")]
                if provider == "openai":
                    extra.extend([m for m in litellm.model_list if "gpt-" in m and "/" not in m])
                for m in extra:
                    info = model_cost.get(m)
                    if _is_text_generation_model(m, info):
                        provider_models.append(m)
        except Exception:
            pass

    unique_models = list(set(provider_models))
    
    def _model_priority(model_name: str) -> tuple:
        low = model_name.lower()
        featured_keywords = [
            "llama-3.3-70b", "llama-3.1-8b", "llama-3.1-70b", "nemotron-70b",
            "llama-3.1", "llama-3.2", "llama-3.3", "deepseek-r1", "deepseek-chat",
            "mistral-large", "mistral-small", "gemma-2-27b", "gemma-2-9b",
            "qwen2.5-72b", "qwen2-7b", "gpt-4o", "claude-3-5-sonnet",
            "gemini-1.5-flash", "gemini-1.5-pro", "command-r"
        ]
        for idx, kw in enumerate(featured_keywords):
            if kw in low:
                return (0, idx, low)
        return (1, 0, low)

    provider_models = sorted(unique_models, key=_model_priority)
    return {"models": provider_models}

# ---------------------------------------------------------------------------
# System Version & Updates
# ---------------------------------------------------------------------------

@router.get("/api/system/version")
async def get_system_version():
    """Returns local version and checks for updates against GitHub Releases."""
    import urllib.request
    
    current_ver = CURRENT_APP_VERSION
    data = {
        "current_version": current_ver,
        "latest_version": current_ver,
        "release_name": f"v{current_ver}",
        "update_available": False,
        "release_url": "https://github.com/sowmiyan-s/crewlyze/releases",
        "release_notes": "",
        "download_url": "",
        "checked_at": time.time()
    }
    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/sowmiyan-s/crewlyze/releases/latest",
            headers={"User-Agent": "Crewlyze-App", "Accept": "application/vnd.github.v3+json"}
        )
        with urllib.request.urlopen(req, timeout=4) as resp:
            if resp.status == 200:
                rel = json.loads(resp.read().decode("utf-8"))
                tag = str(rel.get("tag_name", "")).lstrip("v").strip()
                if tag:
                    data["latest_version"] = tag
                    data["release_name"] = rel.get("name") or f"Release v{tag}"
                    data["release_url"] = rel.get("html_url", data["release_url"])
                    data["release_notes"] = rel.get("body", "")
                    
                    def _parse_v(v_str):
                        parts = [int(re.sub(r'\D', '', x) or 0) for x in str(v_str).split(".")]
                        while len(parts) < 3:
                            parts.append(0)
                        return parts
                    
                    v_curr = _parse_v(current_ver)
                    v_remote = _parse_v(tag)
                    if v_remote > v_curr:
                        data["update_available"] = True
                        for asset in rel.get("assets", []):
                            if str(asset.get("name", "")).endswith(".exe"):
                                data["download_url"] = asset.get("browser_download_url", "")
                                break
    except Exception as e:
        data["error"] = str(e)
        
    return data

@router.post("/api/system/update")
async def trigger_system_update():
    """Triggers background download and installation of the latest release."""
    import subprocess
    base_dir = Path(__file__).resolve().parent.parent.parent
    updater_ps1 = base_dir / "installer" / "updater.ps1"
    if not updater_ps1.exists():
        updater_ps1 = base_dir / "updater.ps1"
    
    if updater_ps1.exists() and sys.platform == "win32":
        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", str(updater_ps1)
        ]
        flags = subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        subprocess.Popen(cmd, creationflags=flags)
        return {"status": "success", "message": "Crewlyze auto-updater launched in a new terminal window."}
    else:
        return {"status": "redirect", "url": "https://github.com/sowmiyan-s/crewlyze/releases/latest"}

# ---------------------------------------------------------------------------
# Feedback API
# ---------------------------------------------------------------------------

@router.api_route("/api/feedback", methods=["GET", "POST"])
async def handle_feedback(request: Request):
    """Receive a user report/feature/bug, persist it locally, and email it if SMTP is configured."""
    feedback_type = "feedback"
    name = ""
    email = ""
    message = ""

    content_type = request.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                feedback_type = body.get("feedback_type") or body.get("type") or "feedback"
                name = body.get("name") or ""
                email = body.get("email") or ""
                message = body.get("message") or ""
        except Exception:
            pass
    elif "form" in content_type:
        try:
            form = await request.form()
            feedback_type = form.get("feedback_type") or form.get("type") or "feedback"
            name = form.get("name") or ""
            email = form.get("email") or ""
            message = form.get("message") or ""
        except Exception:
            pass

    if not message and request.query_params:
        feedback_type = request.query_params.get("feedback_type") or request.query_params.get("type") or feedback_type
        name = request.query_params.get("name") or name
        email = request.query_params.get("email") or email
        message = request.query_params.get("message") or ""

    feedback_type = (feedback_type or "feedback").strip().lower()
    name = (name or "").strip()
    email = (email or "").strip()
    message = (message or "").strip()

    if request.method == "GET" and not (name or email or message):
        return {
            "status": "active",
            "endpoint": "/api/feedback",
            "supported_methods": ["GET", "POST"],
            "description": "Submit a bug report, feature request, or feedback. Fields: feedback_type, name (required), email (required), message (required).",
        }

    if not name:
        raise HTTPException(status_code=400, detail="Your name is required to submit a report.")

    if not email or "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="A valid email address is required to submit a report.")

    if not message:
        raise HTTPException(status_code=400, detail="Feedback message cannot be empty.")

    submission_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "feedback_type": feedback_type,
        "name": name,
        "email": email,
        "message": message,
    }

    try:
        feedback_file = DATA_DIR / "feedback_submissions.json"
        existing = []
        if feedback_file.exists():
            try:
                with open(feedback_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    if not isinstance(existing, list):
                        existing = []
            except Exception:
                existing = []
        existing.append(submission_entry)
        with open(feedback_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
    except Exception as e:
        print(f"[Feedback] Warning: Could not persist submission locally: {e}")

    RECIPIENT = "contact2boundbycode@gmail.com"
    SENDER = "Crewlyze Feedback <noreply@crewlyze.app>"
    email_sent = False

    type_label = {
        "bug": "🐞 Bug Report",
        "feature": "✨ Feature Request",
        "report": "📝 Report/Issue",
    }.get(feedback_type, "💬 Feedback")

    try:
        import requests
        gateway_url = f"https://formsubmit.co/ajax/{RECIPIENT}"
        gateway_payload = {
            "name": name or "Anonymous User",
            "email": email or "noreply@crewlyze.app",
            "type": type_label,
            "message": message,
            "_subject": f"[Crewlyze Live Report] {type_label} from {name or 'User'}",
            "_template": "table",
            "_captcha": "false",
        }
        gateway_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Crewlyze-Desktop/1.2.4",
            "Origin": "https://crewlyze.app",
            "Referer": "https://crewlyze.app/",
        }
        res_gateway = requests.post(gateway_url, json=gateway_payload, headers=gateway_headers, timeout=10)
        if res_gateway.status_code == 200:
            email_sent = True
    except Exception as gw_err:
        print(f"[Feedback] Web email gateway notice: {gw_err}")

    type_name = "bug report" if feedback_type == "bug" else "report" if feedback_type == "report" else "feature request" if feedback_type == "feature" else "feedback"
    return {
        "status": "success",
        "message": f"Thank you! Your {type_name} was sent directly to our team inbox.",
        "id": submission_entry["id"]
    }
