# LLM Configuration Guide

This directory contains centralized LLM configuration for the CrewAI Data Analyst application.

## Quick Start

### 1. Choose Your LLM Provider

Set the `LLM_PROVIDER` environment variable (in Replit Secrets or `.env` file):

```bash
LLM_PROVIDER=groq  # Options: groq, openai, ollama, anthropic
```

### 2. Add Your API Key

Add the corresponding API key to Replit Secrets:

| Provider | API Key Variable | Get Key From |
|----------|-----------------|--------------|
| Groq (Default) | `GROQ_API_KEY` | https://console.groq.com/keys |
| OpenAI | `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| Anthropic | `ANTHROPIC_API_KEY` | https://console.anthropic.com/ |
| Ollama | `OLLAMA_BASE_URL` | http://localhost:11434 (local) |

### 3. Restart the Application

After changing providers, restart the workflow to apply changes.

## Supported Providers

### 🚀 Groq (Recommended)
- **Model**: llama-3.3-70b-versatile
- **Speed**: Very fast
- **Cost**: Low
- **Best for**: Production use, fast responses

```bash
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
```

### 🤖 OpenAI
- **Model**: gpt-4o-mini
- **Speed**: Fast
- **Cost**: Medium
- **Best for**: High-quality responses

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

### 🏠 Ollama (Local)
- **Model**: llama3
- **Speed**: Depends on hardware
- **Cost**: Free (runs locally)
- **Best for**: Privacy, offline use

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

### 🧠 Anthropic Claude
- **Model**: claude-3-5-sonnet-20241022
- **Speed**: Fast
- **Cost**: Medium
- **Best for**: Complex reasoning tasks

```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

## How It Works

The `llm_config.py` file provides a centralized configuration system that:

1. **Reads environment variables** to determine which LLM provider to use
2. **Validates credentials** before initializing agents
3. **Returns standardized config** that works with all CrewAI agents
4. **Allows easy switching** between providers without code changes

### Code Example

All agents automatically use the centralized config:

```python
from crewai import Agent, LLM
from config.llm_config import get_llm_params

my_agent = Agent(
    name="My Agent",
    role="My Role",
    llm=LLM(**get_llm_params()),  # Automatically uses configured provider
    verbose=True
)
```

## Customizing Models

To use a different model for a specific provider, edit `config/llm_config.py`:

```python
GROQ_CONFIG = {
    "model": "groq/llama-3.1-8b-instant",  # Change this
    "api_key": os.getenv("GROQ_API_KEY"),
}
```

## Troubleshooting

### Error: "Invalid LLM provider"
- Check that `LLM_PROVIDER` is set to one of: groq, openai, ollama, anthropic

### Error: "API_KEY environment variable is not set"
- Make sure you've added the API key to Replit Secrets
- Restart the workflow after adding secrets

### Error: "Connection refused" (Ollama)
- Make sure Ollama is running locally
- Check that `OLLAMA_BASE_URL` points to the correct address

## Security Notes

- **Never commit API keys** to version control
- Always use Replit Secrets or environment variables
- The `.env.example` file is safe to commit (contains no real keys)
