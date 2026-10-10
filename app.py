"""
InsightIQ - AI-Powered Business Intelligence & Decision Support Platform.
Main application entry point, multi-page router, and theme system coordinator.
"""

import os
import streamlit as st
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="InsightIQ • Business Intelligence Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSS_PATH = os.path.join(BASE_DIR, "assets", "style.css")

# Inject Static Stylesheet
if os.path.exists(CSS_PATH):
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Import Design System & Services
from components.design_system import inject_design_system_css, get_current_theme
from services.data_loader import get_demo_dataset, profile_dataset
from services.business_metrics import infer_business_columns, calculate_executive_kpis
from database.connection import db_manager

from components.sidebar import render_sidebar
from views.overview import render_overview_page
from views.data_explorer import render_data_explorer_page
from views.data_quality import render_data_quality_page
from views.sql_analytics import render_sql_analytics_page
from views.ask_insightiq import render_ask_insightiq_page
from views.customer_analytics import render_customer_analytics_page
from views.churn_prediction import render_churn_prediction_page
from views.revenue_forecasting import render_revenue_forecasting_page
from views.business_insights import render_business_insights_page
from views.reports import render_reports_page
from views.settings import render_settings_page


def init_session_state():
    """Initialize global session state with default theme and demo dataset."""
    if "theme" not in st.session_state:
        st.session_state["theme"] = "light"

    if "raw_df" not in st.session_state:
        default_df = get_demo_dataset("ecommerce")
        st.session_state["raw_df"] = default_df
        st.session_state["active_df"] = default_df.copy()
        st.session_state["active_dataset_name"] = "Demo E-Commerce Orders"
        st.session_state["dataset_profile"] = profile_dataset(default_df)
        st.session_state["col_map"] = infer_business_columns(default_df)
        st.session_state["kpis"] = calculate_executive_kpis(default_df, st.session_state["col_map"])
        db_manager.register_dataframe("active_dataset", default_df)


def main():
    """Main application loop and page router."""
    init_session_state()

    # Inject dynamic theme variables & styles
    inject_design_system_css()

    # Render Sidebar and retrieve active page selection
    selected_page = render_sidebar()

    # Clean selected page name
    clean_page = selected_page.split(". ", 1)[-1] if ". " in selected_page else selected_page
    if clean_page == "Data Quality & Cleaning":
        clean_page = "Data Quality"
    elif clean_page == "Ask InsightIQ Copilot":
        clean_page = "Ask InsightIQ"

    # Router
    if clean_page == "Overview":
        render_overview_page()
    elif clean_page == "Data Explorer":
        render_data_explorer_page()
    elif clean_page == "Data Quality":
        render_data_quality_page()
    elif clean_page == "SQL Analytics":
        render_sql_analytics_page()
    elif clean_page == "Ask InsightIQ":
        render_ask_insightiq_page()
    elif clean_page == "Customer Analytics":
        render_customer_analytics_page()
    elif clean_page == "Churn Prediction":
        render_churn_prediction_page()
    elif clean_page == "Revenue Forecasting":
        render_revenue_forecasting_page()
    elif clean_page == "Business Insights":
        render_business_insights_page()
    elif clean_page == "Reports & Exports":
        render_reports_page()
    elif clean_page == "Settings & About":
        render_settings_page()
    else:
        render_overview_page()


if __name__ == "__main__":
    main()
