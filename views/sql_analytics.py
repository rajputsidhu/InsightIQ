"""
SQL Analytics Studio Page for InsightIQ.
Executes high-performance analytical queries against active datasets using DuckDB/PostgreSQL
with schema inspection, SQL library templates, and execution telemetry.
"""

import os
import streamlit as st
import pandas as pd
from components.header import render_header
from components.ui_components import render_page_title, render_section_header, render_empty_state
from components.alerts import render_alert
from components.design_system import get_theme_tokens
from database.connection import db_manager
from database.repository import SQLRepository
from services.report_generator import export_dataframe_to_csv_bytes

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_DIR = os.path.join(BASE_DIR, "sql")


def _load_sql_file(filename: str) -> str:
    path = os.path.join(SQL_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "SELECT * FROM active_dataset LIMIT 10;"


def render_sql_analytics_page():
    """Render the SQL analytics workspace and query library."""
    render_header("SQL Analytics", "Analytics")

    df: pd.DataFrame = st.session_state.get("active_df")

    if df is None or df.empty:
        render_empty_state(
            title="No Active Dataset Registered",
            description="Load a demo dataset or upload a file from the sidebar to query via in-memory DuckDB.",
            icon="⚡"
        )
        return

    tokens = get_theme_tokens()
    render_page_title(
        "SQL Analytics Studio",
        "Author and execute analytical SQL queries directly against in-memory columnar tables or live PostgreSQL."
    )

    # Ensure table is registered in DuckDB
    db_manager.register_dataframe("active_dataset", df)
    status = db_manager.get_status()

    # Query Safety & Engine Info Banner
    engine_badge = "PostgreSQL Live" if status["is_postgres"] else "DuckDB Columnar In-Memory"
    badge_bg = tokens["success_bg"] if status["is_postgres"] else tokens["brand_light"]
    badge_fg = tokens["success"] if status["is_postgres"] else tokens["brand_primary"]

    st.markdown(
        f"""
        <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 12px; padding: 0.85rem 1.25rem; display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; box-shadow: {tokens['card_shadow']};">
            <div style="font-size: 0.875rem; color: {tokens['text_secondary']};">
                Table: <code style="color: {tokens['brand_primary']}; font-weight: 600;">active_dataset</code> &nbsp;•&nbsp; 
                Records: <strong style="color: {tokens['text_primary']};">{len(df):,}</strong> rows &nbsp;•&nbsp; 
                Mode: <span style="color: {tokens['text_primary']}; font-weight: 500;">Read-Only Analytical Sandbox</span>
            </div>
            <div>
                <span style="background: {badge_bg}; color: {badge_fg}; font-size: 0.775rem; font-weight: 600; padding: 3px 10px; border-radius: 9999px; border: 1px solid {badge_fg}33;">
                    ⚡ {engine_badge}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Saved Query Library
    saved_queries = {
        "Custom Query": "SELECT * FROM active_dataset LIMIT 15;",
        "Monthly Revenue & MoM Growth": _load_sql_file("revenue_analysis.sql"),
        "Customer Spending Quartiles": _load_sql_file("customer_analysis.sql"),
        "Monthly Cohort Retention": _load_sql_file("cohort_analysis.sql"),
        "Product Profitability & Margins": _load_sql_file("profitability_analysis.sql"),
        "SQL RFM Scoring": _load_sql_file("rfm_segmentation.sql"),
    }

    render_section_header("Query Workbench", subtitle="Select from pre-authored financial analytics templates or craft custom SQL.")

    lib_col1, lib_col2 = st.columns([3, 1])
    with lib_col1:
        selected_template = st.selectbox(
            "Pre-built SQL Analytical Query Library",
            options=list(saved_queries.keys()),
            index=1 if "Monthly Revenue & MoM Growth" in saved_queries else 0,
            key="sql_template_select",
        )

    with lib_col2:
        max_rows = st.selectbox("Row Limit", options=[100, 500, 1000, 5000], index=1, key="sql_max_rows")

    default_sql = saved_queries[selected_template]

    # SQL Editor Area
    query_input = st.text_area(
        "SQL Query Editor",
        value=default_sql,
        height=220,
        help="Execute standard SQL. Restricted to read-only analytical queries against 'active_dataset'.",
        key="sql_editor_text",
    )

    btn_col1, btn_col2, btn_col3 = st.columns([1.5, 2, 4])
    with btn_col1:
        run_clicked = st.button("▶️ Execute Query", type="primary", use_container_width=True)

    with btn_col2:
        if st.button("📋 Inspect Columns", use_container_width=True):
            st.session_state["show_schema_dialog"] = not st.session_state.get("show_schema_dialog", False)

    if st.session_state.get("show_schema_dialog"):
        clean_cols = [str(c).strip().replace(" ", "_").replace("-", "_").replace(".", "_") for c in df.columns]
        st.info(f"**Available Columns in `active_dataset`:**\n`{', '.join(clean_cols)}`")

    # Query Execution Logic
    if run_clicked or "last_query_result" in st.session_state:
        if run_clicked:
            with st.spinner("Executing analytical query..."):
                res_df, meta, err = SQLRepository.execute_query(query_input, row_limit=max_rows)
                st.session_state["last_query_result"] = res_df
                st.session_state["last_query_meta"] = meta
                st.session_state["last_query_error"] = err

        res_df = st.session_state.get("last_query_result")
        meta = st.session_state.get("last_query_meta", {})
        err = st.session_state.get("last_query_error")

        if err:
            render_alert(err, level="danger", title="Query Validation / Execution Error")
        elif res_df is not None:
            # Metadata Bar
            st.markdown(
                f"""
                <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; padding: 0.75rem 1.25rem; border-radius: 10px; font-size: 0.85rem; margin: 1.25rem 0; display: flex; gap: 2rem; box-shadow: {tokens['card_shadow']};">
                    <span>⏱️ <b style="color: {tokens['text_primary']};">Execution Time:</b> {meta.get('execution_time_ms', 0)} ms</span>
                    <span>📊 <b style="color: {tokens['text_primary']};">Rows:</b> {meta.get('rows_returned', 0):,}</span>
                    <span>📐 <b style="color: {tokens['text_primary']};">Columns:</b> {meta.get('columns_returned', 0)}</span>
                    <span>⚡ <b style="color: {tokens['text_primary']};">Engine:</b> {meta.get('engine', 'DuckDB')}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Results View
            render_section_header("Query Results Table", subtitle="Tabular dataset output with column sorting and export.")
            st.dataframe(res_df, use_container_width=True, hide_index=True)

            # Export Button
            csv_bytes = export_dataframe_to_csv_bytes(res_df)
            st.download_button(
                label="⬇️ Export Results as CSV",
                data=csv_bytes,
                file_name="insightiq_sql_results.csv",
                mime="text/csv",
            )
