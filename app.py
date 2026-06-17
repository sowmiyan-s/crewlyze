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

# Custom CSS for premium design
st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background: radial-gradient(circle at top right, #1e1b4b, #09090b);
        color: #e2e8f0;
        font-family: 'Outfit', sans-serif;
    }
    
    .main {
        background: radial-gradient(circle at top right, #1e1b4b, #09090b);
        padding: 2.5rem;
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(15, 23, 42, 0.45);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    .glass-card:hover {
        transform: translateY(-2px);
        border-color: rgba(139, 92, 246, 0.3);
    }
    
    /* Scorecard stats grid */
    .stat-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .stat-card {
        flex: 1;
        background: rgba(139, 92, 246, 0.05);
        border: 1px solid rgba(139, 92, 246, 0.15);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        box-shadow: inset 0 0 12px rgba(139, 92, 246, 0.05);
    }
    .stat-val {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #a78bfa, #22d3ee);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    .stat-lbl {
        font-size: 0.85rem;
        color: #94a3b8;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Headers */
    .main-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 800 !important;
        font-size: 3.5rem !important;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #a78bfa 0%, #6366f1 50%, #22d3ee 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
        text-shadow: 0 0 40px rgba(99, 102, 241, 0.1);
    }
    
    h2 {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
        margin-top: 2rem !important;
        border-left: 4px solid #a78bfa;
        padding-left: 1rem;
        letter-spacing: -0.02em;
    }
    
    h3 {
        color: #cbd5e1 !important;
        font-weight: 600 !important;
        font-size: 1.4rem !important;
        margin-top: 1.5rem !important;
        letter-spacing: -0.01em;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: rgba(9, 9, 11, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 50%, #06b6d4 100%);
        color: #ffffff !important;
        border: none;
        padding: 0.75rem 1.75rem;
        font-weight: 700;
        border-radius: 10px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.85rem;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.25);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.45);
        color: #ffffff !important;
        background: linear-gradient(135deg, #a78bfa 0%, #818cf8 50%, #22d3ee 100%);
    }
    
    /* DataFrames */
    .stDataFrame {
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        background-color: rgba(9, 9, 11, 0.4);
        padding: 5px;
    }
    
    /* Custom Bullet Points */
    .styled-bullet {
        background: rgba(15, 23, 42, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 1.25rem;
        margin-bottom: 0.75rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.2s;
    }
    .styled-bullet:hover {
        transform: translateX(6px);
        border-color: rgba(139, 92, 246, 0.4);
        background: rgba(15, 23, 42, 0.5);
    }
    
    /* Relations specific */
    .relation-item {
        background: linear-gradient(90deg, rgba(139, 92, 246, 0.08) 0%, rgba(6, 182, 212, 0.03) 100%);
        border: 1px solid rgba(139, 92, 246, 0.15);
        padding: 0.85rem 1.25rem;
        border-radius: 10px;
        margin-bottom: 0.6rem;
        display: flex;
        align-items: center;
        font-family: 'JetBrains Mono', monospace;
        transition: transform 0.2s;
    }
    .relation-item:hover {
        transform: translateX(4px);
        border-color: rgba(6, 182, 212, 0.3);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: rgba(15, 23, 42, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        font-size: 1rem;
        color: #e2e8f0 !important;
    }
    
    /* File uploader custom style */
    div[data-testid="stFileUploader"] {
        background: rgba(15, 23, 42, 0.25);
        border: 2px dashed rgba(139, 92, 246, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        transition: border-color 0.3s;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: rgba(6, 182, 212, 0.4);
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

def export_pdf(result):
    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from PIL import Image as PILImage
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Custom colors
    primary_color = colors.HexColor("#6366f1")
    secondary_color = colors.HexColor("#06b6d4")
    text_color = colors.HexColor("#1e293b")
    
    # Custom paragraph styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=secondary_color,
        spaceAfter=20
    )
    
    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_color,
        spaceAfter=8
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_color,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=6
    )

    # Document Header
    story.append(Paragraph("Agentic Data Analysis Report", title_style))
    story.append(Paragraph("Autonomous Business Intelligence Insights & Visualizations", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Dataset Metadata Table
    story.append(Paragraph("Dataset Summary", h1_style))
    df = result.get('dataframe')
    if df is not None:
        summary_data = [
            [Paragraph("<b>Metric</b>", body_style), Paragraph("<b>Value</b>", body_style)],
            [Paragraph("Total Rows", body_style), Paragraph(str(df.shape[0]), body_style)],
            [Paragraph("Total Columns", body_style), Paragraph(str(df.shape[1]), body_style)],
            [Paragraph("Columns", body_style), Paragraph(f"{', '.join(df.columns[:8])}{'...' if len(df.columns) > 8 else ''}", body_style)]
        ]
        t = Table(summary_data, colWidths=[130, 370])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t)
    story.append(Spacer(1, 10))
    
    # Cleaning Steps
    story.append(Paragraph("Data Cleaning Steps", h1_style))
    cleaning_steps = result.get('cleaning_steps', '')
    for line in cleaning_steps.split('\n'):
        line = line.strip()
        if line:
            if line.startswith(('-', '*', '•')):
                line = line[1:].strip()
            story.append(Paragraph(f"• {line}", bullet_style))
    story.append(Spacer(1, 10))
    
    # Relations
    story.append(Paragraph("Identified Relationships", h1_style))
    relations = result.get('relations', '')
    for line in relations.split('\n'):
        line = line.strip()
        if line:
            if line.startswith(('-', '*', '•')):
                line = line[1:].strip()
            story.append(Paragraph(f"🔗 {line}", bullet_style))
    story.append(Spacer(1, 10))
    
    # Key Insights
    story.append(Paragraph("Key Insights", h1_style))
    insights = result.get('insights', '')
    for line in insights.split('\n'):
        line = line.strip()
        if line:
            if line.startswith(('-', '*', '•')) or (len(line) > 2 and line[0].isdigit() and line[1] == '.'):
                line = line.lstrip('0123456789.-*• ').strip()
            story.append(Paragraph(f"✨ {line}", bullet_style))
    
    # Page Break for Visualizations
    story.append(PageBreak())
    
    # Visualizations
    story.append(Paragraph("Visualizations", h1_style))
    output_dir = Path("outputs")
    png_files = list(output_dir.glob("*.png"))
    
    if png_files:
        for png_file in png_files:
            try:
                with PILImage.open(png_file) as img:
                    orig_w, orig_h = img.size
                
                max_w = 460
                max_h = 300
                
                aspect = orig_h / orig_w
                if aspect > (max_h / max_w):
                    new_h = max_h
                    new_w = new_h / aspect
                else:
                    new_w = max_w
                    new_h = new_w * aspect
                
                story.append(Paragraph(f"<b>{png_file.stem}</b>", body_style))
                story.append(Image(str(png_file), width=new_w, height=new_h))
                story.append(Spacer(1, 10))
            except Exception as e:
                story.append(Paragraph(f"Error loading image {png_file.name}: {str(e)}", body_style))
    else:
        story.append(Paragraph("No visualizations generated.", body_style))
        
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

def main():
    # Sidebar
    with st.sidebar:
        st.markdown("## Configuration")
        
        st.markdown("### LLM Settings")
        provider = st.selectbox(
            "Select Provider",
            ["nvidia", "groq", "openai", "anthropic", "huggingface", "mistral", "gemini"],
            index=0
        )
        
        # Model Options
        model_options = {
            "nvidia": ["nvidia_nim/mistralai/mistral-medium-3.5-128b", "nvidia_nim/mistralai/mistral-large-2407"],
            "groq": ["groq/llama-3.1-8b-instant", "groq/llama-3.3-70b-versatile", "groq/mixtral-8x7b-32768", "groq/gemma2-9b-it"],
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
        
        default_key = ""
        if provider == "nvidia":
            default_key = os.getenv("NVIDIA_API_KEY", "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")
        else:
            default_key = os.getenv(f"{provider.upper()}_API_KEY", "")

        api_key = st.text_input(
            f"{provider.upper()} API Key",
            value=default_key,
            type="password",
            help=f"Enter your {provider} API key"
        )
        
        if api_key:
            os.environ[f"{provider.upper()}_API_KEY"] = api_key
        
        os.environ["LLM_PROVIDER"] = provider
        os.environ["LLM_MODEL"] = selected_model
        
        cooldown = st.slider(
            "API Cooldown (seconds)",
            min_value=0,
            max_value=60,
            value=15,
            help="Time to sleep between agent tasks to prevent rate limiting."
        )
        os.environ["API_COOLDOWN"] = str(cooldown)
        
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
    st.markdown("<h1 class='main-title'>Agentic Data Analyst</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 1.15rem; margin-bottom: 2rem;'>Autonomous Multi-Agent Business Intelligence and Data Engineering System</p>", unsafe_allow_html=True)
    
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
                        <div style="height: 300px; overflow-y: scroll; background-color: rgba(9, 9, 11, 0.85); backdrop-filter: blur(12px); color: #22d3ee; padding: 18px; border-radius: 12px; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; white-space: pre-wrap; border: 1px solid rgba(139, 92, 246, 0.4); box-shadow: 0 0 20px rgba(139, 92, 246, 0.15), inset 0 0 15px rgba(0,0,0,0.6);">
                            <span style="color: #a78bfa; font-weight: bold;">$ agentic_terminal_output</span><br/>
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
            st.markdown("## 📊 Executive Dashboard")
            df = result['dataframe']
            
            # Scorecard Grid
            st.markdown(f"""
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
                    <div class="stat-val">{len(df.select_dtypes(include=['number']).columns)}</div>
                    <div class="stat-lbl">Numeric Fields</div>
                </div>
                <div class="stat-card">
                    <div class="stat-val">{len(df.select_dtypes(include=['object']).columns)}</div>
                    <div class="stat-lbl">Categorical Fields</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Tabs for results layout
            tab_preview, tab_cleaning, tab_relations, tab_insights, tab_plots = st.tabs([
                "🔍 Data Preview", 
                "🧹 Clean Report", 
                "🔗 Relations Map", 
                "💡 Key Insights",
                "📈 Visual intelligence"
            ])
            
            with tab_preview:
                st.markdown("### 🔍 Dataset Explorer")
                st.dataframe(result['dataframe'].head(100), use_container_width=True)
                
            with tab_cleaning:
                st.markdown("### 🧹 Data Cleaning Operations")
                display_text_as_bullets(result['cleaning_steps'], "🔹")
                
            with tab_relations:
                st.markdown("### 🔗 Column Relationships")
                display_relations(result['relations'])
                
            with tab_insights:
                st.markdown("### 💡 Business Intelligence Insights")
                display_text_as_bullets(result['insights'], "✨")
                
            with tab_plots:
                st.markdown("### 📈 Agent Generated Visualizations")
                output_dir = Path("outputs")
                png_files = list(output_dir.glob("*.png"))
                if png_files:
                    for png_file in png_files:
                        st.image(str(png_file), caption=png_file.stem, use_container_width=True)
                else:
                    st.info("No visualizations generated by the agent.")

            # Generated Code Info
            st.markdown("---")
            st.markdown("### ⚙️ Visualization Architecture")
            st.code(result.get('code', 'Automatic visualization generation'), language='python')

            # Export Options
            st.markdown("---")
            st.markdown("### 📥 Export Options")
            c1, c2 = st.columns(2)
            with c1:
                try:
                    pdf_bytes = export_pdf(result)
                    st.download_button(
                        label="📄 Export Full Report as PDF",
                        data=pdf_bytes,
                        file_name="data_analysis_report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error preparing PDF: {str(e)}")
            with c2:
                csv = result['dataframe'].to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Cleaned Dataset (CSV)",
                    data=csv,
                    file_name="cleaned_dataset.csv",
                    mime="text/csv",
                    use_container_width=True
                )

if __name__ == "__main__":
    main()
