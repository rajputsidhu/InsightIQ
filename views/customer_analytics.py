"""
Customer Analytics & RFM Segmentation Page for InsightIQ.
Provides customer behavioral segmentation, unsupervised K-Means clustering,
and probabilistic Customer Lifetime Value (CLV) projections.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from components.header import render_header
from components.ui_components import render_page_title, render_section_header, render_empty_state
from components.kpi_cards import render_kpi_card
from components.charts import plot_rfm_scatter, plot_cluster_profiles, apply_theme
from components.alerts import render_alert, render_methodology_disclaimer
from components.design_system import get_theme_tokens
from services.business_metrics import infer_business_columns
from services.customer_analysis import compute_rfm_metrics, run_kmeans_clustering
from services.report_generator import export_dataframe_to_csv_bytes


def render_customer_analytics_page():
    """Render customer segmentation, RFM analysis, and CLV modeling."""
    render_header("Customer Analytics", "Analytics")

    df: pd.DataFrame = st.session_state.get("active_df")

    if df is None or df.empty:
        render_empty_state(
            title="No Active Dataset Loaded",
            description="Please load a transaction or order dataset (such as 'Demo E-Commerce Orders') from the sidebar.",
            icon="👥"
        )
        return

    tokens = get_theme_tokens()
    col_map = st.session_state.get("col_map") or infer_business_columns(df)
    cust_col = col_map.get("customer_id")
    date_col = col_map.get("date")
    rev_col = col_map.get("revenue")
    order_col = col_map.get("order_id")

    if not cust_col or cust_col not in df.columns or not date_col or date_col not in df.columns or not rev_col or rev_col not in df.columns:
        render_alert(
            "Customer Analytics requires Customer ID, Date, and Revenue columns. "
            "Please select an appropriate dataset like 'Demo E-Commerce Orders' from the sidebar.",
            level="warning",
            title="Required Columns Missing"
        )
        return

    render_page_title(
        "Customer Intelligence & Segmentation",
        "Analyze purchasing recency, frequency, monetary value (RFM), K-Means behavioral cohorts, and 2-year CLV projections."
    )

    # Compute RFM metrics
    rfm_df = compute_rfm_metrics(df, cust_col, date_col, rev_col, order_col)

    if rfm_df.empty:
        st.error("Failed to compute customer metrics. Ensure date and monetary values are properly formatted.")
        return

    # Top KPI Metrics Grid
    render_section_header("Customer Base Benchmarks", subtitle="Aggregate population metrics across distinct buyer accounts.", badge="RFM Engine")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card("Total Customers", f"{len(rfm_df):,}", "Unique Accounts", accent="blue")
    with k2:
        render_kpi_card("Avg Spend / Customer", f"${rfm_df['monetary'].mean():,.2f}", "Historical Monetary", accent="teal")
    with k3:
        render_kpi_card("Avg Order Frequency", f"{rfm_df['frequency'].mean():.1f}", "Orders per Account", accent="green")
    with k4:
        render_kpi_card("Avg Recency", f"{rfm_df['recency'].mean():.0f} days", "Since Last Order", accent="amber")

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # Tabs for RFM Segmentation vs K-Means vs CLV
    tab_rfm, tab_kmeans, tab_clv = st.tabs([
        "🎯 RFM Segmentation & Behavior",
        "🤖 K-Means Clustering Model",
        "💰 Customer Lifetime Value (CLV)",
    ])

    with tab_rfm:
        render_section_header("Customer Behavioral Segments", subtitle="Standardized RFM behavioral classification rules.")
        
        seg_counts = rfm_df["rfm_segment"].value_counts().reset_index()
        seg_counts.columns = ["Segment", "Customer Count"]
        seg_counts["Share %"] = (seg_counts["Customer Count"] / len(rfm_df) * 100).round(1)

        col_s1, col_s2 = st.columns([2, 3])
        with col_s1:
            st.dataframe(
                seg_counts,
                column_config={
                    "Share %": st.column_config.NumberColumn(format="%.1f%%"),
                },
                use_container_width=True,
                hide_index=True,
            )

        with col_s2:
            fig_pie = px.pie(
                seg_counts,
                names="Segment",
                values="Customer Count",
                title="Customer Segment Distribution",
                hole=0.45,
                color_discrete_sequence=[
                    tokens.get("brand_primary", "#4F46E5"),
                    tokens.get("teal", "#14B8A6"),
                    tokens.get("purple", "#8B5CF6"),
                    tokens.get("warning", "#F59E0B"),
                    tokens.get("blue_secondary", tokens.get("secondary_blue", tokens.get("blue", "#3B82F6"))),
                    tokens.get("danger", "#EF4444")
                ],
            )
            fig_pie = apply_theme(fig_pie, height=300)
            st.plotly_chart(fig_pie, use_container_width=True)

        render_section_header("Recency vs. Monetary Distribution", subtitle="Bi-dimensional scatter plot highlighting spend density by inactivity days.")
        fig_scatter = plot_rfm_scatter(rfm_df)
        st.plotly_chart(fig_scatter, use_container_width=True)

    with tab_kmeans:
        render_section_header("Unsupervised K-Means Customer Clustering", subtitle="Machine-learning driven customer groupings based on standardized features.")
        render_alert(
            "K-Means clusters are empirical mathematical groupings derived from standardized Recency, Frequency, "
            "and Monetary features. They should be validated against qualitative business context.",
            level="info",
            title="Methodological Notice"
        )

        cluster_col1, cluster_col2 = st.columns([1, 3])
        with cluster_col1:
            k_val = st.slider("Select Number of Clusters (k)", min_value=2, max_value=6, value=4, key="kmeans_k_slider")

        clustered_df, cluster_meta = run_kmeans_clustering(rfm_df, n_clusters=k_val)

        if "cluster_profiles_df" in cluster_meta:
            prof_df = cluster_meta["cluster_profiles_df"]
            st.markdown(
                f"""
                <div style="background: {tokens['surface_subtle']}; border: 1px solid {tokens['border']}; border-radius: 8px; padding: 0.5rem 1rem; font-size: 0.85rem; margin-bottom: 1rem; color: {tokens['text_secondary']};">
                    Silhouette Score: <strong style="color: {tokens['text_primary']};">{cluster_meta.get('silhouette_score', 'N/A')}</strong> (Mathematical clustering cohesion)
                </div>
                """,
                unsafe_allow_html=True
            )

            st.dataframe(
                prof_df,
                column_config={
                    "customer_count": "Customers",
                    "avg_recency": st.column_config.NumberColumn("Avg Recency (Days)", format="%.0f d"),
                    "avg_frequency": st.column_config.NumberColumn("Avg Orders", format="%.1f"),
                    "avg_monetary": st.column_config.NumberColumn("Avg Spend", format="$%.2f"),
                    "total_revenue": st.column_config.NumberColumn("Total Revenue", format="$%.2f"),
                    "revenue_share_pct": st.column_config.NumberColumn("Revenue Share", format="%.1f%%"),
                },
                use_container_width=True,
                hide_index=True,
            )

            fig_clust = plot_cluster_profiles(prof_df)
            st.plotly_chart(fig_clust, use_container_width=True)

    with tab_clv:
        render_section_header("2-Year Customer Lifetime Value (CLV) Projections", subtitle="Parametric longevity and monetary value modeling.")
        render_alert(
            "Estimated CLV is calculated using historical order cadence, average order values, and estimated gross margin. "
            "CLV values represent statistical projections rather than guaranteed revenues.",
            level="warning",
            title="Projection Disclaimer"
        )

        clv_c1, clv_c2 = st.columns([2, 3])
        with clv_c1:
            st.metric("Mean Projected 2-Yr CLV", f"${rfm_df['estimated_clv_2yr'].mean():,.2f}")
            st.metric("Top 10% Accounts CLV", f"${rfm_df['estimated_clv_2yr'].quantile(0.90):,.2f}")

        with clv_c2:
            fig_clv = px.histogram(
                rfm_df,
                x="estimated_clv_2yr",
                nbins=25,
                title="Projected 2-Year CLV Distribution",
                color_discrete_sequence=[tokens["teal"]],
                labels={"estimated_clv_2yr": "Estimated 2-Year CLV ($)"},
            )
            fig_clv = apply_theme(fig_clv, height=280)
            st.plotly_chart(fig_clv, use_container_width=True)

        top_clv_df = rfm_df.sort_values(by="estimated_clv_2yr", ascending=False).head(20)[[
            "customer_id", "monetary", "frequency", "recency", "rfm_segment", "estimated_clv_2yr"
        ]].copy()
        if not hasattr(st, "column_config") or isinstance(getattr(st, "column_config", None), type):
            top_clv_df["monetary"] = top_clv_df["monetary"].apply(lambda v: f"${v:,.2f}")
            top_clv_df["estimated_clv_2yr"] = top_clv_df["estimated_clv_2yr"].apply(lambda v: f"${v:,.2f}")
        st.dataframe(
            top_clv_df,
            column_config={
                "monetary": st.column_config.NumberColumn("Historical Spend", format="$%.2f"),
                "estimated_clv_2yr": st.column_config.NumberColumn("Projected 2-Yr CLV", format="$%.2f"),
            },
            use_container_width=True,
            hide_index=True,
        )

        csv_bytes = export_dataframe_to_csv_bytes(rfm_df)
        st.download_button(
            label="⬇️ Export Customer RFM & CLV Analysis (CSV)",
            data=csv_bytes,
            file_name="insightiq_customer_rfm_clv.csv",
            mime="text/csv",
        )

    render_methodology_disclaimer()
