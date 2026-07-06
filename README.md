---
title: Crewlyze
emoji: 📊
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
---
# Crewlyze

<p align="center">
  <img src="assets/branding_image.png" alt="Transform Raw Datasets Into Insights With Agentic AI Analysts" width="100%" />
</p>
<p align="center">
  <img src="assets/stars.svg" alt="5-star rating" height="28" />
  &nbsp;&nbsp;
  <img src="assets/badge_crewai.svg" alt="crewai" height="28" />
  <img src="assets/badge_pandas.svg" alt="pandas" height="28" />
  <img src="assets/badge_matplotlib.svg" alt="matplotlib" height="28" />
  <img src="assets/badge_seaborn.svg" alt="seaborn" height="28" />
  <img src="assets/badge_ollama.svg" alt="ollama" height="28" />
</p>
<p align="center">
  <a href="https://render.com/deploy?repo=https://github.com/your-username/Multi-Agent-Data-Analysis-System-with-CrewAI">
    <img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Render">
  </a>
</p>


## Overview

> **Autonomous Data Intelligence as a Service** | A premium, modular data-analyst pipeline powered by LLM-driven agents. Upload a CSV to initialize a workspace, chat with your dataset in real-time, execute custom schema modifications via natural language, and run a complete multi-agent pipeline to generate structured audits, correlation maps, and executive business summaries.

- 📖 **[Read the Workflow Guide](WORKFLOW.md)** for details on the AI pipelines and chat systems.
- 🏗️ **[Read the Architecture Guide](ARCHITECTURE.md)** for details on the tech stack and project structure.

---

## 🛠️ Installation & Setup

You can easily install Crewlyze globally via `npm`. The installation process will automatically configure a dedicated Python environment for the backend!

1. **Install Crewlyze via NPM**:
   ```bash
   npm install crewlyze
   ```
   *(Note: The postinstall script will automatically elevate this to a global installation and install all Python requirements, so you don't even need the `-g` flag!)*

2. **Launch the Platform**:
   ```bash
   crewlyze
   ```
   This will start the FastAPI backend and automatically provide a link to the web interface.

3. **Open Browser**:
   Navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000)


## Alternative Installation (Manual / Git)

1. **Clone & Navigate**:
   ```bash
   git clone https://github.com/your-username/Multi-Agent-Data-Analysis-System-with-CrewAI.git
   cd Multi-Agent-Data-Analysis-System-with-CrewAI
   ```

2. **Run with Docker (Recommended for Enterprise/Cloud)**:
   ```bash
   docker-compose up --build
   ```

3. **Run Python Setup & Launch (Local)**:
   ```bash
   npm install
   npm start
   ```

---

*Crewlyze*  
*Copyright (c) 2025 Sowmiyan S*  
*Licensed under the MIT License*
