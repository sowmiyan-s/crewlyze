# Crewlyze Workflow

<p align="center">
  <img src="assets/complete_workflow.svg" alt="Crewlyze Workflow" width="100%" />
</p>

## Overview
Once a project is initialized, the system branches into two distinct, high-impact paths:

### Track A: AI Data Chat (Interactive Exploration)
- **Natural Language Querying**: Query your dataset directly to get condition-based rows, statistics, or aggregations.
- **On-the-Fly Data Prep**: Ask the copilot to perform edits in-place, such as `Rename column "Q3_Sales" to "Sales_Q3"` or `Delete column "Notes"`, and watch the live data preview table update dynamically.
- **Instant Visualizations**: Command the chat bot to create custom charts (e.g. *"plot a neon-purple scatter chart of rating vs cost"*). It writes and runs the matplotlib code in a sandboxed subprocess to output charts inline.

### Track B: Agentic Analysis (CrewAI Pipeline)
Select and run specific automated tasks through the multi-agent pipeline:
1. **Data Cleaner (🧹)**: Audits columns, formats values, drops redundant rows, and generates a structured cleaning audit trail.
2. **Relationship Mapper (🔗)**: Maps numeric and categorical variables, rendering zoomable, interactive **Plotly** correlation charts.
3. **Business Insights (💡)**: Analyzes statistical summaries and generates easily readable Observation ➔ Implication ➔ Strategy cards alongside critical risk alerts.
4. **Visualizer Agent (📈)**: Automatically creates, styles, and saves formatted matplotlib PNG graphs.

## Pipeline Orchestration
The pipeline is orchestrated dynamically per user session, injecting current data profiles and metadata into the context of each agent. Agents can also auto-heal errors and dynamically retry sandboxed python scripts if execution fails.
