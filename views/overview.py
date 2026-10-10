"""
Executive Overview Dashboard Page for InsightIQ.
High-impact enterprise SaaS interface displaying KPIs, financial trends,
category performance, and top product margins.
"""

import streamlit as st
import pandas as pd
from components.header import render_header
from components.ui_components import render_page_title, render_section_header
from components.kpi_cards import render_kpi_card
from components.charts import (
    plot_revenue_profit_trend,
    plot_category_breakdown,
    plot_top_products,
)
from components.alerts import render_alert
from components.design_system import get_theme_tokens
from services.business_metrics import (
    compute_time_series_aggregation,
    compute_category_breakdown,
    compute_top_products,
    infer_business_columns,
    calculate_executive_kpis,
)
from services.data_loader import get_demo_dataset


def render_overview_page():
    """Render the main executive overview dashboard."""
    render_header("Executive Overview", "Workspace")

    df: pd.DataFrame = st.session_state.get("active_df")

    # If no dataset loaded, render welcoming landing view with quick actions
    if df is None or df.empty:
        _render_welcome_hero()
        return

    tokens = get_theme_tokens()
    render_page_title(
        "Executive Overview",
        "Monitor revenue, profitability, order performance, and customer engagement in real time."
    )

    col_map = st.session_state.get("col_map") or infer_business_columns(df)

    # Initialize filter session states if not present
    if "overview_filter_cat" not in st.session_state:
        st.session_state["overview_filter_cat"] = "All Categories"
    if "overview_filter_reg" not in st.session_state:
        st.session_state["overview_filter_reg"] = "All Regions"

    # Filter Toolbar
    st.markdown(
        f"""
        <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 12px; padding: 1rem 1.25rem; margin-bottom: 1.5rem; box-shadow: {tokens['card_shadow']};">
            <div style="font-size: 0.775rem; font-weight: 700; color: {tokens['text_muted']}; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">
                Filters & Segmentation
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    has_cat = bool(col_map.get("category") and col_map["category"] in df.columns)
    has_reg = bool(col_map.get("region") and col_map["region"] in df.columns)

    f_col1, f_col2, f_col3, f_col4 = st.columns([2, 2, 2, 1.2])

    with f_col1:
        if has_cat:
            cats = ["All Categories"] + sorted(list(df[col_map["category"]].dropna().unique()))
            # Ensure saved value exists in list
            if st.session_state["overview_filter_cat"] not in cats:
                st.session_state["overview_filter_cat"] = "All Categories"
            sel_cat = st.selectbox(
                "Category",
                options=cats,
                key="overview_filter_cat",
                help="Filter metrics and charts by product category",
            )
        else:
            st.selectbox("Category", options=["Not Available in Dataset"], disabled=True)
            sel_cat = "All Categories"

    with f_col2:
        if has_reg:
            regs = ["All Regions"] + sorted(list(df[col_map["region"]].dropna().unique()))
            if st.session_state["overview_filter_reg"] not in regs:
                st.session_state["overview_filter_reg"] = "All Regions"
            sel_reg = st.selectbox(
                "Region",
                options=regs,
                key="overview_filter_reg",
                help="Filter metrics and charts by geographical region",
            )
        else:
            st.selectbox("Region", options=["Not Available in Dataset"], disabled=True)
            sel_reg = "All Regions"

    with f_col3:
        # Date range indicator or info
        if col_map.get("date") and col_map["date"] in df.columns:
            try:
                date_series = pd.to_datetime(df[col_map["date"]].dropna())
                date_span = f"{date_series.min().strftime('%b %Y')} – {date_series.max().strftime('%b %Y')}"
            except Exception:
                date_span = "All Available Time"
            st.text_input("Active Period", value=date_span, disabled=True, help="Historical time window covered by dataset")
        else:
            st.text_input("Active Period", value="Full Dataset Scope", disabled=True)

    with f_col4:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Reset", key="overview_btn_reset", use_container_width=True, help="Reset all filters to default"):
            st.session_state["overview_filter_cat"] = "All Categories"
            st.session_state["overview_filter_reg"] = "All Regions"
            st.rerun()

    # Apply filters
    filtered_df = df.copy()
    if sel_cat != "All Categories" and has_cat:
        filtered_df = filtered_df[filtered_df[col_map["category"]] == sel_cat]
    if sel_reg != "All Regions" and has_reg:
        filtered_df = filtered_df[filtered_df[col_map["region"]] == sel_reg]

    filtered_kpis = calculate_executive_kpis(filtered_df, col_map)

    # Compute monthly trends for KPI sparklines
    ts_df = compute_time_series_aggregation(filtered_df, col_map, freq="MS")
    rev_spark = ts_df["revenue"].tolist() if not ts_df.empty and "revenue" in ts_df.columns else None
    profit_spark = ts_df["profit"].tolist() if not ts_df.empty and "profit" in ts_df.columns else None
    orders_spark = ts_df["orders"].tolist() if not ts_df.empty and "orders" in ts_df.columns else None

    # Executive KPI Grid
    render_section_header(
        "Executive Key Performance Indicators",
        subtitle=f"Showing performance metrics computed across {len(filtered_df):,} matching transactions.",
        badge="Live Metrics"
    )

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        rev_str = f"${filtered_kpis['total_revenue']:,.2f}" if filtered_kpis.get("total_revenue") is not None else "N/A"
        growth_val = filtered_kpis.get("revenue_growth_pct")
        delta_str = f"{growth_val:+.1f}% vs prev period" if growth_val is not None else None
        render_kpi_card(
            label="Total Net Revenue",
            value=rev_str,
            subtext="Period Volume",
            delta=delta_str,
            delta_positive=(growth_val or 0) >= 0,
            accent="blue",
            sparkline_data=rev_spark,
        )

    with kpi_col2:
        orders_str = f"{filtered_kpis['total_orders']:,}" if filtered_kpis.get("total_orders") is not None else "N/A"
        aov_str = f"AOV: ${filtered_kpis['average_order_value']:,.2f}" if filtered_kpis.get("average_order_value") is not None else "Total Orders"
        render_kpi_card(
            label="Total Orders",
            value=orders_str,
            subtext=aov_str,
            accent="teal",
            sparkline_data=orders_spark,
        )

    with kpi_col3:
        profit_str = f"${filtered_kpis['total_profit']:,.2f}" if filtered_kpis.get("total_profit") is not None else "N/A"
        margin_val = filtered_kpis.get("profit_margin_pct")
        margin_sub = f"Margin: {margin_val:.1f}%" if margin_val is not None else "Operating Profit"
        render_kpi_card(
            label="Net Profit",
            value=profit_str,
            subtext=margin_sub,
            accent="green",
            sparkline_data=profit_spark,
        )

    with kpi_col4:
        cust_str = f"{filtered_kpis['unique_customers']:,}" if filtered_kpis.get("unique_customers") is not None else "N/A"
        rep_val = filtered_kpis.get("repeat_customer_pct")
        rep_sub = f"Repeat Rate: {rep_val:.1f}%" if rep_val is not None else "Unique Accounts"
        render_kpi_card(
            label="Customer Reach",
            value=cust_str,
            subtext=rep_sub,
            accent="purple",
        )

    # Explanation if any metrics were unsupported by dataset
    if filtered_kpis.get("unsupported_metrics"):
        render_alert(
            f"Some KPIs are not displayed because the active dataset lacks required columns: {', '.join(filtered_kpis['unsupported_metrics'])}.",
            level="info",
            title="Schema Notice",
        )

    # Charts Section
    render_section_header("Revenue Dynamics & Category Distribution", subtitle="Monthly revenue/profit trends and category volume breakdown.")

    chart_col1, chart_col2 = st.columns([3, 2])

    with chart_col1:
        if not ts_df.empty:
            fig_ts = plot_revenue_profit_trend(ts_df)
            st.plotly_chart(fig_ts, use_container_width=True)
        else:
            st.info("Time-series trend requires a valid Date and Numeric Revenue column.")

    with chart_col2:
        cat_df = compute_category_breakdown(filtered_df, col_map)
        if not cat_df.empty:
            fig_cat = plot_category_breakdown(cat_df)
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("Category breakdown requires a Category and Revenue column.")

    # Top Products and Performance Breakdown
    render_section_header("Product Performance & Margin Ranking", subtitle="Detailed margin breakdown and ranking for highest-earning catalog items.")

    prod_col1, prod_col2 = st.columns([3, 2])
    with prod_col1:
        top_prod_df = compute_top_products(filtered_df, col_map, top_n=8)
        if not top_prod_df.empty:
            fig_prod = plot_top_products(top_prod_df)
            st.plotly_chart(fig_prod, use_container_width=True)
        else:
            st.info("Product performance requires Product Name and Revenue columns.")

    with prod_col2:
        if not top_prod_df.empty:
            st.markdown(f"<div style='font-size: 0.875rem; font-weight: 600; color: {tokens['text_primary']}; margin-bottom: 0.5rem;'>Top Revenue Products</div>", unsafe_allow_html=True)
            disp_df = top_prod_df.copy()
            if not hasattr(st, "column_config") or isinstance(getattr(st, "column_config", None), type):
                if "Revenue" in disp_df.columns and pd.api.types.is_numeric_dtype(disp_df["Revenue"]):
                    disp_df["Revenue"] = disp_df["Revenue"].apply(lambda v: f"${v:,.2f}")
                if "Profit" in disp_df.columns and pd.api.types.is_numeric_dtype(disp_df["Profit"]):
                    disp_df["Profit"] = disp_df["Profit"].apply(lambda v: f"${v:,.2f}")
                if "Margin %" in disp_df.columns and pd.api.types.is_numeric_dtype(disp_df["Margin %"]):
                    disp_df["Margin %"] = disp_df["Margin %"].apply(lambda v: f"{v:.1f}%")
            st.dataframe(
                disp_df,
                column_config={
                    "Revenue": st.column_config.NumberColumn(format="$%.2f"),
                    "Profit": st.column_config.NumberColumn(format="$%.2f"),
                    "Margin %": st.column_config.NumberColumn(format="%.1f%%"),
                },
                use_container_width=True,
                hide_index=True,
            )


def _render_welcome_hero():
    """Render landing welcome view when no dataset is loaded."""
    tokens = get_theme_tokens()
    st.markdown(
        f"""
        <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 16px; padding: 3rem 2.5rem; text-align: center; margin-bottom: 2rem; box-shadow: {tokens['card_shadow']};">
            <div style="display: inline-block; background: {tokens['brand_light']}; color: {tokens['brand_primary']}; font-size: 0.775rem; font-weight: 700; padding: 4px 14px; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 1rem; border: 1px solid {tokens['border']};">
                AI-Powered Decision Support Platform
            </div>
            <h1 style="color: {tokens['text_primary']}; font-size: 2.25rem; font-weight: 800; letter-spacing: -0.03em; margin: 0 0 1rem 0; line-height: 1.2;">
                Turn Business Data into <span style="color: {tokens['brand_primary']};">Actionable Intelligence</span>
            </h1>
            <p style="color: {tokens['text_secondary']}; font-size: 1.05rem; max-width: 680px; margin: 0 auto; line-height: 1.6;">
                InsightIQ combines automated data validation, statistical analytics, supervised churn prediction, 
                and time-series revenue forecasting into a single unified business intelligence workspace.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Quick Start Cards
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        st.markdown(
            f"""
            <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 12px; padding: 1.5rem; min-height: 170px; margin-bottom: 1rem; box-shadow: {tokens['card_shadow']};">
                <div style="font-size: 1.75rem; margin-bottom: 0.5rem;">📊</div>
                <div style="color: {tokens['text_primary']}; font-weight: 700; font-size: 1.05rem; margin-bottom: 0.35rem;">E-Commerce Analytics</div>
                <div style="color: {tokens['text_secondary']}; font-size: 0.85rem; line-height: 1.5;">Analyze 1,250 multi-category retail orders with revenue, profit margins, RFM customer segmentation, and SQL queries.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🛍️ Explore E-Commerce Demo", key="hero_ecom", use_container_width=True):
            df = get_demo_dataset("ecommerce")
            from components.sidebar import _set_active_dataset
            _set_active_dataset("Demo E-Commerce Orders", df)
            st.rerun()

    with col_c2:
        st.markdown(
            f"""
            <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 12px; padding: 1.5rem; min-height: 170px; margin-bottom: 1rem; box-shadow: {tokens['card_shadow']};">
                <div style="font-size: 1.75rem; margin-bottom: 0.5rem;">👥</div>
                <div style="color: {tokens['text_primary']}; font-weight: 700; font-size: 1.05rem; margin-bottom: 0.35rem;">Customer Churn Prediction</div>
                <div style="color: {tokens['text_secondary']}; font-size: 0.85rem; line-height: 1.5;">Train and compare Logistic Regression, Random Forest, and XGBoost models with ROC-AUC curves and risk scoring.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🎯 Explore Telecom Churn Demo", key="hero_churn", use_container_width=True):
            df = get_demo_dataset("churn")
            from components.sidebar import _set_active_dataset
            _set_active_dataset("Demo Telecom Churn", df)
            st.session_state["current_page"] = "Churn Prediction"
            st.rerun()

    with col_c3:
        st.markdown(
            f"""
            <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 12px; padding: 1.5rem; min-height: 170px; margin-bottom: 1rem; box-shadow: {tokens['card_shadow']};">
                <div style="font-size: 1.75rem; margin-bottom: 0.5rem;">📈</div>
                <div style="color: {tokens['text_primary']}; font-weight: 700; font-size: 1.05rem; margin-bottom: 0.35rem;">Revenue Forecasting</div>
                <div style="color: {tokens['text_secondary']}; font-size: 0.85rem; line-height: 1.5;">Forecast monthly SaaS MRR trends using Exponential Smoothing and Moving Averages with confidence intervals.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🚀 Explore SaaS Forecast Demo", key="hero_saas", use_container_width=True):
            df = get_demo_dataset("saas")
            from components.sidebar import _set_active_dataset
            _set_active_dataset("Demo SaaS Metrics", df)
            st.session_state["current_page"] = "Revenue Forecasting"
            st.rerun()

    # Tech Stack Highlights
    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="text-align: center;">
            <div style="font-size: 0.775rem; font-weight: 700; color: {tokens['text_muted']}; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.75rem;">
                Built with Enterprise Open-Source Technologies
            </div>
            <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 0.5rem;">
                <span class="tech-badge">Python 3.10+</span>
                <span class="tech-badge">Streamlit</span>
                <span class="tech-badge">Pandas & NumPy</span>
                <span class="tech-badge">Scikit-Learn</span>
                <span class="tech-badge">XGBoost</span>
                <span class="tech-badge">DuckDB SQL</span>
                <span class="tech-badge">PostgreSQL</span>
                <span class="tech-badge">Plotly</span>
                <span class="tech-badge">Statsmodels</span>
                <span class="tech-badge">ReportLab PDF</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
