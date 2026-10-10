"""
Ask InsightIQ - Conversational Data Analytics Copilot Page.
Allows business stakeholders to query datasets in natural language,
review safe AST-verified SQL, and interact with automatically generated charts.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from components.header import render_header
from components.ui_components import render_page_title, render_section_header, render_empty_state
from components.alerts import render_alert
from components.charts import apply_theme
from components.design_system import get_theme_tokens
from services.copilot import AnalyticsCopilotService
from services.report_generator import export_dataframe_to_csv_bytes


def render_ask_insightiq_page():
    """Render interactive conversational copilot interface."""
    render_header("Ask InsightIQ", "AI & Automation")

    df: pd.DataFrame = st.session_state.get("active_df")
    active_name = st.session_state.get("active_dataset_name", "Active Workspace Dataset")

    if df is None or df.empty:
        render_empty_state(
            title="No Active Dataset Loaded",
            description="Please load a demo dataset or upload a file from the sidebar to query via AI Copilot.",
            icon="💬"
        )
        return

    tokens = get_theme_tokens()
    render_page_title(
        "Ask InsightIQ Copilot",
        "Ask natural language business questions and receive instant deterministic SQL queries, data tables, and dynamic charts."
    )

    # Initialize Copilot Service & Chat History in Session State
    if "copilot_service" not in st.session_state:
        st.session_state["copilot_service"] = AnalyticsCopilotService()
    if "copilot_history" not in st.session_state:
        st.session_state["copilot_history"] = []

    copilot: AnalyticsCopilotService = st.session_state["copilot_service"]

    # Top Status & Context Banner
    stat_c1, stat_c2 = st.columns([3, 1])
    with stat_c1:
        st.markdown(
            f"""
            <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 10px; padding: 0.75rem 1.15rem; font-size: 0.85rem; color: {tokens['text_secondary']}; box-shadow: {tokens['card_shadow']};">
                Active Table: <code style="color: {tokens['brand_primary']}; font-weight: 600;">{active_name}</code> &nbsp;•&nbsp; 
                Scope: <strong style="color: {tokens['text_primary']};">{len(df):,}</strong> records &nbsp;•&nbsp; 
                Security: <span style="color: {tokens['success']}; font-weight: 600;">AST Verified (DuckDB)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with stat_c2:
        if st.button("🗑️ Clear History", use_container_width=True, help="Reset conversation history"):
            st.session_state["copilot_history"] = []
            st.rerun()

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Example Prompt Suggestions
    render_section_header("Suggested Business Questions", subtitle="Select a prompt to quickly explore dataset dynamics.")
    sug_cols = st.columns(4)
    suggested_queries = [
        "Which category generated highest profit?",
        "Top 5 products by revenue",
        "Monthly revenue trend over time",
        "Total revenue, orders, and average order value",
    ]

    selected_suggestion = None
    for idx, sq in enumerate(suggested_queries):
        with sug_cols[idx]:
            if st.button(sq, key=f"sug_btn_{idx}", use_container_width=True):
                with st.spinner("Analyzing inquiry, synthesizing validated SQL, and executing query..."):
                    result = copilot.ask(sq, df)
                    st.session_state["copilot_history"].insert(0, result)
                    st.rerun()

    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

    # Question Input Bar
    with st.form("copilot_query_form", clear_on_submit=False):
        user_query = st.text_input(
            "Ask a question about your business data:",
            value=selected_suggestion or "",
            placeholder="e.g., Which category has the highest profit margin? or Show top 5 products by revenue",
            key="copilot_text_input"
        )
        submit_btn = st.form_submit_button("🚀 Ask InsightIQ", type="primary")

    if submit_btn and user_query:
        with st.spinner("Analyzing inquiry, synthesizing validated SQL, and executing query..."):
            result = copilot.ask(user_query, df)
            st.session_state["copilot_history"].insert(0, result)

    # Render Chat History
    history = st.session_state.get("copilot_history", [])

    if not history:
        st.markdown(
            f"""
            <div style="background: {tokens['surface_subtle']}; border: 1px dashed {tokens['border']}; border-radius: 12px; padding: 2.5rem; text-align: center; margin-top: 1.5rem;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">💬</div>
                <div style="font-weight: 600; color: {tokens['text_primary']};">No queries submitted yet</div>
                <div style="font-size: 0.85rem; color: {tokens['text_secondary']}; margin-top: 4px;">Click any suggested prompt above or type a custom inquiry.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    render_section_header(f"Conversation Log ({len(history)} queries)", subtitle="Chronological history of questions and verified answers.")

    for idx, item in enumerate(history):
        is_success = item.get("success", False)

        with st.container():
            # Question Card
            st.markdown(
                f"""
                <div style="background: {tokens['brand_light']}; border-left: 4px solid {tokens['brand_primary']}; padding: 0.85rem 1.15rem; border-radius: 8px; margin-top: 1.25rem;">
                    <div style="font-size: 0.725rem; color: {tokens['brand_primary']}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;">User Inquiry</div>
                    <div style="font-size: 1.05rem; font-weight: 600; color: {tokens['text_primary']}; margin-top: 2px;">{item.get('question')}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if not is_success:
                st.error(item.get("error", "An error occurred during query execution."))
                if "blocked_sql" in item:
                    with st.expander("Inspect Blocked SQL"):
                        st.code(item["blocked_sql"], language="sql")
                continue

            # Assistant Answer Card
            st.markdown(
                f"""
                <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 10px; padding: 1.15rem 1.35rem; margin-top: 0.5rem; box-shadow: {tokens['card_shadow']};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="font-size: 0.775rem; font-weight: 700; color: {tokens['teal']}; text-transform: uppercase; letter-spacing: 0.04em;">
                            InsightIQ Copilot Answer ({item.get('provider_name')})
                        </span>
                        <span style="font-size: 0.75rem; color: {tokens['text_muted']};">
                            ⚡ Execution: {item.get('execution_time_ms', 0)}ms ({item.get('row_count', 0)} rows)
                        </span>
                    </div>
                    <div style="font-size: 0.95rem; color: {tokens['text_primary']}; line-height: 1.55;">
                        {item.get('response_text')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Chart and Table tabs
            res_df = item.get("result_df")
            fig = item.get("chart_fig")

            tab_viz, tab_data, tab_sql = st.tabs([
                f"📊 Visualization ({item.get('chart_type', 'Chart')})",
                f"📋 Tabular Data ({len(res_df) if res_df is not None else 0} rows)",
                "🛡️ Verified SQL Code",
            ])

            with tab_viz:
                if fig is not None:
                    fig = apply_theme(fig, height=360)
                    st.plotly_chart(fig, use_container_width=True, key=f"copilot_fig_{idx}")
                else:
                    st.info("Data is best viewed as a table.")
                    if res_df is not None:
                        st.dataframe(res_df, use_container_width=True)

            with tab_data:
                if res_df is not None:
                    st.dataframe(res_df, use_container_width=True)
                    csv_bytes = export_dataframe_to_csv_bytes(res_df)
                    st.download_button(
                        label="⬇️ Download Query Result (CSV)",
                        data=csv_bytes,
                        file_name=f"insightiq_query_result_{idx}.csv",
                        mime="text/csv",
                        key=f"dl_csv_{idx}"
                    )

            with tab_sql:
                st.code(item.get("sql", ""), language="sql")
                st.caption("Validated with SQLGlot AST parser. Enforced read-only SELECT against DuckDB.")
