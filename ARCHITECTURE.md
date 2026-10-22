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
├── agents/                     # 25 Agentic Data Intelligence System
│   ├── base_agent.py           # Standardized 6-Step Agent Lifecycle Contract
│   ├── registry.py             # Master 25-Agent Catalog, Presets, and Dynamic Factories
│   ├── data_analysis/          # 📊 Domain 1: Hygiene, Descriptive Stats, Trends, Cohorts, Insights
│   ├── business_analysis/      # 💼 Domain 2: Sales Pareto, Profitability, Expenses, Customers, Decisions
│   ├── data_mining/            # ⛏️ Domain 3: Pattern Clustering, Correlations, Segmentation, Anomaly Detection
│   ├── predictive_analysis/    # 🔮 Domain 4: Sales Forecast, Budget Burn, Demand Buffers, Risk Auto-ML
│   └── eda/                    # 🔭 Domain 5: Schema Discovery, NL Query, Decoupled Visuals, Quality, Storytelling
├── config/                     # Platform configuration
│   ├── llm_config.py           # Multi-Provider settings and model catalog
│   └── __init__.py
├── tools/                      # Deterministic Python Analytical Engines (zero LLM hallucination)
│   ├── stats_tools.py          # SciPy descriptive distributions, IQR, Mann-Kendall trends
│   ├── business_tools.py       # Pareto 80/20, contribution margin, expense spike detection
│   ├── mining_tools.py         # KMeans clustering, Pearson correlation, Isolation Forest
│   ├── predictive_tools.py     # Holt-Winters exponential smoothing, Random Forest regressors
│   ├── eda_tools.py            # Glassmorphic Plotly builders, schema analysis, data health scores
│   └── dataset_tools.py        # Robust CSV ingestion, subprocess sandbox runner
├── ui/                         # Document export services
│   └── export.py               # C-Suite Executive PDF Builder & 25-Agent Multi-Domain Report
├── workflows/                  # Dynamic Multi-Agent Orchestration
│   ├── context_bus.py          # Real-time event streaming and shared blackboard bus
│   ├── coordinator.py          # MasterCoordinator (staged execution, error containment)
│   └── pipeline.py             # Make pipeline orchestration (adaptive cooldown)
├── api/                        # Modular FastAPI Backend Layer
│   ├── dependencies.py         # Session security, paths, LLM loader, and locks
│   ├── notifications.py        # Outbound automated Email, Slack, Discord, Webhook dispatchers
│   └── routers/                # Decoupled APIRouter endpoints
│       ├── analysis.py         # /api/analyze, /api/analyze/stream, /api/upload, /api/clean
│       ├── projects.py         # /api/projects CRUD, /api/preview, ZIP import/export
│       ├── chat.py             # /api/copilot, /api/copilot/stream, /api/chat-history
│       ├── export.py           # /api/export-pdf, /api/export-notebook, /api/share/*
│       └── config.py           # /api/config, /api/llm/providers, /api/validate-key, /api/metrics
├── web/                        # Web Frontend (Zero Build Step Native ES6 Modules)
│   ├── index.html              # Glassmorphic Workspace structure & 5-Step Command Center
│   ├── style.css               # Dark Obsidian & Electric Neon Theme styles
│   ├── app.js                  # Backward-compatibility loader
│   └── js/                     # Decoupled ES6 Frontend Modules
│       ├── main.js             # Application bootstrap & lifecycle coordinator (< 180 lines)
│       ├── state.js            # Reactive state store & model catalogue
│       ├── api.js              # Unified fetch client & SSE stream handler
│       ├── command_center.js   # 25-Agent 5-Step Command Center & preset synchronizer
│       ├── dashboard.js        # Tab switching, summary metrics & interactive preview table
│       ├── charts.js           # Plotly interactive renderer & hidden-tab ResizeObserver
│       ├── chat.js             # AI Copilot conversational UI & slash commands
│       └── export_ui.js        # Executive PDF, CSV, ZIP, and Notebook export triggers
├── data/                       # Dynamic project sessions
│   └── sessions/               # Concurrency-isolated session directories
│       └── <session_id>/
│           ├── original_upload.csv
│           ├── cleaned.csv
│           └── metadata.json
├── outputs/                    # Sandbox generated PNG charts
│   └── <session_id>/
├── assets/                     # Static icons and complete_workflow.svg
├── bin/                        # CLI and NPM binaries
├── package.json                # Node package configuration
├── requirements.txt            # Python package catalog
└── main.py                     # Master FastAPI application orchestrator (< 160 lines)
```
