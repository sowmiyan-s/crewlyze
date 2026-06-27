# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Streamlit entry point for the Agentic Data Analyst application.

Performance improvements in this version:
- st.status() provides a live progress log as each pipeline stage completes
- on_progress callback surfaces intermediate results without blocking the UI
- Plotly interactive charts rendered via st.plotly_chart() in the Visual tab
  (with agent-generated PNGs as fallback if Plotly charts are unavailable)
- Default API cooldown reduced from 15s → 5s
- 'ollama' added as a zero-cooldown provider option in the sidebar
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
from ui.styles import inject_styles
from ui.components import display_text_as_bullets, display_relations, StreamlitLogger
from ui.export import export_pdf_cached

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
    """Initialise per-session state on first load."""
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = uuid.uuid4().hex[:12]
    if "llm_provider" not in st.session_state:
        st.session_state["llm_provider"] = os.getenv("LLM_PROVIDER", "nvidia")
    if "llm_model" not in st.session_state:
        st.session_state["llm_model"] = ""
    if "api_key" not in st.session_state:
        st.session_state["api_key"] = ""


# ── Sidebar ───────────────────────────────────────────────────────────────────

def _render_sidebar() -> dict:
    """Render the sidebar and return the current LLM config dict."""
    with st.sidebar:
        st.markdown("## Configuration")
        st.markdown("### LLM Settings")

        model_options = {
            "nvidia":      ["nvidia_nim/mistralai/mistral-medium-3.5-128b", "nvidia_nim/mistralai/mistral-large-2407"],
            "minimax":     ["minimaxai/minimax-m3"],
            "groq":        ["groq/llama-3.1-8b-instant", "groq/llama-3.3-70b-versatile", "groq/mixtral-8x7b-32768", "groq/gemma2-9b-it"],
            "openai":      ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "anthropic":   ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            "huggingface": ["huggingface/HuggingFaceH4/zephyr-7b-beta", "huggingface/meta-llama/Llama-2-7b-chat-hf", "huggingface/tiiuae/falcon-7b-instruct"],
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

        selected_model = st.selectbox(
            "Select Model",
            model_options.get(provider, []),
            index=0,
        )
        st.session_state["llm_model"] = selected_model

        # Pre-fill key from env (initial load only) — stored in session_state
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
            help=f"Enter your {provider} API key" if provider != "ollama"
                 else "URL of your local Ollama server",
        )
        st.session_state["api_key"] = api_key

        # Cooldown: default 5s (was 15s); Ollama users typically set to 0
        default_cooldown = 0 if provider == "ollama" else int(os.getenv("API_COOLDOWN", "5"))
        cooldown = st.slider(
            "API Cooldown (seconds)",
            min_value=0,
            max_value=60,
            value=default_cooldown,
            help=(
                "Seconds to sleep between agent tasks to prevent rate limiting. "
                "Set to 0 for self-hosted models (Ollama) with no rate limits."
            ),
        )
        st.session_state["api_cooldown"] = cooldown

        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown(
            """
            <div style="background-color:#171717;padding:15px;border-radius:8px;border:1px solid #262626;">
                <p style="margin:0;font-size:0.9em;color:#a3a3a3;">
                    <b>Agentic Data Analyst</b><br>
                    An intelligent system powered by CrewAI that automates data cleaning,
                    analysis, and visualization.
                </p>
                <hr style="border-color:#262626;margin:10px 0;">
                <p style="margin:0;font-size:0.8em;color:#737373;">
                    Developed by:<br>
                    • Prithiv.A.K<br>• Sebin.S<br>• Sowmiyan.S
                </p>
                <div style="margin-top:15px;">
                    <a href="https://github.com/sowmiyan-s/Multi-Agent-Data-Analysis-System-with-CrewAI"
                       target="_blank" style="text-decoration:none;">
                        <button style="width:100%;background-color:#262626;color:#e0e0e0;
                            border:1px solid #404040;padding:8px;border-radius:6px;
                            cursor:pointer;font-size:0.8em;transition:all 0.3s;">
                            ⭐ Star on GitHub
                        </button>
                    </a>
                </div>
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


# ── Apply LLM config to os.environ (only when running analysis) ───────────────

def _apply_env(cfg: dict) -> None:
    """Write LLM settings to os.environ immediately before run_crew()."""
    if cfg["api_key"]:
        os.environ[cfg["env_key_name"]] = cfg["api_key"]
    os.environ["LLM_PROVIDER"] = cfg["provider"]
    os.environ["LLM_MODEL"]    = cfg["model"]
    os.environ["API_COOLDOWN"] = str(cfg["cooldown"])


# ── Results display ───────────────────────────────────────────────────────────

def _render_results(result: dict) -> None:
    """Render the full analysis results UI."""
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

    with tab_preview:
        st.markdown("### 🔍 Dataset Explorer")
        st.dataframe(result["dataframe"].head(100), use_container_width=True)

    with tab_cleaning:
        st.markdown("### 🧹 Data Cleaning Operations")
        display_text_as_bullets(result["cleaning_steps"], "🔹")

    with tab_relations:
        st.markdown("### 🔗 Column Relationships")
        display_relations(result["relations"])

    with tab_insights:
        st.markdown("### 💡 Business Intelligence Insights")
        display_text_as_bullets(result["insights"], "✨")

    with tab_plots:
        st.markdown("### 📈 Visual Intelligence")

        # ── Interactive Plotly charts (generated from relation output, no LLM) ──
        plotly_charts = result.get("plotly_charts", [])
        if plotly_charts:
            st.markdown("#### 🎯 Interactive Charts")
            st.caption("Zoom, pan, and hover for details on any chart.")
            for chart in plotly_charts:
                st.plotly_chart(chart["fig"], use_container_width=True)
            st.markdown("---")

        # ── Agent-generated static PNGs (supplementary / fallback) ──────────────
        output_dir = Path(result.get("output_dir", "outputs"))
        png_files  = sorted(output_dir.glob("*.png"))
        if png_files:
            st.markdown("#### 🖼️ Agent-Generated Visualizations")
            for png_file in png_files:
                st.image(str(png_file), caption=png_file.stem, use_container_width=True)
        elif not plotly_charts:
            st.info("No visualizations generated by the agent.")

    # Generated code block
    st.markdown("---")
    st.markdown("### ⚙️ Visualization Architecture")
    st.code(result.get("code", "Automatic visualization generation"), language="python")

    # Export options
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

    # ── Save file ─────────────────────────────────────────────────────────────
    data_dir  = Path("data")
    data_dir.mkdir(exist_ok=True)
    file_path = data_dir / uploaded_file.name

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # ── Cache key: MD5 of file CONTENT (not just filename) ───────────────────
    file_hash  = hashlib.md5(uploaded_file.getvalue()).hexdigest()
    cache_key  = f"result_{file_hash}"
    session_id = st.session_state["session_id"]

    # ── Preview ───────────────────────────────────────────────────────────────
    df = pd.read_csv(file_path, nrows=200)
    st.success(f"✅ File uploaded: **{uploaded_file.name}** ({uploaded_file.size:,} bytes)")
    with st.expander("📊 Preview Dataset", expanded=cache_key not in st.session_state):
        st.dataframe(df.head())

    st.markdown("---")

    # ── Show results if already cached ───────────────────────────────────────
    if cache_key in st.session_state:
        _render_results(st.session_state[cache_key])
        if st.button("🔄 Re-run Analysis", use_container_width=True):
            del st.session_state[cache_key]
            st.rerun()
        return

    # ── Explicit run button ───────────────────────────────────────────────────
    st.markdown("### 🤖 Ready to Analyse")
    if not st.button("▶️ Run Analysis", use_container_width=True, type="primary"):
        st.info("Configure the LLM provider in the sidebar, then click **Run Analysis**.")
        return

    # Apply config to os.environ only at invocation time
    _apply_env(cfg)

    log_container = st.empty()
    logs: list[str] = []

    # ── Progressive status display ────────────────────────────────────────────
    _STAGE_LABELS = {
        "profiling":     "📊 Dataset profiled (eliminated tool-call round-trips)",
        "cleaning":      "🧹 Data cleaning complete",
        "relations":     "🔗 Relationships identified",
        "insights":      "💡 Business insights generated",
        "visualization": "🖼️ Agent visualizations complete",
        "plotly":        "🎯 Interactive charts built",
    }

    with contextlib.redirect_stdout(StreamlitLogger(log_container, logs)):
        try:
            with st.status("🤖 Agents are analysing your data...", expanded=True) as status:
                status.write("⚙️ Starting pipeline...")

                def on_progress(stage: str, data=None) -> None:
                    label = _STAGE_LABELS.get(stage, f"✅ {stage} complete")
                    status.write(label)

                result = run_crew(
                    str(file_path),
                    session_id=session_id,
                    on_progress=on_progress,
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
