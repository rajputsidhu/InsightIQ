"""
Sidebar Navigation and Dataset Management Component for InsightIQ.
Implements structured grouped navigation (Workspace, Analytics, AI, Reporting, System),
branded SaaS logo, high-contrast theme-aware styling, active dataset footer, and ingestion drawers.
"""

import streamlit as st
import pandas as pd
from services.data_loader import get_demo_dataset, load_dataset_from_bytes, profile_dataset
from services.business_metrics import infer_business_columns, calculate_executive_kpis
from database.connection import db_manager
from components.design_system import get_theme_tokens


PAGE_CONFIGS = [
    # (section, key, label, icon)
    ("Workspace", "Overview", "Overview", "📊"),
    ("Workspace", "Data Explorer", "Data Explorer", "📋"),
    ("Workspace", "Data Quality", "Data Quality", "🛡️"),
    ("Analytics", "SQL Analytics", "SQL Analytics", "⚡"),
    ("Analytics", "Customer Analytics", "Customer Analytics", "👥"),
    ("Analytics", "Churn Prediction", "Churn Prediction", "🎯"),
    ("Analytics", "Revenue Forecasting", "Revenue Forecasting", "📈"),
    ("Analytics", "Business Insights", "Business Insights", "💡"),
    ("AI", "Ask InsightIQ", "Ask InsightIQ", "💬"),
    ("Reporting", "Reports & Exports", "Reports & Exports", "📄"),
    ("System", "Settings & About", "Settings & About", "⚙️"),
]

PAGE_KEYS = [p[1] for p in PAGE_CONFIGS]
PAGE_ICONS = {p[1]: p[3] for p in PAGE_CONFIGS}
PAGE_SECTIONS = {p[1]: p[0] for p in PAGE_CONFIGS}


def render_sidebar() -> str:
    """Render the sidebar navigation and dataset controls, returning selected page name."""
    tokens = get_theme_tokens()

    with st.sidebar:
        # 1. Sidebar Brand Header (Theme-Aware: 44px square logo, indigo-to-violet gradient)
        st.markdown(
            f"""
            <div style="padding-bottom: 1rem; border-bottom: 1px solid {tokens['sidebar_border']}; margin-bottom: 1rem; padding-right: 36px;">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <div style="background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); color: #FFFFFF; width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.15rem; letter-spacing: -0.02em; flex-shrink: 0;">
                        IQ
                    </div>
                    <div style="min-width: 0; flex: 1;">
                        <div style="font-size: 1.15rem; font-weight: 700; color: {tokens['sidebar_text']}; letter-spacing: -0.02em; line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">InsightIQ</div>
                        <div style="font-size: 0.62rem; color: {tokens['sidebar_text_muted']}; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700; margin-top: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">ENTERPRISE INTELLIGENCE</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        current_page = st.session_state.get("current_page", "Overview")
        # Normalize in case older format with prefix was stored
        clean_current = current_page.split(". ", 1)[-1] if ". " in current_page else current_page
        if clean_current == "Data Quality & Cleaning":
            clean_current = "Data Quality"
        elif clean_current == "Ask InsightIQ Copilot":
            clean_current = "Ask InsightIQ"

        default_idx = PAGE_KEYS.index(clean_current) if clean_current in PAGE_KEYS else 0

        # 2. Main Navigation Menu (WORKSPACE Section Header)
        st.markdown(
            f"""
            <div style="font-size: 0.68rem; font-weight: 700; color: {tokens['sidebar_text_muted']}; text-transform: uppercase; letter-spacing: 0.08em; margin: 0 0 8px 10px;">
                WORKSPACE
            </div>
            """,
            unsafe_allow_html=True,
        )

        selected_page = st.radio(
            "Navigation Menu",
            options=PAGE_KEYS,
            index=default_idx,
            format_func=lambda k: f"{PAGE_ICONS.get(k, '•')}  {k}",
            label_visibility="collapsed",
            key="sb_radio_nav"
        )
        st.session_state["current_page"] = selected_page

        st.markdown(f"<div style='border-top: 1px solid {tokens['sidebar_border']}; margin: 1.5rem 0 1rem 0;'></div>", unsafe_allow_html=True)


        # 3. Active Dataset Ingestion & Switcher
        st.markdown(
            f"""
            <div style="font-size: 0.68rem; font-weight: 700; color: {tokens['sidebar_text_muted']}; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; padding-left: 0.2rem;">
                Data Feeds
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Quick Load Demo Datasets
        col_demo1, col_demo2 = st.columns(2)
        with col_demo1:
            if st.button("🛍️ Retail", use_container_width=True, help="1,250 multi-category e-commerce transactions"):
                df = get_demo_dataset("ecommerce")
                _set_active_dataset("Demo E-Commerce Orders", df)
                st.rerun()

        with col_demo2:
            if st.button("👥 Telco", use_container_width=True, help="1,100 customer subscription & churn records"):
                df = get_demo_dataset("churn")
                _set_active_dataset("Demo Telecom Churn", df)
                st.rerun()

        if st.button("📈 SaaS MRR Series", use_container_width=True, help="36 months of SaaS metric time-series"):
            df = get_demo_dataset("saas")
            _set_active_dataset("Demo SaaS Metrics", df)
            st.rerun()

        # File Uploader Drawer
        with st.expander("📤 Upload CSV/Excel"):
            uploaded_file = st.file_uploader(
                "Upload Dataset",
                type=["csv", "xlsx", "xls", "txt"],
                label_visibility="collapsed",
            )
            if uploaded_file is not None:
                file_bytes = uploaded_file.getvalue()
                df, err = load_dataset_from_bytes(file_bytes, uploaded_file.name)
                if err:
                    st.error(err)
                elif df is not None:
                    _set_active_dataset(uploaded_file.name, df)
                    st.success(f"Loaded {len(df):,} rows!")
                    st.rerun()

        st.markdown(f"<div style='border-top: 1px solid {tokens['sidebar_border']}; margin: 1.15rem 0 0.85rem 0;'></div>", unsafe_allow_html=True)

        # 4. Sidebar Footer with Real Metadata (Theme-Aware)
        active_name = st.session_state.get("active_dataset_name", "None")
        df_rows = len(st.session_state.get("raw_df", [])) if st.session_state.get("raw_df") is not None else 0

        st.markdown(
            f"""
            <div style="padding: 0.65rem 0.85rem; background: {tokens['surface_subtle']}; border: 1px solid {tokens['sidebar_border']}; border-radius: 8px;">
                <div style="font-size: 0.68rem; color: {tokens['sidebar_text_muted']}; font-weight: 700; text-transform: uppercase;">Active Workspace Data</div>
                <div style="font-size: 0.85rem; font-weight: 600; color: {tokens['sidebar_text']}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 2px;">
                    {active_name}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px; font-size: 0.75rem; color: {tokens['sidebar_text_muted']};">
                    <span>{df_rows:,} records</span>
                    <span style="color: {tokens['brand_primary']}; font-weight: 600;">v2.0 SaaS</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        return selected_page


def _set_active_dataset(name: str, df: pd.DataFrame):
    """Set active dataset and initialize derived profile and SQL tables."""
    st.session_state["raw_df"] = df
    st.session_state["active_df"] = df.copy()
    st.session_state["active_dataset_name"] = name
    st.session_state["dataset_profile"] = profile_dataset(df)
    st.session_state["col_map"] = infer_business_columns(df)
    st.session_state["kpis"] = calculate_executive_kpis(df, st.session_state["col_map"])
    db_manager.register_dataframe("active_dataset", df)
