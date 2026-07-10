<div align="center">
  <img src="assets/branding_image.png" alt="Crewlyze - Autonomous Data Analysis Platform" width="100%" style="border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.15);" />
</div>

<h1 align="center" style="font-size: 4rem; margin-bottom: 0;">🚀 Crewlyze 🚀</h1>

<p align="center">
  <strong style="font-size: 1.3rem; color: #8b5cf6;">The Premier Autonomous Multi-Agent Data Analyst Platform.</strong><br>
  <em>Transforming raw datasets into cinematic executive reports and actionable business insights using CrewAI, FastAPI, and Vanilla JS.</em>
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
  <a href="https://github.com/sowmiyan-s/">
    <img src="https://img.shields.io/badge/Sponsor-%E2%9D%A4-pink?style=for-the-badge&logo=github" alt="Sponsor">
  </a>
  <a href="https://www.npmjs.com/package/crewlyze">
    <img src="https://img.shields.io/npm/v/crewlyze?style=for-the-badge&color=cb3837&logo=npm" alt="NPM Version">
  </a>
  <a href="https://python.org">
    <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Version">
  </a>
</p>

---

## 📑 Table of Contents

<details open>
<summary><strong>Click to Expand/Collapse Navigation</strong></summary>

1. [🌍 Executive Vision & Enterprise Value](#-executive-vision--enterprise-value)
2. [✨ Core Capabilities & Feature Deep-Dive](#-core-capabilities--feature-deep-dive)
3. [🏗️ Technical Architecture & Design](#-technical-architecture--design)
4. [🛡️ Security & Privacy (Local Execution)](#️-security--privacy-local-execution)
5. [🚀 Installation & Local Deployment](#-installation--local-deployment)
6. [🔑 API Guidelines & Model Configuration](#-api-guidelines--model-configuration)
7. [📸 Step-by-Step Platform Walkthrough](#-step-by-step-platform-walkthrough)
8. [📊 Deliverables: Reports & Visualizations](#-deliverables-reports--visualizations)
9. [🏢 Industry Use Cases & ROI](#-industry-use-cases--roi)
10. [📂 Project Structure & API Routes](#-project-structure--api-routes)
11. [🛣️ Roadmap & Future Scope](#️-roadmap--future-scope)
12. [🛠️ Comprehensive Troubleshooting](#️-comprehensive-troubleshooting)
13. [🤝 Contributing & Development](#-contributing--development)
14. [👥 Meet the Team & Contributors](#-meet-the-team--contributors)
15. [💖 Sponsorship & Support](#-sponsorship--support)
16. [📜 License & Legal](#-license--legal)

</details>

---

## 🌍 Executive Vision & Enterprise Value

In the era of Big Data, the primary bottleneck is no longer data collection or storage—it is **data interpretation**. Traditional data analysis is heavily gated by technical requirements: writing complex Python scripts (Pandas, Numpy), manually cleaning messy datasets, identifying statistical correlations, and spending hours formatting PowerPoint presentations for stakeholders.

**Crewlyze** completely shatters this paradigm by introducing an **Autonomous Multi-Agent Swarm**. Powered by the orchestration logic of [CrewAI](https://github.com/joaomdmoura/crewai) and the universal model compatibility of [LiteLLM](https://github.com/BerriAI/litellm), Crewlyze mimics an entire physical data department. It assigns distinct, hyper-specialized AI personas—such as the *Data Quality Engineer*, the *Statistical Pattern Spotter*, and the *Senior Business Strategist*—to independently audit, clean, analyze, and visualize your data in minutes.

### 💡 Why Crewlyze is a "Million-Dollar" Solution
For enterprises, data science teams, and C-Suite executives, Crewlyze offers compounding ROI:
- **Exponential Time Savings:** What normally takes a data scientist 15-20 hours of Exploratory Data Analysis (EDA) and reporting is accomplished autonomously in under 3 minutes.
- **Democratization of Data:** Non-technical executives can upload raw CSV/Excel files and instantly receive actionable business strategies—without needing to write a single line of SQL or Python.
- **Privacy-First Architecture:** Unlike ChatGPT or Claude web interfaces, Crewlyze can run completely air-gapped on your local hardware using Ollama, ensuring highly confidential corporate data never leaves your internal network.

---

## ✨ Core Capabilities & Feature Deep-Dive

Crewlyze is not a thin wrapper around a language model; it is a complex orchestration engine equipped with secure, sandboxed code-execution tools.

<details>
<summary><strong>🤖 1. The Autonomous Data Pipeline (Agentic Swarm)</strong></summary>
<br>
When a dataset is uploaded, Crewlyze triggers a multi-agent cascade:

*   **🕵️ Profiling Agent:** Scans the dataset for missing values, extreme outliers, cardinality issues, and data type inconsistencies.
*   **🧹 Cleaning Agent:** Autonomously executes Python code in a secure environment to drop highly-null columns, impute missing values (using mean/median/mode depending on distribution), and sanitize string formatting.
*   **📊 Relational Analysis Agent:** Uses statistical libraries (like `scipy` and `statsmodels`) to hunt for non-linear correlations, feature importances, and hidden multi-variable relationships.
*   **💼 Senior Strategic Agent:** Translates raw statistics ("Feature X has a 0.8 Pearson correlation with Target Y") into boardroom-ready language ("Increasing Feature X by 10% is projected to increase Revenue Y, suggesting immediate marketing budget reallocation").
</details>

<details>
<summary><strong>💬 2. Interactive Data Copilot (Chat AI)</strong></summary>
<br>
Don't need a full report? The Chat AI feature allows you to interrogate your dataset dynamically. 

*   **Natural Language Queries:** "What was our highest selling month in 2023?"
*   **On-the-Fly Transformations:** "Drop all rows where the 'Status' column is 'Pending'."
*   **Dynamic Visuals:** "Plot a scatter graph of Age vs Salary, colored by Department."
</details>

<details>
<summary><strong>📈 3. Natively Embedded, Interactive Visualizations</strong></summary>
<br>
Crewlyze does not hallucinate ASCII charts. It writes and executes `Plotly` Python scripts natively. The resulting HTML-based interactive charts (zoom, pan, hover tooltips) are injected directly into the Vanilla JS frontend for a stunning user experience.
</details>

<details>
<summary><strong>📑 4. Cinematic PDF Generation</strong></summary>
<br>
Using `ReportLab`, Crewlyze captures the AI-generated business insights and statically renders the `Plotly` graphs into a beautifully formatted, multi-page PDF Executive Summary. This report includes dynamic conclusions based on the actual analysis, ready to be emailed to stakeholders.
</details>

---

## 🏗️ Technical Architecture & Design

Crewlyze operates on a dual-engine architecture designed for maximum speed, security, and scalability.

### ⚙️ Backend: FastAPI & Python
- **Asynchronous Execution:** FastAPI handles heavy LLM network requests concurrently, ensuring the UI remains snappy even during massive dataset ingestion.
- **Thread-Isolated Sandboxes:** When the AI writes Python code to clean your data, Crewlyze executes it in isolated subprocesses. This prevents malicious code execution (e.g., `os.system('rm -rf /')`) and protects the host system.
- **Session Management:** Project files, intermediate CSVs, JSON logs, and SQLite metadata are stored securely in `~/.crewlyze/data`, separated by unique Session UUIDs.

### 🎨 Frontend: Vanilla JS & CSS Glassmorphism
We specifically avoided heavy frameworks like React or Angular to keep the application blisteringly fast and dependency-light.
- **State Management:** Handled entirely via localized DOM manipulation and JavaScript Proxy objects.
- **Aesthetics:** Utilizes state-of-the-art Glassmorphism CSS, smooth CSS variables for real-time dark/light mode toggling, and micro-animations to create a premium, "living" application feel.
- **Streaming UI:** Real-time log streaming using Server-Sent Events (SSE) allows the user to watch the AI agents "think" and execute in real-time.

---

## 🛡️ Security & Privacy (Local Execution)

Data privacy is the number one concern for enterprise adoption of AI. Crewlyze tackles this head-on.

*   **No Cloud Storage:** Crewlyze does not upload your CSV files to any external database. All files remain strictly on the machine running the FastAPI server.
*   **Local LLM Integration (Air-Gapped):** By integrating [Ollama](https://ollama.com/), you can download open-source models (like `Llama 3 8B` or `Mistral`) directly to your machine. When configured in the Crewlyze Settings, your data is processed 100% offline. **Zero bytes of data leave your network.**
*   **Secure API Key Storage:** If using Cloud LLMs (OpenAI, Anthropic), API keys are stored exclusively in your browser's local `IndexedDB/localStorage`. They are transmitted securely only when actively making a request.

---

## 🚀 Installation & Local Deployment

Whether you are a developer, a data analyst, or an IT administrator, deploying Crewlyze is incredibly straightforward.

### ⚡ Option 1: NPM Install (Recommended for End-Users)
The fastest, most seamless way to get Crewlyze running on Windows, macOS, or Linux.

**Prerequisites:** 
- [Node.js](https://nodejs.org/) (v16+)
- [Python](https://python.org) (3.10+)

```bash
# 1. Install Crewlyze globally via NPM
npm install crewlyze

# 2. Launch the application from anywhere in your terminal
crewlyze
```
> 🎉 **Success:** The backend server will automatically initialize, and your default web browser will open to `http://localhost:8000`.

### 🐳 Option 2: Docker (Enterprise & Cloud Ready)
Ideal for deploying on AWS, GCP, Azure, or keeping your local machine clean.

```bash
# Clone the repository
git clone https://github.com/sowmiyan-s/Multi-Agent-Data-Analysis-System-with-CrewAI.git
cd Multi-Agent-Data-Analysis-System-with-CrewAI

# Build and start the container in detached mode
docker-compose up --build -d
```
> The application is now running securely inside a containerized Linux environment at `http://localhost:8000`.

### 💻 Option 3: Developer Source Setup
For contributors who want to modify the source code, adjust CSS, or engineer new CrewAI prompts.

```bash
# 1. Clone the repository
git clone https://github.com/sowmiyan-s/Multi-Agent-Data-Analysis-System-with-CrewAI.git
cd Multi-Agent-Data-Analysis-System-with-CrewAI

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the environment
# For macOS/Linux:
source venv/bin/activate
# For Windows:
venv\Scripts\activate

# 4. Install required dependencies
pip install -r requirements.txt

# 5. Start the FastAPI development server
python main.py
```

---

## 🔑 API Guidelines & Model Configuration

Crewlyze's integration with **LiteLLM** means you have access to over 100+ language models globally. Configuration is handled entirely within the UI.

<details>
<summary><strong>🔹 Step 1: Navigating to Settings</strong></summary>
<br>
Click the gear icon (⚙️) on the Home Page to access the secure Settings portal. Here you can configure multiple providers simultaneously.
</details>

<details>
<summary><strong>🔹 Step 2: Adding Cloud API Keys (OpenAI, Anthropic, Gemini)</strong></summary>
<br>
1. Select your desired provider from the dropdown. <br>
2. Paste your secure API key (e.g., `sk-ant-api03...`). <br>
3. Click "Save". The key is encrypted in your local browser state. <br>
4. You can now select flagship models like `gpt-4o`, `claude-3-5-sonnet-20240620`, or `gemini-1.5-pro` from the main project dashboard.
</details>

<details>
<summary><strong>🔹 Step 3: Configuring Local Models (Ollama)</strong></summary>
<br>
1. Download and run Ollama on your machine. <br>
2. Pull a model via terminal: `ollama run llama3:8b` <br>
3. In Crewlyze Settings, select the **Ollama** provider. <br>
4. Set the Custom Base URL to: `http://localhost:11434` <br>
5. Set the model name to exactly match Ollama's registry: `ollama/llama3:8b`
</details>

<details>
<summary><strong>🔹 Step 4: Custom Enterprise Gateways (Azure, AWS Bedrock)</strong></summary>
<br>
If your company routes API traffic through an internal gateway: <br>
1. Select **Custom Provider** in settings. <br>
2. Input the corporate proxy URL. <br>
3. Provide the necessary Bearer tokens and custom header configurations.
</details>

---

## 📸 Step-by-Step Platform Walkthrough

Our frontend is meticulously designed for high readability, minimal friction, and cognitive ease.

### 1️⃣ The Global Dashboard (Home Page)
**Features:** Instantly view your currently active AI model, track token usage, manage all historical projects, and effortlessly create new analysis sessions or import shared `.zip` project files.
<p align="center"><img src="assets/Screenshots/1.HOME%20PAGE.png" alt="Home Page" width="90%" style="border-radius:8px; border:2px solid #2d2d2d; box-shadow: 0 4px 10px rgba(0,0,0,0.5);"/></p>

### 2️⃣ Comprehensive Settings & Integrations
**Features:** A unified hub for API keys. If LiteLLM supports it, Crewlyze supports it. Dynamically search for niche providers (like Groq for ultra-fast inference) and bind them instantly.
<p align="center"><img src="assets/Screenshots/2.SETTINGS.png" alt="Settings" width="90%" style="border-radius:8px; border:2px solid #2d2d2d; box-shadow: 0 4px 10px rgba(0,0,0,0.5);"/></p>

### 3️⃣ The Project Workspace Hub
**Features:** Once a CSV is uploaded, you face a strategic choice. Will you interrogate the data manually via the **Chat AI**, or will you deploy the **Data Analyst Crew** for an exhaustive, autonomous audit?
<p align="center"><img src="assets/Screenshots/3.INSIDE%20PROJECT.png" alt="Inside Project" width="90%" style="border-radius:8px; border:2px solid #2d2d2d; box-shadow: 0 4px 10px rgba(0,0,0,0.5);"/></p>

### 4️⃣ Interactive Chat Assistant (Copilot)
**Features:** A ChatGPT-like interface injected directly with your data's context. Ask the AI to perform complex filtering, calculate standard deviations, or explain anomalies in plain English.
<p align="center"><img src="assets/Screenshots/4.CHAT%20AI.png" alt="Chat AI" width="90%" style="border-radius:8px; border:2px solid #2d2d2d; box-shadow: 0 4px 10px rgba(0,0,0,0.5);"/></p>

### 5️⃣ Multi-Agent Configuration Panel
**Features:** The cockpit for your AI team. Define the overarching business goal (e.g., "Maximize user retention"), select the target feature column, and hit run.
<p align="center"><img src="assets/Screenshots/5.DATA%20ANALYSIS.png" alt="Data Analysis" width="90%" style="border-radius:8px; border:2px solid #2d2d2d; box-shadow: 0 4px 10px rgba(0,0,0,0.5);"/></p>

### 6️⃣ Live Agentic Processing (Terminal View)
**Features:** Total transparency. Watch the agents converse, write Python code, debug errors, and synthesize data in real-time. This ensures trust and verifiability in the AI's methodology.
<p align="center"><img src="assets/Screenshots/6.ANALYSING.png" alt="Analysing" width="90%" style="border-radius:8px; border:2px solid #2d2d2d; box-shadow: 0 4px 10px rgba(0,0,0,0.5);"/></p>

### 7️⃣ Executive Business Insights Dashboard
**Features:** The magnum opus of the platform. The UI splits findings into three hyper-readable columns: **Observation** (The stat), **Business Implication** (Why it matters), and **Actionable Strategy** (What you should do today).
<p align="center"><img src="assets/Screenshots/7.BUSINESS%20INSIGHTS.png" alt="Business Insights" width="90%" style="border-radius:8px; border:2px solid #2d2d2d; box-shadow: 0 4px 10px rgba(0,0,0,0.5);"/></p>

### 8️⃣ Natively Embedded Visualizations
**Features:** Interactive, dark-mode optimized Plotly charts generated to back up the strategic claims made by the AI. Hover over data points for exact values.
<p align="center"><img src="assets/Screenshots/8.VISUALIZATION.png" alt="Visualization" width="90%" style="border-radius:8px; border:2px solid #2d2d2d; box-shadow: 0 4px 10px rgba(0,0,0,0.5);"/></p>

---

## 📊 Deliverables: Reports & Visualizations

Crewlyze ensures that the final mile of data analysis—the presentation—is handled with utmost professionalism.

### 📥 The Executive PDF Report
At the click of a button, Crewlyze aggregates the insights, renders the interactive Plotly graphs into high-resolution PNGs, and packages them into a stunning PDF document. 
*   **Dynamic Conclusions:** The conclusion is not boiler-plate; it dynamically references the most critical business risk discovered during the run.
*   **Branded Styling:** Includes headers, footers, pagination, and color-coded risk alerts.

🎯 **[Click Here to View the Example Executive Report PDF](assets/Screenshots/EXAMPLE%20REPORT.pdf)**

### 💾 Data Artifacts
*   **`cleaned_dataset.csv`**: Download the mathematically imputed and sanitized version of your dataset.
*   **`execution_trace.json`**: Download the complete LLM token trace for compliance and auditing purposes.

---

## 🏢 Industry Use Cases & ROI

Crewlyze is designed to be highly versatile across sectors.

| Industry Sector | Example Dataset | How Crewlyze Transforms the Workflow | Projected ROI |
| :--- | :--- | :--- | :--- |
| 🏥 **Healthcare & Pharma** | Patient clinical trials, vitals logs. | Secure, local analysis of patient outcomes. Agents identify correlations between drug dosage and recovery times without exposing PII to the cloud. | Saves months of manual biostatistical coding. |
| 📈 **Finance & FinTech** | Ledger exports, stock price histories, transaction logs. | The Strategic Agent flags anomalies in transaction frequency, identifying potential fraud or optimizing portfolio rebalancing rules. | Drastic reduction in risk exposure and manual audit hours. |
| 🛒 **E-Commerce & Retail** | Shopify/Amazon sales exports, customer churn data. | Instantly maps which demographic segments are driving the highest Customer Lifetime Value (CLV) and suggests targeted ad spend shifts. | Direct increase in ROAS (Return on Ad Spend). |
| 🏭 **Manufacturing & Supply Chain** | Sensor IoT data, logistics timetables. | Profiles massive datasets to find failure thresholds in machinery, enabling preventative maintenance strategies. | Prevents costly factory downtime. |

---

## 📂 Project Structure & API Routes

For developers looking to understand the inner workings:

```text
Crewlyze/
├── main.py                 # FastAPI core, route definitions, SSE streaming logic
├── crew.py                 # CrewAI orchestration, agent definitions, and task routing
├── requirements.txt        # Python dependency manifest
├── package.json            # NPM configuration for global installation
├── README.md               # You are here
├── config/                 # YAML configurations for prompts, roles, and settings
├── tools/                  # Python sandboxing tools (dataset_tools.py)
├── ui/                     # PDF Generation scripts (export.py) using ReportLab
├── web/                    # 100% Vanilla Frontend (HTML, CSS, JS)
│   ├── index.html          # Main SPA Entrypoint
│   ├── style.css           # Glassmorphism design system
│   └── app.js              # State management and DOM routing
└── assets/                 # Branding and Documentation Screenshots
```

### 🔌 Core API Routes
*   `POST /api/upload`: Handles multipart form data for initial CSV ingestion.
*   `GET /api/stream`: Opens a Server-Sent Events (SSE) connection for real-time terminal logs.
*   `POST /api/analyze`: Triggers the async `crew.py` background task.
*   `POST /api/chat`: Handles conversational queries against the dataset context.
*   `GET /api/download_pdf`: Assembles and returns the binary PDF stream.

---

## 🛣️ Roadmap & Future Scope

Crewlyze is actively maintained. Here is our vision for the next 12-18 months:

<details>
<summary><strong>🚀 Phase 1: Current State (v1.0)</strong></summary>
<br>
- Complete CSV/Excel processing <br>
- Multi-Agent Orchestration via CrewAI <br>
- LiteLLM Multi-Provider Support <br>
- PDF Export & Plotly Integration
</details>

<details>
<summary><strong>🌐 Phase 2: Database Integration (v2.0) - Q3 2026</strong></summary>
<br>
- Direct native connections to PostgreSQL, MySQL, and Snowflake. <br>
- Autonomous SQL Query Generation agents. <br>
- Multi-table join analysis.
</details>

<details>
<summary><strong>🧠 Phase 3: RAG & Enterprise Memory (v3.0) - Q1 2027</strong></summary>
<br>
- Retrieval-Augmented Generation (RAG): Upload company PDFs and wikis so the AI contextualizes data insights based on company history. <br>
- Webhook CRON scheduling: Automatically run weekly reports on live databases and email the PDF to executives.
</details>

---

## 🛠️ Comprehensive Troubleshooting

Encountering an issue? Check our detailed solutions below:

<details>
<summary><strong>🔴 Issue: The AI fails to generate Plotly charts or outputs invalid Python code.</strong></summary>
<br>
**Solution:** Code generation requires high-tier reasoning capabilities. <br>
1. Ensure you are using a flagship model like `gpt-4o`, `claude-3-5-sonnet`, or `gemini-1.5-pro`. <br>
2. If using Ollama, ensure you are using at least `llama3:8b` or `qwen2.5:14b`. Smaller 7B models often hallucinate syntax errors. <br>
3. Check the terminal logs for exact Python tracebacks.
</details>

<details>
<summary><strong>🔴 Issue: CORS Errors in the Browser Console.</strong></summary>
<br>
**Solution:** By default, FastAPI `main.py` binds to `localhost:8000` and allows origins for `127.0.0.1` and `localhost`. If you are hosting the backend on a remote server (e.g., an AWS EC2 instance), you must update the `CORSMiddleware` in `main.py` to allow your specific frontend domain.
</details>

<details>
<summary><strong>🔴 Issue: Uploading large CSVs (1GB+) crashes the browser.</strong></summary>
<br>
**Solution:** Crewlyze currently parses data into memory using Pandas. For massive datasets, consider pre-filtering your data, or increase your system's swap memory. Future updates will incorporate Dask/Polars for out-of-core processing.
</details>

---

## 🤝 Contributing & Development

Crewlyze thrives on open-source collaboration! Whether you are fixing typos, designing better CSS, or writing advanced CrewAI prompt templates, your help is welcome.

1. **Fork the Repository** on GitHub.
2. **Clone your Fork** locally.
3. **Create a Feature Branch:** `git checkout -b feature/AmazingNewFeature`
4. **Commit your Changes:** `git commit -m 'Add AmazingNewFeature'`
5. **Push to the Branch:** `git push origin feature/AmazingNewFeature`
6. **Open a Pull Request** against the main `Multi-Agent-Data-Analysis-System-with-CrewAI` repository.

> **Note:** Please ensure all Python code passes standard `flake8` linting and that no sensitive API keys are accidentally committed!

---

## 👥 Meet the Team & Contributors

A massive thank you to the brilliant minds building the future of autonomous data analysis. 

### ✨ Core Contributors

<p align="center">
  <a href="https://github.com/sowmiyan-s/Multi-Agent-Data-Analysis-System-with-CrewAI/graphs/contributors">
    <img src="https://contrib.rocks/image?repo=sowmiyan-s/Multi-Agent-Data-Analysis-System-with-CrewAI" alt="Contributors" />
  </a>
</p>

*   👨‍💻 **Sowmiyan S** - *Lead Architect & Creator*
*   👨‍💻 **Prithiv A.K** - *Core Contributor*
*   👨‍💻 **Sebin S** - *Core Contributor*

---

## 💖 Sponsorship & Support

If Crewlyze has saved you or your enterprise countless hours of manual data labor, please consider supporting the project. Open-source development requires massive amounts of coffee, API testing credits, and server hosting!

Your sponsorship directly funds the development of v2.0 (Database Integrations) and ensures the project remains free and open forever.

<div align="center">
  <a href="https://github.com/sowmiyan-s/">
    <img src="https://img.shields.io/badge/Sponsor_This_Project_on_GitHub-%E2%9D%A4-ff69b4?style=for-the-badge&logo=github" alt="Sponsor on GitHub" width="300">
  </a>
</div>

<br>

**Follow the Creator:**
*   🌐 **GitHub:** [@sowmiyan-s](https://github.com/sowmiyan-s)
*   💼 **LinkedIn:** [Sowmiyan S](https://linkedin.com/in/sowmiyan-s/)

---

## 📜 License & Legal

*Crewlyze* is proudly open-sourced software licensed under the **[MIT License](https://opensource.org/licenses/MIT)**. You are free to use, modify, and distribute this software in both commercial and non-commercial settings.

Copyright © 2025 Sowmiyan S.

> **Disclaimer:** *Always ensure you comply with your organization's internal data privacy policies and GDPR/HIPAA regulations when uploading sensitive datasets to cloud LLM providers (OpenAI, Google, Anthropic). For maximum security with confidential data, strictly utilize local Ollama instances.*
