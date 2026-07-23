<div align="center">
  <img src="assets/branding_image.png" alt="Crewlyze - Autonomous Data Analysis Platform" width="100%" style="border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.15);" />
</div>

<h1 align="center" style="font-size: 4rem; margin-bottom: 0;">🚀 Crewlyze 🚀</h1>

<p align="center">
  <strong style="font-size: 1.3rem; color: #8b5cf6;">The Premier Autonomous Multi-Agent Data Analyst Platform.</strong><br>
  <em>Transforming raw datasets into cinematic executive reports, custom visualizations, and actionable business intelligence using CrewAI, FastAPI, and Vanilla JS.</em>
</p>

<p align="center">
  <a href="https://github.com/sowmiyan-s/Multi-Agent-Data-Analysis-System-with-CrewAI/releases">
    <img src="https://img.shields.io/github/v/release/sowmiyan-s/Multi-Agent-Data-Analysis-System-with-CrewAI?style=for-the-badge&color=6366f1" alt="Release">
  </a>
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License: MIT">
  </a>
  <a href="https://github.com/sowmiyan-s/Multi-Agent-Data-Analysis-System-with-CrewAI/stargazers">
    <img src="https://img.shields.io/github/stars/sowmiyan-s/Multi-Agent-Data-Analysis-System-with-CrewAI?style=for-the-badge&color=f59e0b" alt="Stars">
  </a>
  <a href="https://www.npmjs.com/package/crewlyze">
    <img src="https://img.shields.io/npm/v/crewlyze?style=for-the-badge&color=cb3837&logo=npm" alt="NPM Version">
  </a>
  <a href="https://python.org">
    <img src="https://img.shields.io/badge/Python-3.10%20to%203.13-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
  </a>
</p>

---

## 📑 Table of Contents

<details open>
<summary><strong>Click to Expand/Collapse Navigation</strong></summary>

1. [🌍 Executive Vision & Enterprise Value](#-executive-vision--enterprise-value)
2. [✨ Core Capabilities & Feature Deep-Dive](#-core-capabilities--feature-deep-dive)
3. [📸 Live Application Interface Showcase](#-live-application-interface-showcase)
4. [🏗️ Technical Architecture & Design](#-technical-architecture--design)
5. [🛡️ Security & Privacy (Local Execution)](#️-security--privacy-local-execution)
6. [🚀 Installation & Quickstart](#-installation--quickstart)
7. [🔑 Universal LLM Gateways & Configuration](#-universal-llm-gateways--configuration)
8. [📬 Outbound Integrations Hub (SMTP & Discord)](#-outbound-integrations-hub-smtp--discord)
9. [📊 Executive Deliverables & Export Formats](#-executive-deliverables--export-formats)
10. [📂 Project Structure & API Endpoints](#-project-structure--api-endpoints)
11. [🛠️ Troubleshooting & FAQ](#️-troubleshooting--faq)
12. [📜 License & Legal](#-license--legal)

</details>

---

## 🌍 Executive Vision & Enterprise Value

In the era of Big Data, the primary bottleneck is no longer data collection—it is **data interpretation**. Traditional data analysis requires hours of manual Python scripting (Pandas, Numpy), cleaning messy datasets, calculating correlation matrices, and building slide decks for stakeholders.

**Crewlyze** shatters this paradigm by introducing an **Autonomous Multi-Agent Swarm** paired with a real-time **AI Chat Copilot**. Powered by [CrewAI](https://github.com/joaomdmoura/crewai) and [LiteLLM](https://github.com/BerriAI/litellm), Crewlyze acts as an entire autonomous data department. Specialized AI personas independently clean, audit, analyze, and visualize your data in minutes.

### 💡 Key Value Drivers
- **Zero-SDK One-Line Setup:** Run `npx crewlyze` on Windows, macOS, or Linux without installing C++, Rust, or Java build toolchains. Prebuilt Python binary wheels install automatically.
- **3-Minute Executive Audits:** Replaces 15+ hours of manual Exploratory Data Analysis (EDA) with a complete multi-page PDF executive report, SWOT matrix, and interactive charts.
- **Air-Gapped Privacy:** Run 100% offline using **Ollama** (`http://localhost:11434`), ensuring confidential corporate data never leaves your machine.

---

## ✨ Core Capabilities & Feature Deep-Dive

### 🤖 1. Multi-Agent Swarm Orchestration
When a dataset is uploaded, Crewlyze triggers a sequential 4-agent cascade:
*   **🧹 Data Quality & Profiling Agent (`cleaner.py`):** Drops columns with >60% null values, standardizes headers, imputes numeric missing values, and generates audit trails.
*   **📊 Relationship & Correlation Analyst (`relation.py`):** Calculates Pearson linear indices, Spearman rank correlations, ANOVA variances, and non-linear trend maps.
*   **💼 Senior Strategy Consultant (`insights.py`):** Translates raw statistical correlations into boardroom-ready SWOT matrices, risk bottleneck alerts, and C-suite action items.
*   **📈 Interactive Plotly Visualizer (`visualizer.py`):** Builds responsive, hoverable Plotly dashboard charts.

---

### 💬 2. Real-Time AI Chat & Copilot Suite
Interrogate your dataset dynamically using an intuitive, real-time conversational chat:
*   **Non-Blocking Token & Thought Streaming:** Powered by background thread executors (`loop.run_in_executor`) and Server-Sent Events (SSE). Streams AI reasoning thoughts with a subtle blinking *Thinking...* status.
*   **Slash `/` Column Picker:** Type `/` in the chat input bar to open an interactive column autocomplete dropdown displaying column names and data types.
*   **Automatic Chat History Persistence:** Chat conversations and generated chart images auto-save to `chat_history.json` inside each project's directory and restore upon reload (`F5`).
*   **Chat Exports:** Download complete AI chat threads as Markdown (`.md`) or PDF.

---

### 📊 3. Unlimited Custom Visualization Engine
Ask for ANY custom visualization and Crewlyze generates it in milliseconds (<0.2s) via Matplotlib/Seaborn:
*   **Supported Chart Types:** Distribution Histograms, Box & Violin Plots, Scatter & 3D Scatter Plots, Correlation Heatmaps, Time-Series Line Graphs, Stacked & Grouped Bar Charts, Pie & Donut Charts, Radar Plots, and Subplot Dashboards.
*   **Single Download Overlay:** Hover over any generated chart to immediately download a high-res PNG image via the single `📥 Download PNG` button.
*   **Concise Output Control:** When generating visualizations, the copilot prints ONLY a 1-sentence caption introducing the chart, suppressing unasked text clutter.

---

### 🔍 4. Read-Only SQL Query Workbench
*   **NLP-to-SQL Compiler:** Ask plain English questions (*"Show top 10 transactions by revenue"*) to automatically generate and execute SQL statements against the SQLite engine.
*   **3-Second Timeout & DoS Protection:** SQLite progress handlers interrupt long-running queries after 3 seconds. Administrative/mutating commands (`DROP`, `DELETE`, `UPDATE`) are strictly blocked.

---

### 📬 5. Outbound Integrations Hub (SMTP & Discord)
Dispatch automated executive reports to external communication channels:
*   **SMTP Email Client:** Automatically email generated PDF reports via SMTP relays (Port 587 STARTTLS / 465 SSL).
*   **Discord Webhook Alerts:** Posts rich markdown embeds with metric summaries, warning badges, and direct PDF attachments to Discord channels.
*   **Slack & Custom REST Webhooks:** Dispatch summary cards and JSON metadata payloads to Slack or custom endpoints.

---

### 🔄 6. Stay-on-Page Workspace Reload Persistence
- **Reload State Manager:** `localStorage` session management automatically restores your active project and exact section tab (`Crew Chat`, `Crew Analysis`, or `Hub`) on browser refresh (`F5`).

---

## 📸 Live Application Interface Showcase

Explore live previews captured directly from an active Crewlyze workspace session:

| Application Section | Live Preview & Key Capabilities |
| :--- | :--- |
| **🤖 Real-Time AI Chat & Custom Viz Engine** | <img src="file:///C:/Users/Asus/.gemini/antigravity-ide/brain/90240ab2-7394-40fc-84d1-ee7679e5d9ed/chat_interface_with_chart_1784827501907.png" alt="AI Chat Interface with Custom Chart" width="100%" style="border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);" /><br>*Real-time AI Chat streaming with subtle blinking Thinking... status, custom Matplotlib/Seaborn visualization generation, and single 1-click `📥 Download PNG` button overlays.* |
| **🏢 Project Workspace Hub** | <img src="assets/Screenshots/3.INSIDE PROJECT.png" alt="Project Workspace Hub" width="100%" style="border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);" /><br>*Central project hub with stay-on-page reload state management, dataset preview grid, and instant navigation between Crew Analysis and AI Chat.* |
| **📊 Interactive Dashboards & Plotly Engine** | <img src="assets/Screenshots/8.VISUALIZATION.png" alt="Interactive Dashboards" width="100%" style="border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);" /><br>*Autonomous multi-agent Plotly chart suite with responsive hover tooltips, zoom/pan controls, and feature distribution maps.* |
| **💼 Strategic Business Insights & SWOT** | <img src="assets/Screenshots/7.BUSINESS INSIGHTS.png" alt="Executive Business Insights" width="100%" style="border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);" /><br>*C-suite strategic insights, SWOT risk matrices, correlation analysis, and automated executive action item recommendations.* |
| **⚙️ Settings & Universal LLM Config** | <img src="assets/Screenshots/2.SETTINGS.png" alt="Universal LLM Config" width="100%" style="border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);" /><br>*Configure 100+ cloud & local LLMs (Ollama, OpenAI, Anthropic, Gemini, NVIDIA, Minimax) and SMTP / Discord outbound webhooks.* |

---

## 🏗️ Technical Architecture & Design

Crewlyze features a modern dual-engine architecture built for high performance and zero clutter:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Vanilla JS Frontend (Browser)                   │
│   - Glassmorphism Dark Theme  - SSE Streaming Receiver                 │
│   - Slash / Column Autocomplete - Stay-on-Page Reload State            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / SSE Stream
┌───────────────────────────────────▼────────────────────────────────────┐
│                        FastAPI Asynchronous Backend                    │
│   - Non-Blocking Thread Executors  - Read-Only SQL Workbench           │
│   - Subprocess Code Sandbox        - Automatic Chat History Storage    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ CrewAI & LiteLLM
┌───────────────────────────────────▼────────────────────────────────────┐
│                Universal LLMs & Local Execution (Ollama)              │
│   Ollama Local / OpenAI / Anthropic / Gemini / NVIDIA / Minimax / Groq  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Security & Privacy (Local Execution)

- **Air-Gapped Local Privacy:** Configure **Ollama** (`http://localhost:11434`) for 100% offline analysis. Zero data bytes leave your local network.
- **Isolated Subprocess Sandboxing:** Generated Python code runs inside child processes via `subprocess.run()`, eliminating parent `exec()` vulnerabilities.
- **Path Traversal Guards:** File paths are validated using `.resolve()` and `.relative_to()` security checks.

---

## 🚀 Installation & Quickstart

### ⚡ Option 1: NPM Launcher (Recommended for All Systems)
Works out-of-the-box on Windows, macOS, and Linux. No C++ or Rust compilers required.

```bash
# Install globally via NPM
npm install -g crewlyze

# Launch Crewlyze from anywhere in your terminal
crewlyze
```
> 🎉 **Success:** The server will initialize and launch your default browser to `http://localhost:8000`.

---

### 🐳 Option 2: Docker Container
Ideal for cloud deployment (AWS, GCP, Azure) or isolated local setups:

```bash
git clone https://github.com/sowmiyan-s/Multi-Agent-Data-Analysis-System-with-CrewAI.git
cd Multi-Agent-Data-Analysis-System-with-CrewAI
docker-compose up --build -d
```

---

### 💻 Option 3: Python Developer Setup

```bash
# 1. Clone repository
git clone https://github.com/sowmiyan-s/Multi-Agent-Data-Analysis-System-with-CrewAI.git
cd Multi-Agent-Data-Analysis-System-with-CrewAI

# 2. Virtual environment setup
python -m venv venv
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 3. Install requirements
pip install -r requirements.txt

# 4. Start backend server
python main.py
```

---

## 🔑 Universal LLM Gateways & Configuration

Crewlyze supports 100+ LLM models via LiteLLM. Configure keys in the Sidebar Settings Modal:

| Provider | Setup Instructions | Example Models |
| :--- | :--- | :--- |
| 🦙 **Ollama (Offline)** | Boot Ollama on `http://localhost:11434`. 100% free & offline! | `ollama/llama3.1`, `ollama/qwen2.5` |
| 🟢 **OpenAI** | Enter OpenAI API Key (`OPENAI_API_KEY`) | `gpt-4o`, `gpt-4o-mini` |
| 🟣 **Anthropic** | Enter Anthropic API Key (`ANTHROPIC_API_KEY`) | `claude-3-5-sonnet` |
| 🔵 **Google Gemini** | Enter Gemini API Key (`GEMINI_API_KEY`) | `gemini/gemini-1.5-flash` |
| 🟢 **NVIDIA NIM** | Enter NVIDIA NIM API Key (`NVIDIA_API_KEY`) | `nvidia/llama-3.1-70b-instruct` |
| ⚡ **Groq / DeepSeek** | Enter API Key in Settings | `groq/llama-3.3-70b-versatile` |

---

## 📬 Outbound Integrations Hub (SMTP & Discord)

Configure outbound notification channels in the Settings Modal to automatically dispatch reports:
- **SMTP Email Dispatch:** Delivers PDF executive reports via SMTP relays (Port 587 STARTTLS / 465 SSL).
- **Discord Webhooks:** Dispatches rich markdown embeds with metric summaries and PDF attachments.
- **Slack & REST Webhooks:** Posts summary cards and JSON metadata payloads.

---

## 📊 Executive Deliverables & Export Formats

1. **HTML-Escaped PDF Executive Summary:** ReportLab PDF report containing SWOT matrices, cleaning audit trails, and embedded high-res chart images.
2. **PowerPoint Presentation (`.pptx`):** Slide decks ready for C-suite presentations.
3. **ZIP Workspace Archive:** Bundles datasets, cleaned tables, charts, logs, PDF reports, and chat transcripts into a single ZIP file.

---

## 📂 Project Structure & API Endpoints

```
├── main.py                # FastAPI backend & SSE stream endpoints
├── crew.py                # CrewAI multi-agent swarm manager
├── agents/                # Agent prompt definitions (cleaner, relation, insights, visualizer)
├── ui/copilot.py          # AI Chat Copilot streaming generator & custom viz engine
├── config/                # Context & LLM configuration handlers
├── tools/                 # Subprocess sandbox execution & DuckDB tools
├── web/                   # Vanilla JS frontend (index.html, style.css, app.js)
├── bin/crewlyze.js        # Node.js CLI launcher
└── package.json           # NPM package configuration
```

### Key API Endpoints
- `POST /api/analyze` - Trigger autonomous multi-agent swarm.
- `POST /api/copilot/stream` - SSE streaming endpoint for AI Chat.
- `GET /api/chat-history` - Load saved project chat history.
- `POST /api/chat-history` - Save project chat history.
- `POST /api/query-sql` - Execute read-only SQL queries.
- `POST /api/test-smtp` / `POST /api/test-discord` - Test outbound notifications.

---

## 🛠️ Troubleshooting & FAQ

<details>
<summary><strong>Q: Why does npx crewlyze work without C++ or Rust compilers?</strong></summary>
Crewlyze uses binary wheel flags (`--prefer-binary`) during Python dependency resolution, avoiding source compilation on Windows, macOS, and Linux.
</details>

<details>
<summary><strong>Q: How do I run Crewlyze 100% offline?</strong></summary>
Install Ollama, run `ollama run llama3.1`, select Ollama as provider in Crewlyze Settings, and set Base URL to `http://localhost:11434`.
</details>

<details>
<summary><strong>Q: How does page reload stay on the exact same tab?</strong></summary>
Crewlyze manages session state in `localStorage` (`crewlyze_active_project_id` & `crewlyze_active_section`), restoring active project tabs automatically on `F5` refresh.
</details>

---

## 📜 License & Legal

Distributed under the **MIT License**. Free for commercial and personal use.

---

<div align="center">
  <sub>Built with ❤️ by Sowmiyan S and the Open Source Community.</sub>
</div>
