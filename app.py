# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Streamlit entry point — Agentic Data Analyst.

Improvements in this version:
- Smart task-selection cards (with enforced dependency logic)
- Data preview expander (collapsible / expandable)
- Persistent side-panel chat (visible as soon as a file is uploaded)
- /column slash command in chat for column-aware queries
- Visualization Architecture code moved into the Visual tab
- Interactive Plotly charts with titles and error guards
- Improved PDF export with data insights (min/max/avg)
"""

import contextlib
import hashlib
import os
import sys
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st

from crew import run_crew
from tools.dataset_tools import read_csv_robust
from tools.ui.styles import inject_styles
from tools.ui.components import display_mckinsey_insights, display_cleaning_timeline, display_relations, StreamlitLogger
from tools.ui.export import export_pdf_cached

# Disable CrewAI Telemetry
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"]        = "true"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Agentic Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()


# ── Session initialisation ────────────────────────────────────────────────────

def _init_session() -> None:
    defaults = {
        "session_id":       uuid.uuid4().hex[:12],
        "llm_provider":     os.getenv("LLM_PROVIDER", "nvidia"),
        "llm_model":        "",
        "api_key":          "",
        "preview_expanded": True,
        "copilot_messages": [],
        "col_insert":       "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Sidebar ───────────────────────────────────────────────────────────────────

def _render_sidebar() -> dict:
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        st.markdown("### LLM Settings")

        model_options = {
            "nvidia":      [
                "nvidia_nim/meta/llama-3.1-8b-instruct",
                "nvidia_nim/meta/llama-3.1-70b-instruct",
                "nvidia_nim/nvidia/mistral-nemo-minitron-8b-8k-instruct",
                "nvidia_nim/mistralai/mistral-large-2407",
            ],
            "minimax":     ["minimaxai/minimax-m3"],
            "groq":        ["groq/llama-3.1-8b-instant", "groq/llama-3.3-70b-versatile", "groq/mixtral-8x7b-32768", "groq/gemma2-9b-it"],
            "openai":      ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "anthropic":   ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            "huggingface": ["huggingface/HuggingFaceH4/zephyr-7b-beta", "huggingface/meta-llama/Llama-2-7b-chat-hf"],
            "mistral":     ["mistral/mistral-tiny", "mistral/mistral-small", "mistral/mistral-medium", "mistral/mistral-large-latest"],
            "gemini":      ["gemini/gemini-pro", "gemini/gemini-1.5-pro", "gemini/gemini-1.5-flash"],
            "ollama":      ["ollama/llama3", "ollama/mistral", "ollama/gemma2"],
        }

        provider = st.selectbox(
            "Select Provider",
            list(model_options.keys()),
            index=list(model_options.keys()).index(
                st.session_state.get("llm_provider", "nvidia")
            ),
        )
        st.session_state["llm_provider"] = provider

        override_model = st.checkbox("Custom Model Name", value=False)
        if override_model:
            selected_model = st.text_input(
                "Model Identifier",
                value=st.session_state.get("llm_model") or model_options.get(provider, [""])[0],
            )
        else:
            selected_model = st.selectbox("Select Model", model_options.get(provider, []), index=0)
        st.session_state["llm_model"] = selected_model

        if provider == "ollama":
            env_key_name = "OLLAMA_BASE_URL"
            default_key  = st.session_state.get("api_key") or os.getenv(env_key_name, "http://localhost:11434")
        elif provider in ("nvidia", "minimax"):
            env_key_name = "NVIDIA_API_KEY"
            default_key  = st.session_state.get("api_key") or os.getenv(env_key_name, "")
        else:
            env_key_name = f"{provider.upper()}_API_KEY"
            default_key  = st.session_state.get("api_key") or os.getenv(env_key_name, "")

        api_key = st.text_input(
            f"{provider.upper()} API Key" if provider != "ollama" else "Ollama Base URL",
            value=default_key,
            type="password" if provider != "ollama" else "default",
        )
        st.session_state["api_key"] = api_key

        default_cooldown = 0 if provider == "ollama" else int(os.getenv("API_COOLDOWN", "5"))
        cooldown = st.slider("API Cooldown (s)", 0, 60, default_cooldown)
        st.session_state["api_cooldown"] = cooldown

        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown(
            """
            <div style="background-color:#171717;padding:15px;border-radius:8px;border:1px solid #262626;">
                <p style="margin:0;font-size:0.9em;color:#a3a3a3;">
                    <b>Agentic Data Analyst</b><br>
                    Powered by CrewAI · automates data cleaning, analysis &amp; visualization.
                </p>
                <hr style="border-color:#262626;margin:10px 0;">
                <p style="margin:0;font-size:0.8em;color:#737373;">
                    Developed by:<br>• Prithiv.A.K<br>• Sebin.S<br>• Sowmiyan.S
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return {
        "provider":     provider,
        "model":        selected_model,
        "api_key":      api_key,
        "cooldown":     cooldown,
        "env_key_name": env_key_name,
    }


def _apply_env(cfg: dict) -> None:
    if cfg["api_key"]:
        os.environ[cfg["env_key_name"]] = cfg["api_key"]
    os.environ["LLM_PROVIDER"] = cfg["provider"]
    os.environ["LLM_MODEL"]    = cfg["model"]
    os.environ["API_COOLDOWN"] = str(cfg["cooldown"])


# ── Smart Task Selection UI ───────────────────────────────────────────────────

def _render_task_selector() -> tuple[list[str], bool]:
    """
    Render smart task-selection cards with enforced dependency logic.
    Returns (selected_tasks, deep_analysis).
    """
    st.markdown("### 🎛️ Analysis Configuration")
    st.caption("Select which stages to run. Dependency rules are enforced automatically.")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        do_clean = st.checkbox(
            "🧹 Data Cleaning",
            value=True,
            help="Detect and fix data quality issues (missing values, type errors, duplicates).",
        )

    with col2:
        do_relations = st.checkbox(
            "🔗 Relationship Analysis",
            value=do_clean,
            disabled=not do_clean,
            help="Identify significant correlations and patterns between columns.\n⚠️ Requires Cleaning.",
        )

    with col3:
        do_insights = st.checkbox(
            "💡 Business Insights",
            value=do_clean,
            disabled=not do_clean,
            help="Generate executive-level strategic recommendations.\n⚠️ Requires Cleaning.",
        )

    with col4:
        do_viz = st.checkbox(
            "📈 Visualization",
            value=do_relations,
            disabled=not do_relations,
            help="Create interactive Plotly charts and static PNG plots.\n⚠️ Requires Relationship Analysis.",
        )

    # Quality radio (replaces the deep-analysis checkbox)
    st.markdown("")
    quality = st.radio(
        "🔬 Analysis Depth",
        options=["⚡ Standard — faster, concise output", "🔭 Deep — richer reasoning & detail"],
        index=0,
        horizontal=True,
    )
    deep_analysis = "Deep" in quality

    selected_tasks = []
    if do_clean:     selected_tasks.append("cleaning")
    if do_relations: selected_tasks.append("relations")
    if do_insights:  selected_tasks.append("insights")
    if do_viz:       selected_tasks.append("visualization")

    return selected_tasks, deep_analysis


# ── Chat panel ────────────────────────────────────────────────────────────────

def _render_chat_panel(csv_path: str, output_dir: str, columns: list[str]) -> None:
    """
    Render the AI Data Copilot chat panel.
    Supports /column slash command for column-aware queries.
    """
    st.markdown("### 💬 AI Data Copilot")
    st.caption("Ask questions about your dataset in plain English. Use `/` to insert a column name.")

    # ── /column picker ────────────────────────────────────────────────────────
    if columns:
        col_pick, _ = st.columns([1, 3])
        with col_pick:
            chosen_col = st.selectbox(
                "📌 Insert column →",
                ["(none)"] + columns,
                key="col_picker_select",
                label_visibility="collapsed",
            )
        if chosen_col != "(none)":
            # Append column name to pending query text
            current = st.session_state.get("pending_query", "")
            st.session_state["pending_query"] = (current + f" `{chosen_col}`").lstrip()
            # Reset picker
            st.session_state["col_picker_select"] = "(none)"

    # ── Display history ───────────────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state["copilot_messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("plot_path") and Path(msg["plot_path"]).exists():
                    st.image(msg["plot_path"], use_container_width=True)

    # ── Input ─────────────────────────────────────────────────────────────────
    prefill = st.session_state.pop("pending_query", "")
    prompt  = st.chat_input(
        "Query your dataset (e.g. 'Show average Sales by Region', 'Plot Age vs Income')",
        key="copilot_input",
    ) or prefill

    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state["copilot_messages"].append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Analysing…"):
                from tools.ui.copilot import run_copilot_query
                res = run_copilot_query(prompt, csv_path, output_dir)

            st.markdown(res["text"])
            if res.get("plot_path") and Path(res["plot_path"]).exists():
                st.image(res["plot_path"], use_container_width=True)

            st.session_state["copilot_messages"].append({
                "role":      "assistant",
                "content":   res["text"],
                "plot_path": res.get("plot_path"),
            })


# ── Results display ───────────────────────────────────────────────────────────

def _render_results(result: dict, filename: str = "") -> None:
    st.success("### ✅ Analysis Complete!")
    st.markdown("## 📊 Executive Dashboard")

    df = result["dataframe"]

    st.markdown(
        f"""
        <div class="stat-container">
            <div class="stat-card">
                <div class="stat-val">{df.shape[0]:,}</div>
                <div class="stat-lbl">Total Records</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{df.shape[1]}</div>
                <div class="stat-lbl">Total Columns</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{len(df.select_dtypes(include=["number"]).columns)}</div>
                <div class="stat-lbl">Numeric Fields</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{len(df.select_dtypes(include=["object"]).columns)}</div>
                <div class="stat-lbl">Categorical Fields</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_preview, tab_cleaning, tab_relations, tab_insights, tab_plots = st.tabs([
        "🔍 Data Preview",
        "🧹 Clean Report",
        "🔗 Relations Map",
        "💡 Key Insights",
        "📈 Visual Intelligence",
    ])

    # ── Data Preview (collapsible) ────────────────────────────────────────────
    with tab_preview:
        n_rows, n_cols = df.shape
        expanded_key   = "preview_tab_expanded"
        if expanded_key not in st.session_state:
            st.session_state[expanded_key] = True

        toggle_label = "🔽 Minimize Preview" if st.session_state[expanded_key] else "🔼 Expand Preview"
        if st.button(toggle_label, key="preview_toggle_btn"):
            st.session_state[expanded_key] = not st.session_state[expanded_key]

        if st.session_state[expanded_key]:
            st.caption(f"Showing up to 100 rows · {n_rows:,} total rows · {n_cols} columns")
            st.dataframe(df.head(100), use_container_width=True)
        else:
            st.info(f"Preview minimized — {n_rows:,} rows × {n_cols} columns. Click 'Expand Preview' to show.")

    with tab_cleaning:
        st.markdown("### 🧹 Data Cleaning Operations")
        display_cleaning_timeline(result["cleaning_steps"])

    with tab_relations:
        st.markdown("### 🔗 Column Relationships")
        display_relations(result["relations"])

    with tab_insights:
        st.markdown("### 💡 Business Intelligence Insights")
        display_mckinsey_insights(result["insights"])

    # ── Visual Intelligence tab ───────────────────────────────────────────────
    with tab_plots:
        st.markdown("### 📈 Visual Intelligence")

        # Interactive Plotly charts
        plotly_charts = result.get("plotly_charts", [])
        if plotly_charts:
            st.markdown("#### 🎯 Interactive Charts")
            st.caption("Zoom, pan, hover for details. Charts generated from identified relationships.")
            for chart in plotly_charts:
                try:
                    fig   = chart.get("fig")
                    title = chart.get("title", "Chart")
                    if fig is None:
                        st.warning(f"Chart '{title}' has no figure object.")
                        continue
                    st.markdown(f"**{title}**")
                    st.plotly_chart(fig, use_container_width=True, key=f"plotly_{title}_{id(fig)}")
                except Exception as exc:
                    st.error(f"Could not render chart '{chart.get('title', '?')}': {exc}")
            st.markdown("---")
        else:
            st.info("No interactive charts available. Make sure 'Relationship Analysis' was selected.")

        # Agent-generated static PNGs
        output_dir = Path(result.get("output_dir", "outputs"))
        png_files  = sorted(output_dir.glob("*.png"))
        if png_files:
            st.markdown("#### 🖼️ Agent-Generated Visualizations")
            for png_file in png_files:
                st.image(str(png_file), caption=png_file.stem, use_container_width=True)


    # ── Export options ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📥 Export Options")
    c1, c2 = st.columns(2)

    with c1:
        try:
            cache_key = hashlib.md5(
                (result["cleaning_steps"] + result["relations"] + result["insights"]).encode()
            ).hexdigest()
            pdf_bytes = export_pdf_cached(
                cache_key        = cache_key,
                filename         = filename,
                result_cleaning  = result["cleaning_steps"],
                result_relations = result["relations"],
                result_insights  = result["insights"],
                result_code      = result.get("code", ""),
                output_dir_str   = result.get("output_dir", "outputs"),
                df_csv           = result["dataframe"].to_csv(index=False),
            )
            st.download_button(
                label="📄 Export Full Report as PDF",
                data=pdf_bytes,
                file_name="data_analysis_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Error preparing PDF: {e}")

    with c2:
        csv_bytes = result["dataframe"].to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Cleaned Dataset (CSV)",
            data=csv_bytes,
            file_name="cleaned_dataset.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    _init_session()
    cfg = _render_sidebar()

    st.markdown("<h1 class='main-title'>Agentic Data Analyst</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#94a3b8;font-size:1.15rem;margin-bottom:2rem;'>"
        "Autonomous Multi-Agent Business Intelligence and Data Engineering System</p>",
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader("Upload your CSV dataset", type=["csv"])

    if uploaded_file is None:
        return

    # ── Save uploaded file ────────────────────────────────────────────────────
    data_dir  = Path("data")
    data_dir.mkdir(exist_ok=True)
    file_path = data_dir / uploaded_file.name

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Cache key: MD5 of file content
    file_hash  = hashlib.md5(uploaded_file.getvalue()).hexdigest()
    cache_key  = f"result_{file_hash}"
    session_id = st.session_state["session_id"]

    # CSV path used by agents and copilot
    session_csv = f"data/sessions/{session_id}/cleaned.csv"

    # Use original upload path as fallback if session copy doesn't exist yet
    copilot_csv = session_csv if Path(session_csv).exists() else str(file_path)

    # Load preview data
    df_preview = read_csv_robust(file_path, nrows=200)
    columns    = list(df_preview.columns)

    st.success(f"✅ File uploaded: **{uploaded_file.name}** ({uploaded_file.size:,} bytes)")

    # ── Collapsible Data Preview ──────────────────────────────────────────────
    preview_key = f"preview_expanded_{file_hash}"
    if preview_key not in st.session_state:
        st.session_state[preview_key] = cache_key not in st.session_state  # start expanded on new file

    toggle = "🔽 Minimize Preview" if st.session_state[preview_key] else "🔼 Show Data Preview"
    if st.button(toggle, key=f"preview_toggle_{file_hash}"):
        st.session_state[preview_key] = not st.session_state[preview_key]

    if st.session_state[preview_key]:
        with st.container():
            st.caption(f"{len(df_preview):,} rows (preview) · {len(columns)} columns")
            st.dataframe(df_preview.head(), use_container_width=True)

    st.markdown("---")

    # ── Split layout: analysis (left 2/3) + chat (right 1/3) ─────────────────
    main_col, chat_col = st.columns([2, 1])

    with chat_col:
        output_dir_for_chat = (
            result["output_dir"]
            if (cache_key in st.session_state and isinstance(st.session_state[cache_key], dict))
            else f"outputs/{session_id}"
        )
        _render_chat_panel(copilot_csv, output_dir_for_chat, columns)

    with main_col:
        # ── Show cached results ───────────────────────────────────────────────
        if cache_key in st.session_state:
            result = st.session_state[cache_key]
            _render_results(result, filename=uploaded_file.name)
            if st.button("🔄 Re-run Analysis", use_container_width=True):
                del st.session_state[cache_key]
                st.rerun()
            return

        # ── Task selection + Run ──────────────────────────────────────────────
        selected_tasks, deep_analysis = _render_task_selector()

        st.markdown("---")
        st.markdown("### 🤖 Ready to Analyse")
        if not st.button("▶️ Run Analysis", use_container_width=True, type="primary"):
            st.info("Configure the LLM provider in the sidebar, select stages above, then click **Run Analysis**.")
            return

        _apply_env(cfg)

        log_container = st.empty()
        logs: list[str] = []

        _STAGE_LABELS = {
            "profiling":     "📊 Dataset profiled",
            "cleaning":      "🧹 Data cleaning complete",
            "relations":     "🔗 Relationships identified",
            "insights":      "💡 Business insights generated",
            "visualization": "🖼️ Agent visualizations complete",
            "plotly":        "🎯 Interactive charts built",
        }

        with contextlib.redirect_stdout(StreamlitLogger(log_container, logs)):
            try:
                with st.status("🤖 Agents are analysing your data…", expanded=True) as status:
                    status.write("⚙️ Starting pipeline…")

                    def on_progress(stage: str, data=None) -> None:
                        label = _STAGE_LABELS.get(stage, f"✅ {stage} complete")
                        status.write(label)

                    result = run_crew(
                        str(file_path),
                        session_id=session_id,
                        on_progress=on_progress,
                        selected_tasks=selected_tasks,
                        deep_analysis=deep_analysis,
                    )
                    status.update(
                        label="✅ Analysis complete!",
                        state="complete",
                        expanded=False,
                    )

                if result:
                    st.session_state[cache_key] = result
                    st.rerun()

            except Exception as e:
                st.error(f"❌ An error occurred: {e}")
                st.exception(e)


if __name__ == "__main__":
    main()
