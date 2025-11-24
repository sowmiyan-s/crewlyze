# Usage Guide

## Overview

The CrewAI Data Analyst Agent is a streamlined tool for automated data analysis. It processes CSV files, identifies relationships, and generates insightful reports with visualizations.

## Prerequisites

- **Python**: Version 3.8 or higher
- **Dependencies**: Install via `pip install -r requirements.txt`
- **LLM Backend (Optional)**: Ollama for enhanced analysis
  - Download from [ollama.ai](https://ollama.ai)
  - Pull a model: `ollama pull llama3`
  - Run in background: `ollama serve`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/CrewAI-Data-Analyst-Agent.git
   cd CrewAI-Data-Analyst-Agent
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

1. Place your CSV file in the `data/` directory (e.g., `data/input.csv`).

2. Run the analysis:
   ```bash
   python crew.py
   ```

3. View results: The browser will automatically open `index.html` with the analysis report.

## Detailed Usage

### Input Data
- Supported format: CSV
- Place files in `data/input.csv` or modify `crew.py` to specify a different path
- Ensure data is clean and properly formatted for best results

### Output
- **HTML Report**: `index.html` - Interactive report with insights and visualizations
- **Console Output**: Real-time pipeline execution logs
- **Outputs Directory**: Additional generated files (e.g., code snippets in `outputs/op.py`)

### Customization

#### Modifying Agents
Edit agent configurations in `agents/*.py`:
- Change LLM model or endpoint
- Adjust agent backstories and goals
- Update prompts for specific analysis needs

#### Extending the Pipeline
Add more agents by uncommenting in `crew.py` and updating `workflows/pipeline.py`:
- Data cleaning: Uncomment `cleaner_agent`
- Validation: Uncomment `validator_agent`
- Code generation: Uncomment `code_gen_agent`

#### Configuration
- LLM settings: Modify `config/llm_config.py`
- Pipeline tasks: Edit `workflows/pipeline.py`

## Examples

### Basic Analysis
```bash
python crew.py
# Analyzes data/input.csv and generates index.html
```

### Custom Dataset
1. Place your CSV in `data/custom.csv`
2. Modify `crew.py` to load `data/custom.csv`
3. Run `python crew.py`

### Advanced Configuration
- For different LLM models, update `agents/relation.py` with new `base_url` and model name
- Adjust task parameters in `workflows/pipeline.py` for specific analysis goals

## Troubleshooting

### Common Issues

**ModuleNotFoundError**
```
pip install crewai pandas matplotlib seaborn
```

**Connection Refused (LLM)**
- Ensure Ollama is running: `ollama serve`
- Check network connectivity to `http://localhost:11434`
- Analysis will proceed without LLM if connection fails

**UnicodeEncodeError**
- Resolved in latest version; uses UTF-8 encoding
- If issues persist, ensure CSV files are UTF-8 encoded

**Browser Not Opening**
- Manually open `index.html` in your browser
- Check file permissions

### Performance Tips
- Use smaller datasets for faster processing
- Ensure sufficient RAM for large CSV files
- Close other applications during analysis

## Best Practices

- **Data Preparation**: Clean and validate input data before analysis
- **Version Control**: Use `.gitignore` to exclude sensitive files (e.g., `.env`)
- **Environment**: Always use virtual environments
- **Updates**: Check CHANGELOG.md for latest features and fixes

## Support

For issues or questions:
- Check the [GitHub Issues](https://github.com/yourusername/CrewAI-Data-Analyst-Agent/issues) page
- Review the README.md for additional documentation
- Ensure all prerequisites are met before reporting bugs

---

*Last updated: October 2023*
