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

- Run: `python crew.py`
- Outputs: `outputs/op.py`, `index.html`
- Agents: `agents/` — each agent defines its LLM model and endpoint.

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
    - **Interactive Dashboard**: Real-time analysis logs and progress tracking.
    - **Beautiful Visualizations**: Inline charts and graphs.
    - **Structured Insights**: Clean, bulleted lists for cleaning steps and business insights.
    - **Relation Mapping**: Visual cards showing column relationships.
- `outputs/op.py` — collected Python snippets extracted from agent outputs.
- `index.html` — A professional **Data Analysis Report** featuring:
    - **Data Quality Assessment**: Score, decision, and warnings.
    - **Data Cleaning Steps**: Audit trail of changes.
    - **Visualizations**: Matplotlib/Seaborn charts.
    - **Business Insights**: Strategic findings synthesized from the analysis.

## Project Structure

```
├── agents/               # AI agent definitions
│   ├── cleaner.py        # Data Cleaner
│   ├── validator.py      # Data Quality Assurance Specialist
│   ├── relation.py       # Relationship Analyst
│   ├── code_gen.py       # Code Generator
│   └── insights.py       # Business Intelligence Analyst
├── config/               # Configuration files
│   ├── llm_config.py     # LLM backend configuration
│   └── __init__.py
├── data/                 # Input data directory
│   └── cleaned_csv.csv   # Processed dataset
├── outputs/              # Generated outputs
│   └── op.py             # Generated Python code
├── tools/                # Utility functions
├── workflows/            # Workflow definitions
│   ├── pipeline.py       # Main analysis pipeline
├── assets/               # Static assets
├── crew.py               # Main entry point
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── USAGE.md              # Detailed usage 
├── CHANGELOG.md          # Version history
└── LICENSE               # License information
```

## Customization

### Agent Configuration
Modify agent behaviors by editing files in `agents/`:
- **Validator**: Adjust quality thresholds in `agents/validator.py`.
- **Insights**: Change analysis focus in `agents/insights.py`.

### Pipeline Extension
Extend analysis capabilities:
- Add new agents for specific tasks
- Modify `workflows/pipeline.py` for custom workflows

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
