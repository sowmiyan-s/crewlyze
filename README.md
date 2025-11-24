<!-- Enhanced README: hero, badges, tech icons, screenshots -->

<p align="center">
	<img src="assets/hero.svg" alt="CrewAI Hero" width="900" />
</p>

# CrewAI — Data Analyst Agent

<p align="center">
	<img src="assets/stars.svg" alt="5-star" height="28" />
	&nbsp;&nbsp;
	<img src="assets/badge_crewai.svg" alt="crewai" height="28" />
	<img src="assets/badge_pandas.svg" alt="pandas" height="28" />
	<img src="assets/badge_matplotlib.svg" alt="matplotlib" height="28" />
	<img src="assets/badge_seaborn.svg" alt="seaborn" height="28" />
	<img src="assets/badge_ollama.svg" alt="ollama" height="28" />
</p>

> A professional, modular data-analyst pipeline powered by LLM-driven agents. Feed it a CSV and it will propose cleaning, validate data, suggest visual relationships, generate runnable matplotlib/seaborn code, and produce written insights.

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

2. Start your LLM backend (example: Ollama) and ensure it listens at the address used in `agents/*.py` (default `http://localhost:11434`).

```powershell
ollama serve
```

3. Run the pipeline:

```powershell
python crew.py
```

## What you'll get

- `outputs/op.py` — collected Python snippets extracted from agent outputs (if any).
- `index.html` — a human-friendly summary (raw JSON + highlighted, copyable code blocks).

## Project Structure

```
├── agents/               # AI agent definitions and configurations
│   ├── cleaner.py        # Data cleaning agent
│   ├── validator.py      # Data validation agent
│   ├── relation.py       # Relationship analysis agent
│   ├── code_gen.py       # Code generation agent
│   └── insights.py       # Insights extraction agent
├── config/               # Configuration files
│   ├── llm_config.py     # LLM backend configuration
│   └── __init__.py
├── data/                 # Input data directory
│   └── input.csv         # Default input dataset
├── outputs/              # Generated outputs
│   └── op.py             # Generated Python code
├── tools/                # Utility functions
│   ├── dataframe_ops.py  # DataFrame operations
│   └── __init__.py
├── workflows/            # Workflow definitions
│   ├── pipeline.py       # Main analysis pipeline
│   └── __init__.py
├── assets/               # Static assets for documentation
├── crew.py               # Main entry point
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── USAGE.md              # Detailed usage guide
├── CHANGELOG.md          # Version history
└── LICENSE               # License information
```

## Customization

### Agent Configuration
Modify agent behaviors by editing files in `agents/`:
- Change LLM models in `config/llm_config.py`
- Update agent prompts and backstories
- Adjust agent roles and goals

### Pipeline Extension
Extend analysis capabilities:
- Add new agents for specific tasks
- Modify `workflows/pipeline.py` for custom workflows
- Integrate additional data sources

### Tool Integration
Add custom utilities in `tools/`:
- Data preprocessing functions
- Custom visualization generators
- Export utilities for different formats

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and add tests
4. Submit a pull request

### Guidelines
- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation as needed
- Ensure compatibility with Python 3.8+

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

- 📖 [Usage Guide](USAGE.md)
- 📋 [Changelog](CHANGELOG.md)
- 🐛 [Issues](https://github.com/yourusername/CrewAI-Data-Analyst-Agent/issues)
- 💬 [Discussions](https://github.com/yourusername/CrewAI-Data-Analyst-Agent/discussions)

---

*Built with ❤️ using CrewAI and modern Python practices*

