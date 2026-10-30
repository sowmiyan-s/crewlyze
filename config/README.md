# Crewlyze Configuration Guide

Centralized environment and Large Language Model (LLM) configuration for **Crewlyze**.

---

## 🚀 Quick Start

Configure Crewlyze either via the **Interactive Web Settings Modal** (`http://localhost:8000` ➔ ⚙️ **Settings**) or by defining environment variables in `.env` files.

### Configuration Load Priority
`config/env_loader.py` discovers and loads settings hierarchically:
1. `~/.crewlyze/.env` (Global user profile defaults)
2. `<project-root>/.env` (Workspace overrides)
3. Working directory `.env`
4. Active OS Environment Variables

---

## 🔑 Universal LLM Provider Matrix

Crewlyze integrates with **LiteLLM** and **CrewAI**, supporting 13+ cloud and local LLM providers:

| Provider | Environment Key | Default Model | Setup & Notes |
| :--- | :--- | :--- | :--- |
| 🟢 **NVIDIA NIM** (Default) | `NVIDIA_API_KEY` | `nvidia_nim/meta/llama-3.1-70b-instruct` | Fast, enterprise-grade Llama-3.1-70b models via NVIDIA Integrate API. |
| 🦙 **Ollama (100% Offline)** | `OLLAMA_BASE_URL` | `ollama/llama3` | Fully private, air-gapped local execution on `http://localhost:11434`. Zero cloud egress. |
| ⚡ **Groq** | `GROQ_API_KEY` | `groq/llama-3.1-8b-instant` | Ultra-low latency inference for high-speed exploration. |
| 🟢 **OpenAI** | `OPENAI_API_KEY` | `gpt-4o-mini` | Supports `gpt-4o`, `gpt-4o-mini`, and `o1` series. |
| 🟣 **Anthropic** | `ANTHROPIC_API_KEY` | `claude-3-5-sonnet-20241022` | Premier analytical depth and structured reasoning. |
| 🔵 **Google Gemini** | `GEMINI_API_KEY` | `gemini/gemini-1.5-flash` | Long-context multimodal data evaluation. Also accepts `GOOGLE_API_KEY`. |
| 🌊 **DeepSeek** | `DEEPSEEK_API_KEY` | `deepseek/deepseek-chat` | High reasoning efficiency and competitive performance. |
| 🌪️ **Mistral AI** | `MISTRAL_API_KEY` | `mistral/mistral-small-latest` | European cloud inference and code analysis. |
| 🤝 **Together AI** | `TOGETHER_API_KEY` | `together_ai/meta-llama/Llama-3-70b-chat-hf` | High-throughput open-weights hosting. |
| 🌐 **OpenRouter** | `OPENROUTER_API_KEY` | `openrouter/google/gemma-2-9b-it` | Universal gateway to dozens of open-source and proprietary models. |
| 🔎 **Perplexity** | `PERPLEXITY_API_KEY` | `perplexity/llama-3-sonar-large-32k-chat` | Online search-grounded LLM inference. |
| 💬 **Cohere** | `COHERE_API_KEY` | `cohere/command-r-plus` | Enterprise RAG and tabular synthesis. |
| 🤗 **Hugging Face** | `HUGGINGFACE_API_KEY` | `huggingface/HuggingFaceH4/zephyr-7b-beta` | Open model hub inference. Also accepts `HF_TOKEN`. |
| 🛠️ **Custom / vLLM / LM Studio** | `CUSTOM_API_KEY` | User specified via `LLM_MODEL` | Custom OpenAI-compatible endpoints (`CUSTOM_BASE_URL`). |

---

## 📝 Example `.env` Configuration

```env
# ── LLM Provider Selection ───────────────────────────────────────────────────
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=nvapi-your-key-here
LLM_MODEL=nvidia_nim/meta/llama-3.1-70b-instruct

# ── Alternative Cloud Providers (Optional) ───────────────────────────────────
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-...

# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-...

# LLM_PROVIDER=gemini
# GEMINI_API_KEY=AIzaSy...

# LLM_PROVIDER=groq
# GROQ_API_KEY=gsk_...

# ── Air-Gapped Local Ollama (Optional) ────────────────────────────────────────
# LLM_PROVIDER=ollama
# OLLAMA_BASE_URL=http://localhost:11434
# LLM_MODEL=ollama/llama3.1

# ── Outbound Notifications (Optional) ────────────────────────────────────────
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=reports@example.com
SMTP_PASSWORD=your-app-password
SMTP_SENDER=reports@example.com
REPORT_RECIPIENTS=executive@example.com,csuite@example.com

DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

---

## 📬 Outbound Notification Channels

Configure automated report delivery upon pipeline execution completion:
1. **SMTP Email**: Delivers executive summary PDF reports directly to configured recipient distribution lists.
2. **Discord Webhooks**: Dispatches embedded markdown cards with metric summaries, warning badges, and direct PDF attachments to Discord channels.
3. **Slack Webhooks**: Transmits formatted summary cards to Slack channels.
