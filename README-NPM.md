# Crewlyze

Autonomous Multi-Agent Business Intelligence & Data Engineering Platform.

Crewlyze orchestrates a team of specialized AI agents (powered by CrewAI, FastAPI, and your choice of LLM provider) to clean datasets, map statistical relationships, generate beautiful visual charts, and produce executive-level business strategies.

## Features
* **AI Chat Copilot**: Ask questions about your dataset, plot new graphs, and clean columns using simple words.
* **Autonomous Pipeline**: Triggers a five-stage multi-agent pipeline: Data Profiler, Cleaner, Statistician, Visualizer, and Strategy Director.
* **Premium Dashboard**: Built-in interactive Plotly charts, data preview tables, and an execution stages progress bar.
* **LLM Agnostic**: Supports OpenAI, Anthropic, Gemini, NVIDIA NIM, Groq, Ollama, and more.

## Requirements
* **Node.js** (v16+)
* **Python** (v3.10 - v3.12 recommended)
* *The installation script will automatically set up a Python virtual environment and download the necessary libraries.*

## Installation

Install Crewlyze globally via npm:

```bash
npm install -g crewlyze
```

## Quick Start

Launch the platform:

```bash
crewlyze
```

This starts the local FastAPI server and automatically opens the dashboard at [http://127.0.0.1:8000](http://127.0.0.1:8000).

## License
MIT © Sowmiyan S
