from crewai import Agent, LLM
from config.llm_config import get_llm_params
from tools.bi_tools import BusinessIntelligenceTools

def make_anomaly_agent() -> Agent:
    """Factory — creates a Business Risk & Revenue Leakage Auditor Agent equipped with real BI audit tools."""
    return Agent(
        name="Business Risk & Revenue Leakage Auditor",
        role="Detect operational outliers, revenue leakage, margin anomalies, and commercial risk factors in the dataset",
        goal=(
            "Audit the business dataset using your tools to automatically identify statistical outliers and abnormal clusters. "
            "Flag revenue leakage, margin anomalies, churn warning signs, and operational bottlenecks. "
            "Cross-examine growth claims to find hidden risks, and provide executive safeguards and risk mitigation "
            "recommendations to protect business profitability."
        ),
        backstory=(
            "You are a Senior Risk & Profitability Auditor specializing in quantitative forensic business analysis. "
            "You scrutinize transactions and operational data using computational tools to detect margin leakage, unexpected cost spikes, "
            "and abnormal behavior that threatens sustainable growth. You hold the Growth Scout accountable by verifying margin reality."
        ),
        tools=[
            BusinessIntelligenceTools.audit_margin_leakage,
            BusinessIntelligenceTools.query_segment_performance,
        ],
        allow_delegation=False,
        max_iter=3,
        llm=LLM(**get_llm_params()),
        verbose=True,
    )

