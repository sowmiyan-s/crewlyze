# Crewlyze User Guide

Complete operational guide for **Crewlyze** — Autonomous 7-Agent Business Intelligence & Data Science Platform.

---

## ⚡ 1. Getting Started & Launching Crewlyze

Crewlyze can be launched across any platform with zero compilation needed.

### 🪟 Windows (Standalone Setup Wizard)
1. Download **`Crewlyze_Setup_v1.2.3.exe`** from [GitHub Releases](https://github.com/sowmiyan-s/crewlyze/releases).
2. Follow the setup wizard (automatically registers `crewlyze` in system PATH and provisions the Python runtime).
3. Open any Command Prompt or PowerShell and run:
   ```cmd
   crewlyze
   ```
4. Crewlyze launches at `http://127.0.0.1:8000` and automatically opens your default web browser.

### ⚡ macOS / Linux / Windows (Global NPM Launcher)
```bash
# 1. Install globally via NPM
npm install -g crewlyze

# 2. Launch
crewlyze
```

### 💻 Developer Mode (Python Source)
```bash
# 1. Clone repository
git clone https://github.com/sowmiyan-s/crewlyze.git
cd crewlyze

# 2. Setup virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start backend server
python main.py
```

---

## 📂 2. Working with Datasets

### Supported File Types
Crewlyze ingests data with zero manual configuration:
- **CSV files** (`.csv`) with automatic delimiter and multi-encoding detection (UTF-8, Latin-1, CP1252, ISO-8859-1).
- **Excel spreadsheets** (`.xlsx`, `.xls`) with automatic sheet parsing.
- **SQLite databases** (`.db`, `.sqlite`, `.sqlite3`).

### Creating a Project Workspace
1. Drag and drop your file into the **Upload Zone** on the home screen (or click to browse).
2. Crewlyze validates the schema, computes baseline statistics (rows, columns, data types, missing value densities), and creates an isolated project workspace in `data/sessions/<project_id>/`.
3. The dashboard opens with:
   - **Dataset Telemetry Banner**: Row and column counts, memory footprint, and numeric/categorical breakdowns.
   - **Live Data Preview Grid**: Sortable, interactive paginated table of your dataset.
   - **Quick Action Hub**: Choose between **Crew Chat** or **Agentic Analysis**.

---

## 🤖 3. The 7-Agent Autonomous Pipeline

Crewlyze delegates dataset processing across a coordinated 7-agent swarm:

1. 🧹 **Data Quality & Profiling Agent (`agents/cleaner.py`)**:
   - Removes duplicate rows and evaluates missing value densities (>60% threshold column pruning).
   - Automatically imputes missing numbers (mean/median) and categoricals.
   - Generates a side-by-side **Data Cleaning Diff Summary**.

2. 🔗 **Relationship & Correlation Analyst (`agents/relation.py`)**:
   - Direct execution visualization engine computes Pearson and Spearman correlation matrices.
   - Identifies non-linear connections between columns without stalling the pipeline.

3. 💼 **Senior Business Insights Consultant (`agents/insights.py`)**:
   - Synthesizes findings into McKinsey-style consulting pillars.
   - Outputs structured **Observation ➔ Business Implication ➔ Actionable Strategy** cards with risk alerts.

4. 🎨 **Interactive Visualizer (`agents/visualizer.py`)**:
   - Creates publication-grade, styled Matplotlib and Seaborn charts embedded directly in reports.
   - Powers the interactive Plotly visual dashboard with zoom, pan, and hover tooltips.

5. 🤖 **Predictive Auto-ML Specialist (`agents/predictive.py`)**:
   - Trains automated regression and classification heuristics to identify key growth drivers and feature importances.

6. 🚨 **Anomaly & Risk Auditor (`agents/anomaly.py`)**:
   - Evaluates IQR distributions and Z-scores to flag statistical outliers, operational anomalies, and data drift.

7. 📈 **Temporal Trend Analyst (`agents/trend.py`)**:
   - Analyzes date and period sequences to compute directional momentum vectors and rolling growth velocity.

---

## 💬 4. AI Copilot & Real-Time Chat

Click **Crew Chat** in your project workspace to interact conversationally with your data:
- **Slash `/` Column Autocomplete**: Type `/` in the chat input bar to trigger an interactive dropdown of all columns in your dataset alongside their data types.
- **Sub-Second Custom Charts (<0.2s)**: Ask for any custom chart (e.g. *"Plot a correlation heatmap between Revenue and Marketing Spend"* or *"Show a distribution histogram of Customer Age"*). The copilot generates and runs the Python code in a sandboxed child process, displaying the chart inline with a **📥 Download PNG** button.
- **Chat History Persistence**: Conversations and generated chart image cards auto-save to `data/sessions/<project_id>/chat_history.json` and restore seamlessly on refresh (`F5`).

---

## 🔍 5. Read-Only SQL Workbench

Execute ad-hoc SQL queries directly against your dataset:
- Enter standard SQL queries (`SELECT Region, SUM(Sales) AS Total_Sales FROM dataset GROUP BY Region ORDER BY Total_Sales DESC`).
- **Security Guardrails**: Permitted statements are strictly read-only (`SELECT`, `WITH`, `EXPLAIN`). Mutating statements (`DROP`, `DELETE`, `UPDATE`, `ALTER`) are rejected.
- **3-Second Timeout**: Protected by an internal SQLite progress handler to prevent resource locks.

---

## 📄 6. Document Export Suite

- **C-Suite Executive PDF Report**: Download a multi-page, publication-quality PDF report complete with KPI scorecards, data quality grades, executive SWOT analysis, and embedded high-resolution figures.
- **PowerPoint Slide Deck (`.pptx`)**: Export key findings directly into presentation slides.
- **Jupyter Notebook (`.ipynb`)**: Download an executable notebook containing all cleaning, modeling, and plotting code.
- **Project ZIP Archive**: Download a complete backup archive containing raw data, cleaned CSV, charts, and metadata.

---

## ⚙️ 7. Universal Settings & Integrations

Access **Settings** from the sidebar to configure:
- **LLM Providers**: Choose from 13+ providers (NVIDIA NIM, Ollama, OpenAI, Anthropic, Gemini, Groq, DeepSeek, Mistral, etc.).
- **100% Offline Air-Gapped Mode**: Point to local **Ollama** (`http://localhost:11434`) for zero-cloud data privacy.
- **Outbound Notifications**: Set up SMTP Email, Discord Webhook, or Slack Webhook credentials for automated report dispatch upon analysis completion.
