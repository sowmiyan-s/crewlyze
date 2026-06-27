# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

import streamlit as st

CSS_BLOCK = """
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

    /* PREMIUM BUSINESS INTELLIGENCE CARDS */
    .insight-card {
        background: rgba(15, 23, 42, 0.55);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(139, 92, 246, 0.15);
        border-left: 5px solid #8b5cf6;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .insight-card:hover {
        transform: translateY(-2px);
        border-color: rgba(139, 92, 246, 0.35);
        box-shadow: 0 8px 30px rgba(139, 92, 246, 0.15);
    }
    .insight-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #a78bfa;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 0.5rem;
    }
    .insight-section {
        margin-bottom: 0.75rem;
    }
    .insight-section:last-child {
        margin-bottom: 0;
    }
    .insight-label {
        display: inline-block;
        font-size: 0.7rem;
        font-weight: 800;
        text-transform: uppercase;
        padding: 2px 8px;
        border-radius: 4px;
        margin-bottom: 0.25rem;
        letter-spacing: 0.05em;
    }
    .label-obs {
        background: rgba(148, 163, 184, 0.15);
        color: #cbd5e1;
        border: 1px solid rgba(148, 163, 184, 0.3);
    }
    .label-imp {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .label-strat {
        background: rgba(6, 182, 212, 0.15);
        color: #22d3ee;
        border: 1px solid rgba(6, 182, 212, 0.3);
    }
    .insight-text {
        font-size: 0.95rem;
        line-height: 1.5;
        color: #cbd5e1;
        margin: 0;
    }
    .insight-text-strat {
        font-weight: 500;
        color: #e2e8f0;
    }

    /* TIMELINE AUDIT TRAIL */
    .timeline-container {
        border-left: 2px solid rgba(139, 92, 246, 0.2);
        margin-left: 10px;
        padding-left: 20px;
        position: relative;
    }
    .timeline-item {
        background: rgba(15, 23, 42, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        position: relative;
    }
    .timeline-item::before {
        content: "✔";
        position: absolute;
        left: -31px;
        top: 15px;
        background: #8b5cf6;
        color: white;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        font-size: 0.65rem;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 10px rgba(139, 92, 246, 0.5);
    }
    .timeline-step {
        font-size: 0.8rem;
        font-weight: 700;
        color: #a78bfa;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }
    .timeline-desc {
        font-size: 0.95rem;
        color: #cbd5e1;
        margin: 0;
    }
    </style>

"""


def inject_styles() -> None:
    """Inject the application CSS into the Streamlit page."""
    st.markdown(CSS_BLOCK, unsafe_allow_html=True)
