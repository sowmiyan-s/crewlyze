<div align="center">
  <img src="https://raw.githubusercontent.com/sowmiyan-s/crewlyze/main/assets/branding_image.png" alt="Crewlyze - Autonomous Multi-Agent Data Analyst Platform" width="100%" style="border-radius: 14px; box-shadow: 0 12px 32px rgba(0,0,0,0.3);" />
</div>

<br />

<h1 align="center" style="font-size: 3rem; font-weight: 800; letter-spacing: -1px; margin-bottom: 0;">
  🚀 Crewlyze 🚀
</h1>

<p align="center">
  <strong style="font-size: 1.25rem; color: #a78bfa;">The Autonomous Multi-Agent Business Intelligence & Data Science Platform</strong><br />
  <em>Transforming raw CSV, Excel, and SQLite datasets into executive PDF reports, interactive charts, and strategic business recommendations in seconds.</em>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/crewlyze">
    <img src="https://img.shields.io/npm/v/crewlyze?style=for-the-badge&color=cb3837&logo=npm" alt="NPM Version" />
  </a>
  <a href="https://github.com/sowmiyan-s/crewlyze/releases">
    <img src="https://img.shields.io/badge/Release-v1.2.1-7c3aed?style=for-the-badge&logo=github" alt="Release" />
  </a>
  <a href="https://python.org">
    <img src="https://img.shields.io/badge/Python-3.10%20to%203.13-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  </a>
  <a href="https://github.com/sowmiyan-s/crewlyze/stargazers">
    <img src="https://img.shields.io/badge/Stars-%E2%98%85%20Trending-f59e0b?style=for-the-badge&logo=github" alt="Stars" />
  </a>
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="License: MIT" />
  </a>
</p>

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
