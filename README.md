# Crewlyze — GitHub Repository

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Welcome to the **Crewlyze** source repository! This project hosts the codebase for an autonomous multi-agent data analysis platform built with FastAPI, CrewAI, and a Vanilla JS web interface.

<p align="center">
  <img src="assets/branding_image.png" alt="Transform Raw Datasets Into Insights With Agentic AI Analysts" width="100%" />
</p>

## Project Structure
* `main.py` - Main FastAPI application serving the API endpoints and hosting the custom UI.
* `crew.py` - Setup of CrewAI agents, tasks, and parallel thread runner logic.
* `web/` - SPA Frontend assets (index.html, style.css, app.js).
* `tools/` - Custom data engineering tools (cleaning, visualization code runner).
* `config/` - Context isolation variables, LLM parameters, and metric tracking.
* `workflows/` - Parallel agent pipeline execution engine.
* `bin/` - Global CLI package executables and installation scripts.

---

## 🛠️ Local Development & Setup

### Option 1: Run via Docker (Recommended)
This launches both the web platform and handles all dependencies inside a containerized workspace.
```bash
docker-compose up --build
```
Navigate to [http://localhost:8000](http://localhost:8000)

### Option 2: Run via NPM (Global CLI Mode)
Install globally and execute:
```bash
npm install -g .
crewlyze
```

### Option 3: Manual Startup
1. **Prepare Virtual Environment & Dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Start FastAPI Backend**:
   ```bash
   python main.py
   ```
3. **Open SPA UI**:
   Navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 📖 Related Guides
* 🗺️ **[Architecture Guide](ARCHITECTURE.md)**: Design system, security patches, and thread-isolation configurations.
* 📋 **[Workflow Guide](WORKFLOW.md)**: Details on the 5 stages of the multi-agent pipeline and how inputs are routed.
* 💡 **[Usage Instructions](USAGE.md)**: Detailed API references and dashboard configurations.

---

*Crewlyze*  
*Copyright (c) 2025 Sowmiyan S*  
*Licensed under the MIT License*
