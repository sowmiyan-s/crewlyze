# Usage Guide

## Overview

**Multi Agent Data Analysis with Crew AI** is a premium "Data Analysis as a Service" tool. It uses a swarm of specialized AI agents to clean, validate, analyze, and visualize your datasets automatically.

## Prerequisites

- **Python**: Version 3.10 or higher
- **API Key**: A Groq, OpenAI, Anthropic, or Hugging Face API key (or a local Ollama setup).

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Multi-Agent-Data-Analysis.git
   cd Multi-Agent-Data-Analysis
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # Windows
   # source .venv/bin/activate   # Mac/Linux
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your environment:
   Create a `.env` file in the root directory:
   ```env
   # Example for Groq
   LLM_PROVIDER=groq
   GROQ_API_KEY=your_groq_api_key_here

   # Example for Hugging Face
   # LLM_PROVIDER=huggingface
   # HUGGINGFACE_API_KEY=your_huggingface_api_key_here
   ```

## Quick Start

1. **Prepare Data**: Ensure your CSV file is ready.

2. **Run the System**:
   ```bash
   python crew.py
   ```

3. **Input Path**: When prompted, paste the full path to your CSV file (or press Enter to use the default `data/TB_Burden_Country.csv`).

4. **View Results**: 
   - The system will automatically open `index.html` in your default browser.
   - This report contains your Data Quality Score, Cleaning Logs, Visualizations, and Business Insights.

## Detailed Features

### 1. Data Quality Assurance
The **Data Quality Assurance Specialist** scans your dataset for:
- Missing values and anomalies
- Sufficient volume for analysis
- Data type consistency
- **Output**: A 0-100 Quality Score and a GO/NO-GO decision.

### 2. Automated Cleaning
The **Data Cleaner** agent:
- Removes duplicates
- Fills missing values (Mean for numeric, Mode for categorical)
- Standardizes formats

### 3. Relationship Analysis
The **Relationship Analyst**:
- Identifies correlations between columns
- Selects the best visualization type (Scatter, Bar, Line, Heatmap, etc.)

### 4. Visualization Generation
The **Code Generator**:
- Writes bug-free Matplotlib/Seaborn code
- Executes the code to generate charts embedded in the report

### 5. Business Intelligence
The **Business Intelligence Analyst**:
- Synthesizes all findings into actionable strategic insights.

## Troubleshooting

### Rate Limit Errors
If you see `RateLimitError`:
- Switch to a smaller model in `config/llm_config.py` (e.g., `llama-3.1-8b-instant`).
- The system is optimized to minimize token usage, but heavy usage may still hit free tier limits.

### Browser Not Opening
- Manually open `index.html` in your browser.

## Support

For issues, please open a ticket on our GitHub repository.

---

*Multi Agent Data Analysis with Crew AI*
*Copyright (c) 2025 Sowmiyan S*
*Licensed under the MIT License*
