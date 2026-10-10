"""
Alert and Notification Components for InsightIQ.
"""

import streamlit as st


def render_alert(message: str, level: str = "info", title: str = ""):
    """Render a styled enterprise alert box."""
    icons = {
        "info": "ℹ️",
        "warning": "⚠️",
        "success": "✅",
        "danger": "🚨",
    }
    icon = icons.get(level, "ℹ️")
    title_html = f"<strong>{title}</strong><br/>" if title else ""

    st.markdown(
        f"""
        <div class="alert-box {level}">
            <div style="font-size: 1.1rem; line-height: 1;">{icon}</div>
            <div>{title_html}{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_methodology_disclaimer():
    """Render standardized statistical disclaimer."""
    st.markdown(
        """
        <div class="alert-box info" style="font-size: 0.8rem; margin-top: 2rem;">
            <div>
                <strong>Statistical Methodology & Interpretive Notice:</strong><br/>
                Analytical metrics, clusters, risk scores, and forecasts are computational projections based on historical data. 
                Correlations identified in this platform do not establish causal relationships. 
                Always combine algorithmic outputs with qualitative business context before strategic execution.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
