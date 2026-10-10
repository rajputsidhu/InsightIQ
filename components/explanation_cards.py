"""
Reusable UI Explanation Cards for InsightIQ Explainable AI.
Renders feature attribution cards, attribution waterfalls, and counterfactual scenario cards.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, List


from components.design_system import get_theme_tokens
from components.charts import apply_theme


def render_individual_explanation_card(explanation: Dict[str, Any]):
    """Render comprehensive customer-level explanation with attributions and narrative."""
    if "error" in explanation:
        st.error(explanation["error"])
        return

    tokens = get_theme_tokens()
    prob = explanation["churn_probability"]
    tier = explanation["risk_tier"]

    if tier == "High Risk":
        badge_bg = tokens["danger_bg"]
        badge_fg = tokens["danger"]
    elif tier == "Medium Risk":
        badge_bg = tokens["warning_bg"]
        badge_fg = tokens["warning"]
    else:
        badge_bg = tokens["success_bg"]
        badge_fg = tokens["success"]

    # Header Card
    st.markdown(
        f"""
        <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem; box-shadow: {tokens['card_shadow']};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                <div>
                    <span style="font-size: 0.75rem; font-weight: 700; color: {tokens['text_muted']}; text-transform: uppercase; letter-spacing: 0.05em;">Customer Risk Investigation</span>
                    <h3 style="margin: 2px 0 0 0; color: {tokens['text_primary']}; font-size: 1.35rem; font-weight: 700;">{explanation['customer_id']}</h3>
                </div>
                <div style="text-align: right;">
                    <span style="background: {badge_bg}; color: {badge_fg}; font-weight: 700; padding: 4px 12px; border-radius: 9999px; font-size: 0.8rem; border: 1px solid {badge_fg}33;">
                        {tier} ({prob*100:.1f}%)
                    </span>
                    <div style="font-size: 0.75rem; color: {tokens['text_muted']}; margin-top: 4px;">Engine: {explanation['model_name']} ({explanation['explanation_method']})</div>
                </div>
            </div>
            <div style="background: {tokens['surface_subtle']}; border-left: 3px solid {tokens['brand_primary']}; padding: 0.85rem 1rem; border-radius: 6px; font-size: 0.875rem; color: {tokens['text_secondary']}; line-height: 1.55;">
                <strong style="color: {tokens['text_primary']};">Diagnostic Summary:</strong> {explanation['narrative_explanation']}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Attribution Breakdown Plot
    top_factors = explanation.get("top_factors", [])
    if top_factors:
        st.markdown(f"<div style='font-size: 0.875rem; font-weight: 600; color: {tokens['text_primary']}; margin: 1rem 0 0.5rem 0;'>Top Attributed Factors Influencing Predicted Score</div>", unsafe_allow_html=True)
        features = [f["feature"].replace("num__", "").replace("cat__", "") for f in top_factors][::-1]
        values = [f["attribution"] for f in top_factors][::-1]
        colors = [tokens["danger"] if v > 0 else tokens["success"] for v in values]

        fig = go.Figure(
            go.Bar(
                x=values,
                y=features,
                orientation="h",
                marker=dict(color=colors),
                text=[f"{v:+.3f}" for v in values],
                textposition="outside",
            )
        )
        fig.update_layout(
            height=280,
            margin=dict(l=10, r=40, t=10, b=10),
            xaxis_title="Feature Attribution to Model Score (Positive = Increases Churn)",
            yaxis_title=None,
        )
        fig = apply_theme(fig, height=280)
        st.plotly_chart(fig, use_container_width=True)

    # Attribution Table
    df_attr = pd.DataFrame([
        {
            "Feature Indicator": f["feature"].replace("num__", "").replace("cat__", ""),
            "Attribution Weight": round(f["attribution"], 4),
            "Impact Direction": f["direction"],
        }
        for f in top_factors
    ])
    st.dataframe(df_attr, use_container_width=True, hide_index=True)

    # Statistical Disclaimer
    st.caption(f"ℹ️ *{explanation['methodology_note']}*")


def render_counterfactual_comparison_card(result: Dict[str, Any]):
    """Render counterfactual simulation comparison with delta indicators."""
    if "error" in result:
        st.error(result["error"])
        return

    tokens = get_theme_tokens()
    orig_prob = result["original_probability"]
    sim_prob = result["simulated_probability"]
    abs_delta = result["absolute_delta"]
    pct_change = result["percentage_change"]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Baseline Churn Probability", f"{orig_prob*100:.1f}%", result["original_tier"])
    with c2:
        st.metric(
            "Hypothetical Churn Probability",
            f"{sim_prob*100:.1f}%",
            f"{abs_delta*100:+.1f} pts ({pct_change:+.1f}%)",
            delta_color="inverse"
        )
    with c3:
        st.metric("Hypothetical Risk Tier", result["simulated_tier"], f"Evaluated via {result['model_used']}")

    st.markdown(
        f"""
        <div style="background: {tokens['surface_subtle']}; border: 1px dashed {tokens['border']}; border-radius: 8px; padding: 0.85rem 1.1rem; margin-top: 0.75rem; font-size: 0.85rem; color: {tokens['text_secondary']}; line-height: 1.5;">
            {result['disclaimer']}
        </div>
        """,
        unsafe_allow_html=True
    )
