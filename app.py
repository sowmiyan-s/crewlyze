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
        background: linear-gradient(90deg, #a855f7, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
        font-size: 3.5rem !important;
        letter-spacing: -1px;
        padding-bottom: 1rem;
    }
    
    h2 {
        color: #f3f4f6 !important;
        font-weight: 600 !important;
        font-size: 1.8rem !important;
        margin-top: 2.5rem !important;
        border-left: 4px solid #a855f7;
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
        background: linear-gradient(90deg, #7c3aed, #2563eb);
        color: white;
        border: none;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.9rem;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(124, 58, 237, 0.5);
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
        border-color: #a855f7;
        background: rgba(255, 255, 255, 0.05);
    }
    
    /* Relations specific */
    .relation-item {
        background: linear-gradient(90deg, rgba(124, 58, 237, 0.1), rgba(37, 99, 235, 0.05));
        border: 1px solid rgba(124, 58, 237, 0.2);
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
                <span style="color: #a855f7; font-size: 1.2em; margin-right: 10px;">{emoji}</span>
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
                
                display_text = f"<span style='color: #e0e0e0; font-weight: 600;'>{x_col}</span> <span style='color: #6b7280; margin: 0 5px;'>vs</span> <span style='color: #e0e0e0; font-weight: 600;'>{y_col}</span> <span style='color: #a855f7; font-size: 0.85em; margin-left: 10px; background: rgba(168, 85, 247, 0.1); padding: 2px 8px; border-radius: 12px;'>{plot_type}</span>"
                
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

def main():
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
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
    st.title("Agentic Data Analyst")
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
            
        st.success(f"✅ File uploaded successfully: {uploaded_file.name}")
        
        # Preview
        df = pd.read_csv(file_path)
        with st.expander("📊 Preview Dataset"):
            st.dataframe(df.head())
        
        # Analysis Button
        if st.button("🚀 Start Analysis"):
            st.markdown("---")
            st.markdown("### 🔄 Analysis in Progress")
            
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
                    with st.spinner("🤖 Agents are working..."):
                        result = run_crew(str(file_path))
                    
                    if result:
                        st.session_state['analysis_result'] = result
                        st.markdown("---")
                        st.success("### ✅ Analysis Complete!")
                        st.balloons()
                        
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
                        st.markdown("### 📈 Visualizations")
                        output_dir = result['output_dir']
                        png_files = sorted(glob.glob(str(output_dir / "*.png")))
                        if png_files:
                            cols = st.columns(2)
                            for idx, png_file in enumerate(png_files):
                                with cols[idx % 2]:
                                    img = Image.open(png_file)
                                    st.image(img, use_column_width=True, caption=Path(png_file).stem)
                        else:
                            st.warning("No visualizations generated.")

                        # Generated Code Info
                        st.markdown("### ⚙️ Visualization Method")
                        st.info(result.get('code', 'Automatic visualization generation'))
                        
                        # Insights
                        st.markdown("### 💡 Key Insights")
                        display_text_as_bullets(result['insights'], "✨")
                        
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
                    st.exception(e)
    
    # Display stored results if available
    elif 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']
        st.markdown("## 📊 Analysis Results (Cached)")
        st.dataframe(result['dataframe'].head(50))
        
        st.markdown("### 🧹 Data Cleaning Steps")
        display_text_as_bullets(result['cleaning_steps'], "🔹")
        
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

        st.markdown("### 🔗 Column Relations")
        display_relations(result['relations'])

        st.markdown("### 📈 Visualizations")
        output_dir = result['output_dir']
        png_files = sorted(glob.glob(str(output_dir / "*.png")))
        if png_files:
            cols = st.columns(2)
            for idx, png_file in enumerate(png_files):
                with cols[idx % 2]:
                    img = Image.open(png_file)
                    st.image(img, use_column_width=True, caption=Path(png_file).stem)
        else:
            st.warning("No visualizations generated.")

        st.markdown("### 💡 Key Insights")
        display_text_as_bullets(result['insights'], "✨")

if __name__ == "__main__":
    main()
