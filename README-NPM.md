# 🚀 Crewlyze

> **The Autonomous Multi-Agent Data Analysis & Business Intelligence Engine.**

[![NPM Version](https://img.shields.io/npm/v/crewlyze?style=for-the-badge&color=cb3837&logo=npm)](https://www.npmjs.com/package/crewlyze)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.10%20to%203.13-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

**Crewlyze** transforms raw CSV, Excel, and SQLite datasets into executive PDF reports, interactive charts, and strategic business recommendations in seconds—**no programming or data science experience required!**

---

## ⚡ Quickstart (1-Line Setup)

Install and run Crewlyze globally on **Windows**, **macOS**, or **Linux** with one command:

```bash
# 1. Install globally via NPM
npm install -g crewlyze

# 2. Launch the application
crewlyze
```

🎉 **That's it!** Crewlyze automatically sets up the environment, launches the web interface at `http://localhost:8000`, and opens your default browser.

---

## 🌟 Why Choose Crewlyze? (Key Advantages)

* 🎯 **Zero Code Needed:** Upload any CSV or Excel spreadsheet and let AI handle cleaning, modeling, and visualization automatically.
* 🔒 **100% Offline Air-Gapped Privacy:** Run completely local offline analyses using **Ollama** (`llama3`, `mistral`, `phi3`) with zero cloud data transmission.
* 📄 **C-Suite PDF Reports:** Download polished, McKinsey/BCG-style PDF briefing reports with 1 click.
* 🤖 **7 Specialized AI Agents:** A team of dedicated AI specialists collaborates to audit and analyze your data from every angle.
* 🔑 **Universal AI Support:** Compatible with OpenAI (GPT-4o), Anthropic (Claude 3.5), Google Gemini, NVIDIA NIM, DeepSeek, and custom LLM providers.
* 💬 **Interactive AI Data Copilot:** Ask questions about your dataset in plain English and receive instant chart updates and SQL analysis.
* 📝 **Instant Live Reporting & Feedback:** Built-in modal to submit bug reports and feature requests with zero-setup direct email delivery.

---

## 🤖 The 7 Autonomous AI Agents Explained

Crewlyze deploys a team of 7 specialized AI agents that work sequentially on your dataset:

| Agent Icon & Name | What It Does (Non-Tech Explanation) |
| :--- | :--- |
| 🧹 **1. Data Cleaning Agent** | **Fixes messy data.** Automatically repairs missing entries, strips currency symbols, strips whitespace, casts data types, and removes duplicate rows. |
| 🔗 **2. Relationship Analyst** | **Finds hidden connections.** Computes statistical correlations and identifies how key columns in your dataset influence each other. |
| 💡 **3. Business Insights Agent** | **Acts as your strategy consultant.** Synthesizes findings into McKinsey-style executive pillars, risk warnings, and actionable growth opportunities. |
| 🤖 **4. Predictive Auto-ML Agent** | **Discovers key growth drivers.** Trains automated machine learning models to rank variable importance and identify primary success drivers. |
| 🛡️ **5. Anomaly Risk Auditor** | **Detects red flags & outlier spikes.** Scans distributions using IQR & Z-score statistics to alert you to unexpected data anomalies. |
| 📈 **6. Trend Forecast Analyst** | **Projects future momentum.** Tracks time-series data to calculate trajectory growth vectors and momentum directions. |
| 🎨 **7. Visual Intelligence Agent** | **Creates beautiful charts.** Generates high-resolution Matplotlib/Seaborn plots and interactive, zoomable Plotly dashboards. |

---

## 💡 How to Use Crewlyze in 3 Easy Steps

1. **Upload Dataset:** Drag & drop any CSV or Excel file on the home dashboard.
2. **Select AI Agents:** Pick which agents you want to run (or leave default to run full pipeline).
3. **Explore Results:** View interactive dashboards, chat live with your AI Copilot, or click **Export PDF Report**.

---

## 💻 Developer & Source Installation

To run directly from Python source:

```bash
git clone https://github.com/sowmiyan-s/crewlyze.git
cd crewlyze
python -m venv venv
# Windows: venv\Scripts\activate | macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

## 📜 License

Distributed under the **MIT License**. Created with ❤️ by [Sowmiyan S](https://github.com/sowmiyan-s).
