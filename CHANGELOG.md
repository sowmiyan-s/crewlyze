# Changelog

All notable changes to the Multi Agent Data Analysis with Crew AI project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2026-06-27

### Architecture Refactor
- **Modular UI Package**: Extracted all Streamlit UI logic from `app.py` into a dedicated `ui/` package:
    - `ui/styles.py` — CSS injection (glassmorphism "Obsidian & Electric Violet" theme)
    - `ui/components.py` — `display_text_as_bullets`, `display_relations`, `StreamlitLogger` (module-level, not inline)
    - `ui/export.py` — ReportLab PDF builder, wrapped with `@st.cache_data`
- **Security — Subprocess Sandboxing**: All LLM-generated Python code (cleaning and visualization) now runs in an isolated child process via `subprocess.run()`. `exec()` is never called in the parent process, eliminating RCE risk.
- **Per-session File Isolation**: Each browser session gets its own `data/sessions/<id>/` and `outputs/<id>/` directories. No cross-session data leakage.
- **Content-hashed Caching**: Analysis results and PDF exports are cached by MD5 of the uploaded file content, not the filename. Re-uploading the same file never triggers a redundant re-run.
- **XSS-safe Output**: All LLM-generated text is `html.escape()`'d before injection into `unsafe_allow_html` markdown blocks.

### Improvements
- **Explicit Run Button**: Analysis no longer fires automatically on upload. Users configure the LLM provider in the sidebar and then click **▶️ Run Analysis**.
- **Numbered List Regex**: Bullet stripping now uses `re.sub(r"^[\d]+\.\s+", "", line)` — handles all numbered items (N.), not just 1–3.
- **LLM Config Isolation**: Provider/model/API key are stored in `st.session_state` and only written to `os.environ` immediately before `run_crew()` is invoked.
- **Agent Factory Pattern**: All agent factories (`make_cleaner_agent`, etc.) are called fresh on every `run_crew()` invocation, picking up the latest sidebar config without requiring `importlib.reload()`.
- **Session Cleanup**: `_cleanup_old_sessions()` automatically removes session directories older than 24 hours on every run.

### Fixed
- **Session Isolation Bug**: `execute_visualization_code` tool no longer creates a root-level `outputs/` directory, which previously bypassed per-session isolation.
- **Stale Cached PDF**: PDF export is now `@st.cache_data` wrapped with a content-hash key — it is never rebuilt on every Streamlit rerender.
- **Unicode Crash**: `StreamlitLogger.write()` re-encodes through the terminal's actual encoding with `errors='replace'`, preventing `UnicodeEncodeError` on Windows cp1252 terminals.

### Removed
- `validator.py` (merged into cleaner agent's responsibility)
- `code_gen.py` (replaced by inline visualization task in `visualizer.py`)
- `index.html` report output (replaced by the interactive Streamlit dashboard)
- `outputs/op.py` collected code output (agent code is shown in "Visualization Architecture" section)

## [2.1.0] - 2025-11-27

### UI Overhaul
- **Premium Design**: Introduced a new "Obsidian & Electric Violet" theme with glassmorphism effects.
- **Single-Page Layout**: Removed sidebar navigation for a seamless, scrolling experience.
- **Enhanced Components**:
    - Redesigned "Column Relations" display with visual cards.
    - Styled bullet points for cleaner readability.
    - Modern typography using 'Outfit' and 'JetBrains Mono'.
- **Interactive Sidebar**: Redesigned configuration panel and "About" section with GitHub integration.

### Improvements
- **Robustness**: Improved error handling for LLM API calls and visualization generation.
- **Consistency**: Unified styling for both live analysis results and cached sessions.


## [2.0.0] - 2025-11-26

### Major Features
- **Data Analysis as a Service**: Rebranded and restructured for premium service delivery.
- **Enhanced Validator Agent**: Now acts as a "Data Quality Assurance Specialist" providing detailed quality scores (0-100), decision logic, and specific warnings.
- **Business Intelligence Agent**: Upgraded Insights Agent to a "Business Intelligence Analyst" role, focusing on synthesizing findings from cleaning, validation, and relation tasks.
- **Token Optimization**: Significantly reduced token usage by removing dynamic data context injection and optimizing agent prompts.
- **Professional Reporting**: Updated `index.html` with a modern, dark-themed UI, visual scorecards for data quality, and structured insight presentation.

### Changed
- **Project Branding**: Renamed to "Multi Agent Data Analysis with Crew AI".
- **Agent Roles**: 
    - Validator: Dataset Validator -> Data Quality Assurance Specialist
    - Insights: Insights Agent -> Business Intelligence Analyst
- **Workflow**: Streamlined pipeline to use static task definitions for better efficiency.
- **Licensing**: Added MIT License and copyright headers to all source files.

### Fixed
- **Rate Limit Issues**: Optimized prompts and removed heavy context to prevent LLM rate limit errors.
- **Task Conflicts**: Resolved overlapping task descriptions between Validator and Insights agents.

## [1.0.0] - 2023-10-XX

### Added
- Initial release of CrewAI Data Analyst Agent
- Modular agent system with cleaner, validator, relation, code_gen, and insights agents
- Automated CSV processing and analysis pipeline
- HTML report generation with interactive elements
- LLM integration via Ollama backend

---

**Status**: ✅ Working | 🚀 Production Ready | 📊 Data Analysis as a Service
