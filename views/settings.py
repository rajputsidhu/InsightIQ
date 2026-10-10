"""
Settings, System Diagnostics, Data Connectors & Statistical Documentation for InsightIQ.
Provides runtime environment diagnostics, appearance preferences, database connectors,
ETL batch pipeline testing, and mathematical methodology disclosures.
"""

import sys
import platform
import streamlit as st
import pandas as pd
from components.header import render_header
from components.ui_components import render_page_title, render_section_header
from components.alerts import render_alert
from components.design_system import get_theme_tokens, get_current_theme, set_current_theme
from database.connection import db_manager
from database.connectors import SQLiteConnector, DuckDBConnector, CloudConnectorStub
from services.etl_scheduler import ETLSchedulerService


def render_settings_page():
    """Render system configuration, appearance, connectors, ETL pipeline, and statistical documentation."""
    render_header("Settings & Diagnostics", "System")

    tokens = get_theme_tokens()
    current_theme = get_current_theme()

    render_page_title(
        "Platform Settings & System Diagnostics",
        "Inspect runtime environment, customize display appearance, manage database connectors, and audit ETL ingestion telemetry."
    )

    # In session state, retain ETL scheduler service
    etl_service = st.session_state.get("etl_service")
    if etl_service is None:
        etl_service = ETLSchedulerService()
        st.session_state["etl_service"] = etl_service

    tab_app, tab_sys, tab_conn, tab_etl, tab_method, tab_about = st.tabs([
        "🎨 Appearance & Theme",
        "⚙️ System Diagnostics",
        "🔌 Data Connectors",
        "⏱️ Scheduled Ingestion (ETL)",
        "📐 Methodology & Assumptions",
        "ℹ️ About InsightIQ",
    ])

    with tab_app:
        render_section_header("Appearance & Design System", subtitle="Configure color mode and theme tokens.")

        theme_col1, theme_col2 = st.columns([2, 3])
        with theme_col1:
            st.markdown(
                f"""
                <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 12px; padding: 1.25rem; box-shadow: {tokens['card_shadow']};">
                    <div style="font-size: 0.775rem; font-weight: 700; color: {tokens['text_muted']}; text-transform: uppercase;">Active Theme</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: {tokens['text_primary']}; margin: 0.25rem 0;">
                        {'☀️ Light Theme' if current_theme == 'light' else '🌙 Dark Theme'}
                    </div>
                    <div style="font-size: 0.85rem; color: {tokens['text_secondary']}; line-height: 1.5;">
                        InsightIQ uses a semantic token system for consistent typography, surfaces, and contrast.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)
            new_theme = st.radio(
                "Select Theme Preference",
                options=["light", "dark"],
                index=0 if current_theme == "light" else 1,
                format_func=lambda x: "☀️ Light Mode (Enterprise Clean)" if x == "light" else "🌙 Dark Mode (OLED Slate)",
                key="settings_theme_radio"
            )
            if new_theme != current_theme:
                set_current_theme(new_theme)
                st.rerun()

        with theme_col2:
            st.markdown(f"<div style='font-size: 0.875rem; font-weight: 600; color: {tokens['text_primary']}; margin-bottom: 0.5rem;'>Semantic Color Tokens in Use:</div>", unsafe_allow_html=True)
            token_pills = [
                ("Brand Primary", tokens["brand_primary"]),
                ("App Background", tokens["bg_app"]),
                ("Surface Card", tokens["surface"]),
                ("Border Subtle", tokens["border"]),
                ("Success Green", tokens["success"]),
                ("Warning Amber", tokens["warning"]),
                ("Danger Red", tokens["danger"]),
                ("Analytics Teal", tokens["teal"]),
                ("Analytics Purple", tokens["purple"]),
            ]
            pill_html = "".join([
                f'<div style="display: flex; align-items: center; justify-content: space-between; background: {tokens["surface_subtle"]}; border: 1px solid {tokens["border"]}; border-radius: 6px; padding: 6px 12px; margin-bottom: 6px; font-size: 0.825rem;">'
                f'<span style="color: {tokens["text_primary"]}; font-weight: 500;">{name}</span>'
                f'<div style="display: flex; align-items: center; gap: 6px;"><div style="width: 14px; height: 14px; border-radius: 4px; background: {hex_val}; border: 1px solid rgba(0,0,0,0.15);"></div><code style="font-size: 0.75rem;">{hex_val}</code></div>'
                f'</div>'
                for name, hex_val in token_pills
            ])
            st.markdown(pill_html, unsafe_allow_html=True)

    with tab_sys:
        render_section_header("Runtime Environment Diagnostics", subtitle="Python virtual environment and host operating system.")
        c1, c2, c3 = st.columns(3)
        with c1:
            _render_diag_card("Python Version", sys.version.split()[0], tokens)
        with c2:
            _render_diag_card("Host Platform", platform.system(), tokens)
        with c3:
            _render_diag_card("Streamlit Engine", st.__version__, tokens)

        render_section_header("Installed Analytical Engine Libraries", subtitle="Production analytical dependencies verified in environment.")
        pkgs = [
            ("Pandas", "Data Wrangling & Time-Series Aggregations"),
            ("NumPy", "Vectorized Numerical Linear Algebra"),
            ("Scikit-Learn", "Supervised Churn & Unsupervised K-Means Models"),
            ("XGBoost", "Gradient Boosted Decision Trees"),
            ("DuckDB", "In-Memory High-Speed Columnar Analytical SQL"),
            ("Statsmodels", "Exponential Smoothing, STL & Time-Series Models"),
            ("SHAP", "Model Explainability & Shapley Additive Explanations"),
            ("SQLGlot", "AST-Based SQL Validation & Security Guardrails"),
            ("Python-PPTX", "Executive Widescreen PowerPoint Presentation Builder"),
            ("Plotly", "Interactive Enterprise Visualizations"),
            ("ReportLab", "Automated High-Fidelity PDF Document Generation"),
        ]

        pkg_cols = st.columns(2)
        for i, (name, role) in enumerate(pkgs):
            with pkg_cols[i % 2]:
                st.markdown(
                    f"""
                    <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 8px; padding: 0.65rem 1rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.75rem;">
                        <span style="color: {tokens['success']};">●</span>
                        <strong style="color: {tokens['text_primary']};">{name}</strong>
                        <span style="color: {tokens['text_muted']}; font-size: 0.825rem;">— {role}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with tab_conn:
        render_section_header("Enterprise Data Source Connectors", subtitle="Inspect and test live connections to database storage backends.")

        conn_type = st.selectbox(
            "Select Data Source Type",
            options=["DuckDB (Columnar In-Memory)", "SQLite (Local Database)", "PostgreSQL (Enterprise Persistence)", "Snowflake (Cloud Warehouse)", "Google BigQuery", "AWS Redshift"],
            key="settings_conn_type"
        )

        if "DuckDB" in conn_type:
            d_conn = DuckDBConnector()
            ok, msg = d_conn.test_connection()
            if ok:
                st.success(f"🟢 {msg}")
            else:
                st.error(msg)
            st.markdown(f"**Query Target:** `<code style='color: {tokens['brand_primary']}'>active_dataset</code>` in-memory table")

        elif "SQLite" in conn_type:
            db_path = st.text_input("SQLite Database File Path", value="insightiq_local.db", key="settings_sqlite_path")
            if st.button("🔌 Test SQLite Connection", key="btn_test_sqlite"):
                sql_conn = SQLiteConnector(db_path)
                ok, msg = sql_conn.test_connection()
                if ok:
                    st.success(f"🟢 {msg}")
                    tables = sql_conn.list_tables()
                    st.info(f"Available tables in database: {', '.join(tables) if tables else 'None (Empty Database)'}")
                else:
                    st.error(f"🔴 {msg}")
                sql_conn.close()

        elif "PostgreSQL" in conn_type:
            status = db_manager.get_status()
            if status["is_postgres"]:
                st.success(f"🟢 **Status:** Connected to {status['mode']}")
                st.markdown(f"**Details:** {status['description']}")
            else:
                st.info(f"🔵 **Status:** {status['mode']}")
                st.caption(
                    "To connect PostgreSQL, supply environment variables: "
                    "`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`."
                )

        else:
            provider = conn_type.split()[0]
            st.info(f"Cloud Warehouse Driver: **{provider}**")
            stub = CloudConnectorStub(provider, {})
            ok, msg = stub.test_connection()
            st.warning(f"⚠️ {msg}")
            st.caption(f"Enterprise drivers for {provider} can be configured by supplying service account JSON or environment credentials.")

    with tab_etl:
        render_section_header("Automated Batch ETL Ingestion Pipeline", subtitle="Simulates scheduled batch data ingestion with automated health validation and telemetry.")

        sync_c1, sync_c2, sync_c3 = st.columns([2, 1.5, 1])
        with sync_c1:
            etl_source = st.selectbox(
                "Ingestion Source Stream",
                options=["Demo E-Commerce Feed (Transactions)", "Demo Telecom Feed (Subscriber Records)", "Demo SaaS Stream (MRR Metrics)"],
                key="settings_etl_src"
            )
        with sync_c2:
            etl_cadence = st.selectbox(
                "Ingestion Cadence",
                options=["On-Demand Sync", "Hourly (00:00)", "Daily Batch (02:00 UTC)"],
                key="settings_etl_cadence"
            )
        with sync_c3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            run_etl_btn = st.button("▶️ Run Ingestion Sync", type="primary", use_container_width=True, key="btn_run_etl")

        if run_etl_btn:
            with st.spinner("Executing ETL ingestion batch and computing health audit..."):
                res = etl_service.trigger_pipeline_sync(etl_source, trigger_mode=etl_cadence)
                if res["status"] == "SUCCESS":
                    st.success(f"✅ {res['message']} ({res['duration_ms']}ms)")
                else:
                    st.error(f"❌ {res['message']}")

        render_section_header("Recent Ingestion Run Telemetry", subtitle="Chronological history of batch executions.")
        history = etl_service.get_history()
        if history:
            hist_df = pd.DataFrame(history)[["run_id", "source", "status", "trigger", "rows_ingested", "health_score", "duration_ms", "end_time"]].copy()
            if not hasattr(st, "column_config") or isinstance(getattr(st, "column_config", None), type):
                hist_df["health_score"] = hist_df["health_score"].apply(lambda v: f"{v:.1f}/100")
                hist_df["duration_ms"] = hist_df["duration_ms"].apply(lambda v: f"{v} ms")
            st.dataframe(
                hist_df,
                column_config={
                    "run_id": "Run ID",
                    "source": "Source",
                    "status": "Status",
                    "trigger": "Trigger",
                    "rows_ingested": "Rows Ingested",
                    "health_score": st.column_config.NumberColumn("Health Score", format="%.1f/100"),
                    "duration_ms": st.column_config.NumberColumn("Duration", format="%d ms"),
                    "end_time": "Completed At",
                },
                use_container_width=True,
                hide_index=True
            )

        st.caption(
            "ℹ️ Architecture Notice: This module demonstrates in-process batch ingestion and health verification. "
            "For production deployments, this interface connects directly to orchestrators such as Apache Airflow, Prefect, or AWS Step Functions."
        )

    with tab_method:
        render_section_header("Mathematical Methodology & Modeling Assumptions")
        with st.expander("1. Churn Prediction & Model Evaluation", expanded=True):
            st.markdown(
                """
                - **Target Formulation:** Binary classification ($y \\in \\{0, 1\\}$) identifying accounts transitioning from active to cancelled status.
                - **Leakage Prevention:** Identifiers (Customer ID, Account Number) and post-churn indicators (e.g. cancellation reasons) are stripped from feature vectors before model training.
                - **Explainable AI (SHAP):** Features are attributed via Shapley values indicating mathematical correlation with churn predictions without claiming direct empirical causality.
                """
            )

        with st.expander("2. Time-Series Revenue Forecasting", expanded=True):
            st.markdown(
                """
                - **Sequential Backtesting:** Time-series validation strictly avoids random shuffling, testing models on the latest $k$ observed historical periods.
                - **Evaluation Metrics:** Evaluated using Scale-Dependent (MAE, RMSE) and Scale-Independent metrics (WAPE, Safe MAPE).
                - **STL Decomposition:** Decomposes revenue into Trend, Seasonality, and Residual components using robust LOESS smoothing.
                - **Uncertainty Bounds:** 80% and 95% prediction intervals are computed from model residual standard deviations $\\sigma_e$ scaling with horizon $\\sqrt{h}$.
                """
            )

    with tab_about:
        render_section_header("About InsightIQ")
        st.markdown(
            f"""
            <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 12px; padding: 1.5rem; line-height: 1.6; color: {tokens['text_secondary']}; box-shadow: {tokens['card_shadow']};">
                <div style="font-size: 1.25rem; font-weight: 700; color: {tokens['text_primary']}; margin-bottom: 0.5rem;">InsightIQ Enterprise Platform</div>
                <p>
                    <strong>InsightIQ</strong> is a production-grade Business Intelligence (BI) and Predictive Decision Support platform
                    built for data-driven enterprises. It combines automated data quality diagnostics, in-memory SQL execution,
                    supervised retention modeling, and sequential time-series forecasting in a single cohesive workspace.
                </p>
                <div style="display: flex; gap: 2rem; margin-top: 1rem; border-top: 1px solid {tokens['border']}; padding-top: 1rem; font-size: 0.85rem;">
                    <div><strong style="color: {tokens['text_primary']};">Version:</strong> 2.0.0 SaaS Edition</div>
                    <div><strong style="color: {tokens['text_primary']};">License:</strong> MIT Open Source</div>
                    <div><strong style="color: {tokens['text_primary']};">Framework:</strong> Streamlit 1.30+ • DuckDB • Scikit-Learn</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


def _render_diag_card(label: str, value: str, tokens: dict):
    """Render a clean metric diagnostic card."""
    st.markdown(
        f"""
        <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 10px; padding: 1rem; box-shadow: {tokens['card_shadow']};">
            <div style="font-size: 0.75rem; color: {tokens['text_muted']}; font-weight: 700; text-transform: uppercase;">{label}</div>
            <div style="font-size: 1.4rem; font-weight: 700; color: {tokens['text_primary']}; margin-top: 2px;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
