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

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Configure your LLM provider in `.env` (Groq, OpenAI, Ollama, etc.).

3. Run the pipeline:

```powershell
python crew.py
```

4. Enter the path to your CSV file when prompted.

## What you'll get

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
