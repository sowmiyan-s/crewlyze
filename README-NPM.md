# 🚀 Crewlyze (NPM Package)

> **The Premier Autonomous Multi-Agent Business Intelligence & Data Science Platform.**

[![NPM Version](https://img.shields.io/npm/v/crewlyze?style=for-the-badge&color=cb3837&logo=npm)](https://www.npmjs.com/package/crewlyze)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.10%20to%203.13-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

Transform raw CSV, Excel, and SQLite datasets into C-suite executive PDF reports, custom interactive visualizations, and strategic business intelligence using **CrewAI**, **FastAPI**, and **Vanilla JS**.

---

## ⚡ Instant Quickstart (Zero-SDK Setup)

Install and run Crewlyze globally across **Windows**, **macOS**, and **Linux** without compiling C++, Rust, or Java build toolchains:

```bash
# 1. Install Crewlyze globally via NPM
npm install -g crewlyze

# 2. Launch from anywhere in your terminal
crewlyze
```

> 🎉 **Success:** The backend server initializes automatically on port `8000`, polling readiness, and launches your default web browser to `http://localhost:8000`.

---

## ✨ Core Capabilities & Features

*   **🤖 Autonomous 4-Agent Swarm:** Orchestrates sequential CrewAI agents for automated data cleaning (`cleaner.py`), correlation mapping (`relation.py`), strategic SWOT mining (`insights.py`), and chart generation (`visualizer.py`).
*   **💬 Real-Time AI Chat & Streaming Copilot:** Non-blocking Server-Sent Events (SSE) token streaming with blinking *Thinking...* status, slash `/` column autocomplete dropdown, Markdown (`.md`) / PDF exports, and automatic chat history persistence (`chat_history.json`).
*   **📊 Unlimited Custom Visualization Engine:** High-speed Matplotlib/Seaborn plot rendering (<0.2s) supporting ANY plot type (Histograms, Box/Violin, Scatter, Heatmaps, Time-Series, Stacked Bar, 3D Scatter, Radar, Subplots) with 1-click `📥 Download PNG` button.
*   **🦙 100% Offline Air-Gapped Privacy:** Process datasets locally using **Ollama** (`http://localhost:11434`) with zero cloud data transmission.
*   **🔑 Universal LLM Gateways:** Works out-of-the-box with OpenAI (`gpt-4o`), Anthropic (`claude-3-5-sonnet`), Google Gemini (`gemini-1.5-flash`), NVIDIA NIM, Minimax, Groq, DeepSeek, and custom vLLM proxies.
*   **📬 Outbound Integrations Hub:** Automated PDF report dispatching via **SMTP Email** (Port 587 STARTTLS / 465 SSL), **Discord Webhooks** (rich embeds + PDF attachments), **Slack**, and REST APIs.
*   **🔍 Read-Only SQL Query Workbench:** Natural language-to-SQL compiler with 3-second query execution timeout protection.
*   **🔄 Stay-on-Page Reload State:** `localStorage` session manager automatically restores your active project and tab on browser refresh (`F5`).
*   **📑 Executive Deliverable Formats:** ReportLab PDF Executive Summaries (with HTML-entity escaping), PowerPoint presentation slide decks (`.pptx`), and full ZIP workspace archives.

---

## 💻 Python Source Setup (Alternative for Developers)

If you prefer installing directly from Python source:

```bash
git clone https://github.com/sowmiyan-s/Multi-Agent-Data-Analysis-System-with-CrewAI.git
cd Multi-Agent-Data-Analysis-System-with-CrewAI
python -m venv venv
# Linux/macOS: source venv/bin/activate | Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## 📜 License & Author

Distributed under the **MIT License**. Created by [Sowmiyan S](https://github.com/sowmiyan-s).
