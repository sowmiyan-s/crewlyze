# Crewlyze
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Master BI Orchestrator agent.

Acts as the Chief Strategy Officer and Lead BI Director, setting the strategic agenda,
formulating commercial hypotheses based on the detected business domain, directing
specialist agents, cross-examining conflicting findings, and synthesizing final
high-conviction growth plays.
"""

from crewai import Agent, LLM
from config.llm_config import get_llm_params
from tools.bi_tools import BusinessIntelligenceTools


def make_orchestrator_agent() -> Agent:
    """Factory — creates the Master BI Orchestrator (Chief Strategy Officer)."""
    return Agent(
        name="Master BI Orchestrator",
        role="Chief Strategy Officer & Lead Business Intelligence Director",
        goal=(
            "Direct the autonomous multi-agent business intelligence investigation. "
            "Analyze dataset dimensions and domain signatures, formulate strategic growth hypotheses, "
            "delegate inquiries to specialist agents (Growth Scout, Risk Auditor, Predictive Analyst), "
            "arbitrate trade-offs between growth acceleration and margin risk, and synthesize "
            "a unified executive growth strategy focused on 'Growth in X' and 'Problem in Y likely'."
        ),
        backstory=(
            "You are a top-tier Chief Strategy Officer and former Senior Partner at McKinsey / Bain. "
            "You do not accept surface-level correlations or academic statistical distribution lectures. "
            "You orchestrate a team of specialist analytical agents to interrogate the data relentlessly. "
            "When the Growth Scout claims an opportunity, you task the Risk Auditor to test for hidden margin bleed. "
            "You ensure every recommendation is backed by real numbers and column-level facts from the user's dataset."
        ),
        tools=[
            BusinessIntelligenceTools.query_segment_performance,
            BusinessIntelligenceTools.calculate_driver_correlations,
            BusinessIntelligenceTools.audit_margin_leakage,
        ],
        allow_delegation=False,
        max_iter=3,
        llm=LLM(**get_llm_params()),
        verbose=True,
    )
