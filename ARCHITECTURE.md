# Crewlyze Architecture

## System Architecture
Crewlyze uses a lightweight FastAPI backend and a vanilla JavaScript frontend to deliver a premium user experience with real-time SSE (Server-Sent Events) communication.

## ⚙️ Provider Gateway Support
The system integrates a custom gateway supporting **13+ LLM providers** through local configuration or environment variables:
- **Cloud Gateways**: OpenAI, Anthropic, Google Gemini, NVIDIA NIM, Groq, Mistral, TogetherAI, Cohere, OpenRouter, DeepSeek, Perplexity, HuggingFace.
- **Local Sandbox**: Ollama (auto-detects local models via the Ollama catalog).

## 📂 Project Structure

```
.
├── agents/               # CrewAI Agent factories
│   ├── insights.py       # 💡 Chief Growth Strategist & Executive BI Advisor
│   ├── relation.py       # 🔗 Growth Opportunity & Revenue Driver Analyst
│   ├── visualizer.py     # 📈 Executive BI Visualizer Agent
│   ├── trend.py          # 🚀 Business Velocity & Growth Analyst
│   ├── predictive.py     # 🤖 Predictive Growth Driver Analyst
│   ├── anomaly.py        # 🛡️ Business Risk & Revenue Leakage Auditor
│   └── cleaner.py        # 🧹 Data Quality Auditor (Optional)
├── config/               # Platform configuration
│   ├── llm_config.py     # Multi-Provider settings and model catalog
│   └── __init__.py
├── tools/                # Orchestration tools
│   └── dataset_tools.py  # read_head, subprocess sandbox runner, plotly builder
├── ui/                   # Document export services
│   └── export.py         # Formatted PDF Cover & Content builder
├── workflows/            # Workflow pipelines
│   └── pipeline.py       # Make pipeline orchestration (adaptive cooldown)
├── web/                  # Web Frontend Assets
│   ├── index.html        # Glassmorphic Workspace structure
│   ├── app.js            # Frontend core logic (SSE logs, Chat, API hooks)
│   └── style.css         # Dark Electric-Violet Theme styles
├── data/                 # Dynamic project sessions
│   └── sessions/         # Concurrency-isolated session directories
│       └── <session_id>/
│           ├── original_upload.csv
│           ├── cleaned.csv
│           └── metadata.json
├── outputs/              # Sandbox generated PNG charts
│   └── <session_id>/
├── assets/               # Static icons and complete_workflow.svg
├── bin/                  # CLI and NPM binaries
├── package.json          # Node package configuration
├── requirements.txt      # Python package catalog
└── main.py               # FastAPI backend routing endpoints
```
