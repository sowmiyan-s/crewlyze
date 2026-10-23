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
│   ├── artifact_manager.py     # Deterministic Data Artifact Store (downloadable CSV/JSON, traversal safe)
│   ├── stats_tools.py          # SciPy descriptive distributions, IQR, Mann-Kendall trends
│   ├── business_tools.py       # Pareto 80/20, contribution margin, expense spike detection
│   ├── mining_tools.py         # KMeans clustering, Pearson correlation, Isolation Forest
│   ├── predictive_tools.py     # Holt-Winters exponential smoothing, Random Forest regressors
│   ├── eda_tools.py            # Glassmorphic Plotly builders, schema analysis, data health scores
│   └── dataset_tools.py        # Robust CSV ingestion, subprocess sandbox runner
├── ui/                         # Document export services
│   └── export.py               # Single Platypus Engine: Consolidated Executive PDF & 25 Distinct Capability PDFs
├── workflows/                  # Dynamic Multi-Agent Orchestration
│   ├── context_bus.py          # Real-time event streaming and shared blackboard bus
│   ├── coordinator.py          # MasterCoordinator (staged execution, error containment, artifact aggregation)
│   └── pipeline.py             # Make pipeline orchestration (adaptive cooldown)
├── api/                        # Modular FastAPI Backend Layer
│   ├── dependencies.py         # Session security, paths, LLM loader, and locks
│   ├── notifications.py        # Outbound automated Email, Slack, Discord, Webhook dispatchers
│   └── routers/                # Decoupled APIRouter endpoints
│       ├── analysis.py         # /api/analyze, /api/analyze/stream, /api/upload, /api/clean
│       ├── projects.py         # /api/projects CRUD, /api/preview, ZIP import/export
│       ├── chat.py             # /api/copilot, /api/copilot/stream, /api/chat-history
│       ├── export.py           # /api/export-pdf (distinct & consolidated), /api/artifacts/{key}, /api/share/*
│       └── config.py           # /api/config, /api/llm/providers, /api/validate-key, /api/metrics
├── web/                        # Web Frontend (Zero Build Step Native ES6 Modules)
│   ├── index.html              # Glassmorphic Workspace, 5-Domain Crew Cards & Detail Modal
│   ├── style.css               # Obsidian & Crimson (#ff252a) Gradient Theme styles
│   ├── app.js                  # Backward-compatibility loader
│   └── js/                     # Decoupled ES6 Frontend Modules
│       ├── main.js             # Application bootstrap & lifecycle coordinator (< 180 lines)
│       ├── state.js            # Reactive state store & model catalogue
│       ├── api.js              # Unified fetch client & SSE stream handler
│       ├── command_center.js   # 5-Domain Crew Modal, live telemetry & multi-crew selector
│       ├── dashboard.js        # Tab switching, summary metrics, artifact download chips & preview table
│       ├── charts.js           # Plotly interactive renderer & hidden-tab ResizeObserver
│       ├── chat.js             # AI Copilot conversational UI & slash commands
│       └── export_ui.js        # Consolidated & Distinct PDF export triggers
├── data/                       # Dynamic project sessions
│   └── sessions/               # Concurrency-isolated session directories
│       └── <session_id>/
│           ├── original_upload.csv
│           ├── cleaned.csv
│           ├── artifacts/      # Emitted tabular CSV/JSON files (e.g. sales_pareto_breakdown.csv)
│           └── metadata.json
├── outputs/                    # Sandbox generated PNG charts
│   └── <session_id>/
├── assets/                     # Static icons and complete_workflow.svg
├── bin/                        # CLI and NPM binaries
├── package.json                # Node package configuration
├── requirements.txt            # Python package catalog
└── main.py                     # Master FastAPI application orchestrator (< 160 lines)
```

## 🎯 5-Domain Intelligence Framework

Crewlyze structures multi-agent analytics across 5 specialized domains:
1. **Data Analysis Domain**: Data Hygiene & Sanitization (`DataCleanerAgent`), Descriptive Distributions (`StatisticalAnalysisAgent`), Directional Momentum (`TrendAnalysisAgent`), Cohort Benchmarks (`ComparativeAnalysisAgent`), and Ranked Empirical Discoveries (`InsightDiscoveryAgent`).
2. **Business Analysis Domain**: Commercial Pareto 80/20 Concentration (`SalesAnalysisAgent`), Gross & Contribution Margins (`ProfitabilityAnalysisAgent`), Expenditure Spikes & Variance Optimization (`ExpenseOptimizationAgent`), High-Value Cohorts & RFM (`CustomerIntelligenceAgent`), and Prioritized Decision Matrices (`BusinessDecisionSupportAgent`).
3. **Data Mining Domain**: Multivariate Centroids & Clusters (`PatternDiscoveryAgent`), Pearson Cross-Feature Correlation (`RelationshipAnalysisAgent`), Strategic Performance Tiers (`SegmentationAgent`), Isolation Forest Outliers (`AnomalyDetectionAgent`), and Co-occurrence Combinations (`AssociationMiningAgent`).
4. **Predictive Analysis Domain**: Sales Trajectory Forecasting with 90% Confidence Bounds (`SalesForecastingAgent`), Forward Operational Burn Rates (`BudgetForecastingAgent`), Safety Stock & Reorder Points (`DemandForecastingAgent`), Multi-Algorithm Risk & Feature Importances (`RiskPredictionAgent`), and Elasticity Scenario Simulation (`WhatIfSimulationAgent`).
5. **Exploratory Data Analysis (EDA) Domain**: Schema & Column Dictionary Inspection (`DatasetExplorerAgent`), Natural Language Question Answering (`NaturalLanguageDataQueryAgent`), Decoupled Plotly Visuals (`VisualizationAgent`), Objective Data Health Scoring 0-100 (`DataQualityInspectorAgent`), and Boardroom Narrative Reports (`DataStorytellingAgent`).

## 📄 Distinct PDF Reporting Architecture

Unlike monolithic reporting tools that generate identical layouts for every query, Crewlyze features a **Distinct PDF Reporting Engine** (`ui/export.py`):
- **Polymorphic Dispatch**: The central `export_pdf(result, filename, analysis_id)` seamlessly dispatches to `export_distinct_agent_pdf()` when an `analysis_id` is supplied, while preserving full backward compatibility for consolidated reports.
- **`REPORT_MANIFESTS` Registry**: Defines capability-specific report specifications across all 25 agents (custom cover styling, subtitle, domain badge, KPI scorecards, visual keywords, and domain-specific caveats).
- **Single ReportLab Engine**: Leverages pure Python `reportlab.platypus` flowables with a two-pass `NumberedCanvas` (page X of Y, corporate running headers, footer confidentiality marks, and Obsidian/Crimson visual styling) without any external binary dependencies.

## 💾 Deterministic Data Artifact Store

Agents produce verified, downloadable analytical data artifacts managed by `ArtifactManager` (`tools/artifact_manager.py`):
- Tabular deliverables (e.g., `sales_pareto_breakdown.csv`, `descriptive_statistics.csv`, `flagged_anomalies.csv`, `budget_burn_projection.csv`) are written to `data/sessions/<session_id>/artifacts/`.
- Download endpoints (`/api/artifacts/{key}` and `/api/projects/{project_id}/artifacts/{key}`) enforce strict path traversal validation (`is_safe_filename()` and `Path.is_relative_to()`).
- The frontend dynamically surfaces downloadable artifact chips (`📥 Download CSV`) with real byte sizes directly inside completed agent cards.

