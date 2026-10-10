"""
Deterministic Business Insights & Recommendations Page for InsightIQ.
Synthesizes deterministic evidence-based findings across revenue, product margins,
customer retention, and time-series trajectories into actionable cards.
"""

import streamlit as st
import pandas as pd
from components.header import render_header
from components.ui_components import render_page_title, render_section_header, render_empty_state
from components.alerts import render_alert, render_methodology_disclaimer
from components.design_system import get_theme_tokens
from services.business_metrics import infer_business_columns, calculate_executive_kpis
from services.insight_engine import generate_business_insights, generate_llm_executive_summary
from services.report_generator import export_dataframe_to_csv_bytes


def render_business_insights_page():
    """Render the automated insight and recommendation engine."""
    render_header("Business Insights", "Decision Support")

    df: pd.DataFrame = st.session_state.get("active_df")

    if df is None or df.empty:
        render_empty_state(
            title="No Active Dataset Available",
            description="Load a business or transaction dataset from the sidebar to generate automated insights.",
            icon="💡"
        )
        return

    tokens = get_theme_tokens()
    render_page_title(
        "Executive Business Insights & Decision Support",
        "Deterministic heuristic findings, margin diagnosis, customer segment alerts, and executive briefing synthesis."
    )

    col_map = st.session_state.get("col_map") or infer_business_columns(df)
    kpis = st.session_state.get("kpis") or calculate_executive_kpis(df, col_map)

    # Optional summaries from churn / forecast if available
    churn_summary = None
    if "churn_pipeline" in st.session_state:
        pipe = st.session_state["churn_pipeline"]
        if pipe and hasattr(pipe, "best_model_name") and pipe.best_model_name:
            risk_df = pipe.score_customers(df)
            if not risk_df.empty:
                high_pct = (risk_df["Risk_Tier"] == "High Risk").mean() * 100
                churn_summary = {"high_risk_pct": round(high_pct, 1)}

    forecast_summary = None
    if "forecast_results" in st.session_state:
        fc = st.session_state["forecast_results"]
        hist_mean = fc["summary"]["historical_mean"]
        fc_mean = fc["forecast_df"]["Forecast"].mean()
        if hist_mean > 0:
            growth_pct = round(((fc_mean - hist_mean) / hist_mean) * 100, 1)
            forecast_summary = {"projected_growth_pct": growth_pct}

    # Generate deterministic insights
    insights = generate_business_insights(
        df,
        col_map=col_map,
        kpis=kpis,
        churn_summary=churn_summary,
        forecast_summary=forecast_summary
    )

    st.session_state["business_insights"] = insights

    # Filter Toolbar
    render_section_header("Insight Filtering & Categorization", subtitle="Filter evidence by operational domain and risk level.")

    f_col1, f_col2 = st.columns(2)
    with f_col1:
        categories = ["All Categories"] + sorted(list(set(i.get("category", "General") for i in insights)))
        sel_cat = st.selectbox("Category", options=categories, index=0, key="ins_filter_cat")

    with f_col2:
        severities = ["All Severities", "positive", "warning", "risk", "neutral"]
        sel_sev = st.selectbox("Severity Level", options=severities, index=0, key="ins_filter_sev")

    filtered_insights = [
        i for i in insights
        if (sel_cat == "All Categories" or i.get("category") == sel_cat)
        and (sel_sev == "All Severities" or i.get("severity") == sel_sev)
    ]

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Tabs for Insight Cards vs Executive Briefing
    tab_cards, tab_brief = st.tabs([
        f"💡 Evidence-Based Findings ({len(filtered_insights)})",
        "📄 Executive Intelligence Briefing",
    ])

    with tab_cards:
        if not filtered_insights:
            st.info("No insights matching the selected filter criteria.")

        for ins in filtered_insights:
            sev = ins.get("severity", "neutral")
            if sev == "positive":
                border_color = tokens["success"]
                badge_bg = tokens["success_bg"]
                badge_color = tokens["success"]
            elif sev == "warning":
                border_color = tokens["warning"]
                badge_bg = tokens["warning_bg"]
                badge_color = tokens["warning"]
            elif sev == "risk":
                border_color = tokens["danger"]
                badge_bg = tokens["danger_bg"]
                badge_color = tokens["danger"]
            else:
                border_color = tokens["brand_primary"]
                badge_bg = tokens["brand_light"]
                badge_color = tokens["brand_primary"]

            actions_html = "".join([f"<li style='margin-bottom: 4px;'>{a}</li>" for a in ins.get("recommended_actions", [])])

            card_html = f"""
            <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-left: 4px solid {border_color}; border-radius: 12px; padding: 1.25rem 1.5rem; margin-bottom: 1.25rem; box-shadow: {tokens['card_shadow']};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.65rem;">
                    <span style="font-size: 1.1rem; font-weight: 700; color: {tokens['text_primary']};">{ins.get('title')}</span>
                    <span style="background: {badge_bg}; color: {badge_color}; font-size: 0.75rem; font-weight: 700; padding: 3px 10px; border-radius: 9999px; border: 1px solid {badge_color}33;">
                        {ins.get('category')} • {ins.get('supporting_metric')}
                    </span>
                </div>
                <div style="font-size: 0.9rem; color: {tokens['text_secondary']}; line-height: 1.55; margin-bottom: 0.75rem;">
                    <strong style="color: {tokens['text_primary']};">Observation:</strong> {ins.get('finding')}<br/>
                    <strong style="color: {tokens['text_primary']};">Analytical Interpretation:</strong> {ins.get('interpretation')}
                </div>
                <div style="background: {tokens['surface_subtle']}; border-radius: 8px; padding: 0.85rem 1rem; margin-bottom: 0.75rem; font-size: 0.85rem; color: {tokens['text_secondary']};">
                    <strong style="color: {tokens['text_primary']};">Recommended Action Steps:</strong>
                    <ul style="margin: 0.35rem 0 0 0; padding-left: 1.25rem; line-height: 1.5;">
                        {actions_html}
                    </ul>
                </div>
                <div style="display: flex; gap: 1rem; font-size: 0.775rem; color: {tokens['text_muted']}; border-top: 1px solid {tokens['border']}; padding-top: 0.5rem;">
                    <span><b>Baseline:</b> {ins.get('baseline_comparison')}</span>
                    <span>•</span>
                    <span><b>Boundary Condition:</b> {ins.get('limitations')}</span>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

    with tab_brief:
        render_section_header("Synthesized Executive Intelligence Briefing", subtitle="Structured C-Suite briefing synthesized from top active signals.")
        briefing_text = generate_llm_executive_summary(insights, kpis)
        st.markdown(
            f"""
            <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 12px; padding: 1.5rem; line-height: 1.6; color: {tokens['text_primary']}; box-shadow: {tokens['card_shadow']};">
                {briefing_text}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)
        # Export Insights as CSV
        ins_records = []
        for i in insights:
            ins_records.append({
                "Category": i.get("category"),
                "Title": i.get("title"),
                "Severity": i.get("severity"),
                "Finding": i.get("finding"),
                "Metric": i.get("supporting_metric"),
                "Interpretation": i.get("interpretation"),
                "Top_Recommendation": i.get("recommended_actions", [""])[0],
            })
        ins_df = pd.DataFrame(ins_records)
        csv_bytes = export_dataframe_to_csv_bytes(ins_df)
        st.download_button(
            label="⬇️ Export Insights Summary (CSV)",
            data=csv_bytes,
            file_name="insightiq_business_insights.csv",
            mime="text/csv",
        )

    render_methodology_disclaimer()
