import streamlit as st
import pandas as pd
import os
from pathlib import Path
import sys
import contextlib
import html
import json
import re
import glob
from PIL import Image

from crew import run_crew
import numpy as np

# Disable CrewAI Telemetry
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

# Set page config
st.set_page_config(
    page_title="Agentic Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background-color: #050505;
        color: #e0e0e0;
        font-family: 'Outfit', sans-serif;
    }
    
    .main {
        background-color: #050505;
        padding: 2rem;
    }
    
    /* Headers */
    h1 {
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 3.2rem !important;
        letter-spacing: -1px;
        padding-bottom: 1rem;
        text-shadow: 0 0 30px rgba(255, 255, 255, 0.1);
    }
    
    h2 {
        color: #f3f4f6 !important;
        font-weight: 600 !important;
        font-size: 1.8rem !important;
        margin-top: 2.5rem !important;
        border-left: 4px solid #e879f9;
        padding-left: 1rem;
    }
    
    h3 {
        color: #9ca3af !important;
        font-weight: 500 !important;
        font-size: 1.3rem !important;
        margin-top: 1.5rem !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0a0a0a;
        border-right: 1px solid #262626;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #c084fc, #22d3ee);
        color: #000000;
        border: none;
        padding: 0.8rem 1.5rem;
        font-weight: 700;
        border-radius: 8px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.9rem;
        box-shadow: 0 4px 15px rgba(192, 132, 252, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(192, 132, 252, 0.5);
        color: #000000;
    }
    
    /* DataFrames */
    .stDataFrame {
        border: 1px solid #262626;
        border-radius: 8px;
        background-color: #0a0a0a;
    }
    
    /* Custom Bullet Points */
    .styled-bullet {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid #262626;
        padding: 1rem;
        margin-bottom: 0.75rem;
        border-radius: 8px;
        transition: transform 0.2s, border-color 0.2s;
    }
    .styled-bullet:hover {
        transform: translateX(5px);
        border-color: #e879f9;
        background: rgba(255, 255, 255, 0.05);
    }
    
    /* Relations specific */
    .relation-item {
        background: linear-gradient(90deg, rgba(192, 132, 252, 0.1), rgba(34, 211, 238, 0.05));
        border: 1px solid rgba(192, 132, 252, 0.2);
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #0a0a0a;
        border: 1px solid #262626;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

def display_text_as_bullets(text, emoji="🔹"):
    """Parses text lines and displays them as styled bullet points."""
    if not text:
        return
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if line:
            if line.startswith(('-', '*', '•', '1.', '2.', '3.')):
                line = line.lstrip('-*•1234567890. ')
            
            st.markdown(f"""
            <div class="styled-bullet">
                <span style="color: #e879f9; font-size: 1.2em; margin-right: 10px;">{emoji}</span>
                <span style="font-size: 1.05em; color: #d1d5db;">{line}</span>
            </div>
            """, unsafe_allow_html=True)

def display_relations(text):
    """Parses relations text and displays as simple X vs Y (Type) bullets."""
    if not text:
        return
        
    lines = text.split('\n')
    for line in lines:
        if "|" in line and "X:" in line:
            try:
                parts = [p.strip() for p in line.replace("- ", "").split("|")]
                x_col = parts[0].split(":")[1].strip()
                y_col = parts[1].split(":")[1].strip()
                plot_type = parts[2].split(":")[1].strip()
                
                display_text = f"<span style='color: #e0e0e0; font-weight: 600;'>{x_col}</span> <span style='color: #6b7280; margin: 0 5px;'>vs</span> <span style='color: #e0e0e0; font-weight: 600;'>{y_col}</span> <span style='color: #e879f9; font-size: 0.85em; margin-left: 10px; background: rgba(232, 121, 249, 0.1); padding: 2px 8px; border-radius: 12px;'>{plot_type}</span>"
                
                st.markdown(f"""
                <div class="relation-item">
                    <span style="margin-right: 10px; font-size: 1.2em;">🔗</span>
                    {display_text}
                </div>
                """, unsafe_allow_html=True)
            except:
                st.markdown(f"• {line}")
        elif line.strip():
             st.markdown(f"""
                <div class="relation-item">
                    <span style="margin-right: 10px; font-size: 1.2em;">🔗</span>
                    {line.strip('- ')}
                </div>
                """, unsafe_allow_html=True)

def render_visualizations(df, key_prefix=""):
    """Renders interactive Streamlit visualizations for the dataframe."""
    st.markdown("### 📈 Visualizations")
    
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # 1. Distribution plots
    if numeric_cols:
        st.markdown("#### Distribution of Numeric Variables")
        col_to_plot = st.selectbox("Select column for distribution", numeric_cols, key=f"{key_prefix}_dist_col")
        
        # Calculate histogram
        hist_values, bin_edges = np.histogram(df[col_to_plot].dropna(), bins=20)
        hist_df = pd.DataFrame({"Frequency": hist_values}, index=bin_edges[:-1])
        st.bar_chart(hist_df)
        
    # 2. Correlation Heatmap
    if len(numeric_cols) >= 2:
        st.markdown("#### Correlation Heatmap")
        corr = df[numeric_cols].corr()
        st.dataframe(corr.style.background_gradient(cmap="coolwarm"))
        
    # 3. Scatter Plot
    if len(numeric_cols) >= 2:
        st.markdown("#### Scatter Plot")
        c1, c2 = st.columns(2)
        with c1:
            x_col = st.selectbox("X Axis", numeric_cols, index=0, key=f"{key_prefix}_scatter_x")
        with c2:
            y_col = st.selectbox("Y Axis", numeric_cols, index=1 if len(numeric_cols) > 1 else 0, key=f"{key_prefix}_scatter_y")
        
        st.scatter_chart(df, x=x_col, y=y_col)
        
    # 4. Categorical vs Numeric
    if categorical_cols and numeric_cols:
        st.markdown("#### Categorical vs Numeric")
        c1, c2 = st.columns(2)
        with c1:
            cat_col = st.selectbox("Category", categorical_cols, index=0, key=f"{key_prefix}_cat_col")
        with c2:
            num_col = st.selectbox("Numeric", numeric_cols, index=0, key=f"{key_prefix}_num_col")
            
        # Aggregate mean
        chart_data = df.groupby(cat_col)[num_col].mean().sort_values(ascending=False).head(10)
        st.bar_chart(chart_data)
        st.caption(f"Average {num_col} by Top 10 {cat_col}")

def main():
    # Sidebar
    with st.sidebar:
        st.markdown("## Configuration")
        
        st.markdown("### LLM Settings")
        provider = st.selectbox(
            "Select Provider",
            ["groq", "openai", "anthropic", "huggingface", "mistral", "gemini"],
            index=0
        )
        
        # Model Options
        model_options = {
            "groq": ["groq/llama-3.3-70b-versatile", "groq/llama-3.1-8b-instant", "groq/mixtral-8x7b-32768", "groq/gemma2-9b-it"],
            "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            "huggingface": ["huggingface/HuggingFaceH4/zephyr-7b-beta", "huggingface/meta-llama/Llama-2-7b-chat-hf", "huggingface/tiiuae/falcon-7b-instruct"],
            "mistral": ["mistral/mistral-tiny", "mistral/mistral-small", "mistral/mistral-medium", "mistral/mistral-large-latest"],
            "gemini": ["gemini/gemini-pro", "gemini/gemini-1.5-pro", "gemini/gemini-1.5-flash"]
        }
        
        selected_model = st.selectbox(
            "Select Model",
            model_options.get(provider, []),
            index=0
        )
        
        api_key = st.text_input(
            f"{provider.upper()} API Key",
            type="password",
            help=f"Enter your {provider} API key"
        )
        
        if api_key:
            os.environ[f"{provider.upper()}_API_KEY"] = api_key
        
        os.environ["LLM_PROVIDER"] = provider
        os.environ["LLM_MODEL"] = selected_model
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("""
        <div style="background-color: #171717; padding: 15px; border-radius: 8px; border: 1px solid #262626;">
            <p style="margin: 0; font-size: 0.9em; color: #a3a3a3;">
                <b>Agentic Data Analyst</b><br>
                An intelligent system powered by CrewAI that automates data cleaning, analysis, and visualization.
            </p>
            <hr style="border-color: #262626; margin: 10px 0;">
            <p style="margin: 0; font-size: 0.8em; color: #737373;">
                Developed by:<br>
                • Prithiv.A.K<br>
                • Sebin.S<br>
                • Sowmiyan.S
            </p>
            <div style="margin-top: 15px;">
                <a href="https://github.com/sowmiyan-s/Multi-Agent-Data-Analysis-System-with-CrewAI" target="_blank" style="text-decoration: none;">
                    <button style="width: 100%; background-color: #262626; color: #e0e0e0; border: 1px solid #404040; padding: 8px; border-radius: 6px; cursor: pointer; font-size: 0.8em; transition: all 0.3s;">
                        ⭐ Star on GitHub
                    </button>
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Main Content
    st.title("Multi Agent Data Analysis with Crew AI")
    st.markdown("### Data Analysis as a Service")
    
    # File Upload
    uploaded_file = st.file_uploader("Upload your CSV dataset", type=['csv'])
    
    if uploaded_file is not None:
        # Save uploaded file
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        file_path = data_dir / uploaded_file.name
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        # Check if we need to run analysis (new file or no result yet)
        current_file_key = f"analysis_done_{uploaded_file.name}"
        
        if current_file_key not in st.session_state:
            st.success(f"✅ File uploaded successfully: {uploaded_file.name}")
            
            # Preview
            df = pd.read_csv(file_path)
            with st.expander("📊 Preview Dataset", expanded=True):
                st.dataframe(df.head())
            
            st.markdown("---")
            st.markdown("### 🔄 Auto-Starting Analysis...")
            
            # Container for logs
            log_container = st.empty()
            logs = []
            
            # Capture stdout
            class StreamlitLogger:
                def write(self, message):
                    if message.strip():
                        try:
                            clean_message = message.encode('utf-8', 'ignore').decode('utf-8')
                        except:
                            clean_message = message
                            
                        escaped_message = html.escape(clean_message)
                        logs.append(escaped_message)
                        log_html = f"""
                        <div style="height: 300px; overflow-y: scroll; background-color: #1e1e1e; color: #32CD32; padding: 15px; border-radius: 8px; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; white-space: pre-wrap; border: 1px solid #333; box-shadow: inset 0 0 10px rgba(0,0,0,0.5);">
                            <span style="color: #888;">$ analysis_log</span><br/>
                            {''.join(logs)}
                        </div>
                        """
                        log_container.markdown(log_html, unsafe_allow_html=True)
                    sys.__stdout__.write(message)
                    
                def flush(self):
                    sys.__stdout__.flush()
            
            # Run analysis
            with contextlib.redirect_stdout(StreamlitLogger()):
                try:
                    with st.spinner("🤖 Agents are analyzing your data..."):
                        result = run_crew(str(file_path))
                    
                    if result:
                        st.session_state[current_file_key] = result
                        st.session_state['current_active_file'] = current_file_key
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
                    st.exception(e)
        
        # Display Results if available
        elif current_file_key in st.session_state:
            result = st.session_state[current_file_key]
            
            st.success("### ✅ Analysis Complete!")
            
            # Display Results
            st.markdown("## 📊 Analysis Results")
            
            # Dataset Preview
            st.markdown("### 🔍 Dataset Preview")
            st.dataframe(result['dataframe'].head(50))
            
            # Cleaning Steps
            st.markdown("### 🧹 Data Cleaning Steps")
            display_text_as_bullets(result['cleaning_steps'], "🔹")
            
            # Validation
            st.markdown("### ✅ Dataset Validation")
            val_text = result['validation']
            if "Decision:" in val_text:
                parts = val_text.split("Decision:")
                if len(parts) > 1:
                    decision_part = parts[1].split("Reason:")[0].strip()
                    reason_part = val_text.split("Reason:")[1].strip() if "Reason:" in val_text else ""
                    
                    color = "#10b981" if "YES" in decision_part.upper() else "#ef4444"
                    st.markdown(f"""
                    <div style="padding: 15px; border-left: 5px solid {color}; background: rgba(255,255,255,0.05); border-radius: 5px;">
                        <h4 style="margin:0; color:{color}">Decision: {decision_part}</h4>
                        <p style="margin-top:10px;">{reason_part}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.text(val_text)
            
            # Relations
            st.markdown("### 🔗 Column Relations")
            display_relations(result['relations'])
            
            # Visualizations
            render_visualizations(result['dataframe'], key_prefix="main")

            # Generated Code Info
            st.markdown("### ⚙️ Visualization Method")
            st.info(result.get('code', 'Automatic visualization generation'))
            
            # Insights
            st.markdown("### 💡 Key Insights")
            display_text_as_bullets(result['insights'], "✨")

if __name__ == "__main__":
    main()
