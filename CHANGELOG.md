# Changelog

All notable changes to the Multi Agent Data Analysis with Crew AI project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
