---
title: Multi Agent Data Analysis
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.31.0
app_file: app.py
pinned: false
---

<!-- Enhanced README: hero, badges, tech icons, screenshots -->



# Multi Agent Data Analysis with Crew AI

<p align="center">
  <img src="assets/complete_workflow.svg" alt="Multi Agent Data Analysis with Crew AI" width="100%" />
</p>

<p align="center">
	<img src="assets/stars.svg" alt="5-star" height="28" />
	&nbsp;&nbsp;
	<img src="assets/badge_crewai.svg" alt="crewai" height="28" />
	<img src="assets/badge_pandas.svg" alt="pandas" height="28" />
	<img src="assets/badge_matplotlib.svg" alt="matplotlib" height="28" />
	<img src="assets/badge_seaborn.svg" alt="seaborn" height="28" />
	<img src="assets/badge_ollama.svg" alt="ollama" height="28" />
</p>

> **Data Analysis as a Service** | A premium, modular data-analyst pipeline powered by LLM-driven agents. Feed it a CSV and it will perform professional data quality assurance, cleaning, relationship mapping, visualization code generation, and business intelligence synthesis.

## Quick Links

- **Web App**: `streamlit run app.py`
- **CLI**: `python crew.py`
- **Agents**: `agents/` — each agent is a factory function that picks up the current LLM config at runtime.
- **Outputs**: session-isolated PNG visualizations under `outputs/<session_id>/`
- **Live Demo**: [Hugging Face Space](https://huggingface.co/spaces/sowmiyan-s/Multi-Agent-Data-Analysis-with-CrewAI)

## Quick Start

### Option 1: Streamlit Web App (Recommended)

Run the interactive web interface:
```bash
streamlit run app.py
```

### Option 2: Command Line Interface

Run the pipeline directly from the terminal:
```bash
python crew.py
```

## Deploying to Hugging Face Spaces

**[View Live Demo](https://huggingface.co/spaces/sowmiyan-s/Multi-Agent-Data-Analysis-with-CrewAI)**

1.  **Create a New Space**:
    *   Go to [huggingface.co/spaces](https://huggingface.co/spaces).
    *   Click **Create new Space**.
    *   Enter a name (e.g., `multi-agent-data-analyst`).
    *   Select **Streamlit** as the SDK.
    *   Click **Create Space**.

2.  **Upload Files**:
    *   Clone your new Space locally:
        ```bash
        git clone https://huggingface.co/spaces/your-username/multi-agent-data-analyst
        ```
    *   Copy all files from this project into that directory.
    *   Push the files:
        ```bash
        git add .
        git commit -m "Initial commit"
        git push
        ```
    *   *Alternatively, you can upload files directly via the "Files" tab on the Hugging Face website.*

3.  **Configure Secrets**:
    *   Go to the **Settings** tab of your Space.
    *   Scroll to **Variables and secrets**.
    *   Click **New secret**.
    *   Add your API keys (e.g., `GROQ_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`).
    *   *Note: You do not need to set `LLM_PROVIDER` here; the user selects it in the app.*

4.  **Run**:
    *   The app will build and launch automatically!

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Configure your LLM provider in `.env` (Groq, OpenAI, Ollama, Hugging Face, Mistral, etc.).

3. Run the application.

4. Upload your CSV file (Web App) or enter the path (CLI).

## What you'll get

- **Premium Web Interface**: A sleek, single-page application with a modern "Obsidian & Electric Violet" theme.
    - **Executive Dashboard**: Scorecards showing row count, column count, numeric and categorical field totals.
    - **Tabbed Results View**: Five dedicated tabs — Data Preview, Clean Report, Relations Map, Key Insights, Visual Intelligence.
    - **Real-time Agent Logs**: A terminal-style scrollable log widget streams agent output as the pipeline runs.
    - **Structured Insights**: Styled bullet and relation cards for cleaning steps, column relationships, and BI insights.
    - **Agent-Generated Visualizations**: PNG charts produced by the visualizer agent, displayed inline.
    - **PDF & CSV Export**: Download a formatted PDF report or the cleaned dataset as CSV.
    - **Per-session Isolation**: Each browser session writes to its own `data/sessions/<id>/` and `outputs/<id>/` directories.
    - **Content-hashed Caching**: Results are cached by MD5 of the file content — no stale data on re-upload of the same file.

## Project Structure

```
.
├── agents/               # AI agent factory functions
│   ├── cleaner.py        # Data Cleaner agent
│   ├── relation.py       # Relationship Analyst agent
│   ├── insights.py       # Business Intelligence Analyst agent
│   └── visualizer.py     # Data Visualizer agent
├── config/               # Configuration
│   ├── llm_config.py     # LLM provider config & param builder
│   └── __init__.py
├── data/                 # Input data
│   └── sessions/         # Per-session working copies (auto-created)
│       └── <session_id>/
│           ├── original.csv   # Pre-cleaning backup
│           └── cleaned.csv    # Cleaned dataset (modified in-place)
├── outputs/              # Generated visualizations
│   └── <session_id>/     # Per-session PNG plots (auto-created)
├── tools/                # CrewAI tool definitions
│   └── dataset_tools.py  # read_head, get_info, clean_python, exec_viz
├── ui/                   # Streamlit UI helpers
│   ├── styles.py         # CSS injection (glassmorphism theme)
│   ├── components.py     # Bullet/relation renderers, StreamlitLogger
│   └── export.py         # PDF report builder (ReportLab)
├── workflows/            # Pipeline orchestration
│   └── pipeline.py       # Agent + Task factory (make_pipeline)
├── assets/               # Static assets (SVG badges, diagrams)
├── app.py                # Streamlit entry point
├── crew.py               # Core orchestration (run_crew)
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── USAGE.md              # Detailed usage guide
├── CHANGELOG.md          # Version history
└── LICENSE               # MIT License
```

## Customization

### Agent Configuration
Modify agent behaviours by editing files in `agents/`:
- **Cleaner**: Adjust cleaning heuristics in `agents/cleaner.py`.
- **Insights**: Change analysis focus in `agents/insights.py`.
- **Relation**: Tune relationship detection in `agents/relation.py`.
- **Visualizer**: Adjust chart generation prompts in `agents/visualizer.py`.

### Pipeline Extension
Extend analysis capabilities:
- Add new agent factories under `agents/`
- Register them in `workflows/pipeline.py`

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

- 📖 [Usage Guide](USAGE.md)
- 📋 [Changelog](CHANGELOG.md)

---

*Multi Agent Data Analysis with Crew AI*
*Copyright (c) 2025 Sowmiyan S*
*Licensed under the MIT License*
