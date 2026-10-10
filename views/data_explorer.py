"""
Interactive Data Explorer & Profiler Page for InsightIQ.
Provides comprehensive dataset inspection, column schemas, distribution histograms,
and numeric correlation matrices in a modern SaaS interface.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from components.header import render_header
from components.ui_components import render_page_title, render_section_header, render_empty_state
from components.tables import render_paginated_table
from components.charts import apply_theme
from components.design_system import get_theme_tokens
from services.data_loader import profile_dataset


def render_data_explorer_page():
    """Render data profiling and exploration tools."""
    render_header("Data Explorer", "Workspace")

    df: pd.DataFrame = st.session_state.get("active_df")

    if df is None or df.empty:
        render_empty_state(
            title="No Active Dataset Available",
            description="Load one of the curated demo datasets from the sidebar or upload your own CSV/Excel file to start exploring.",
            icon="📋"
        )
        return

    tokens = get_theme_tokens()
    render_page_title(
        "Data Explorer & Profiler",
        "Inspect data structures, audit column schemas, view statistical distributions, and analyze attribute correlations."
    )

    profile = st.session_state.get("dataset_profile") or profile_dataset(df)

    # Top Metric Counters in Card Grid
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        _render_stat_pill("Total Records", f"{profile['row_count']:,}", tokens["brand_primary"])
    with m2:
        _render_stat_pill("Total Columns", f"{profile['col_count']:,}", tokens["brand_primary"])
    with m3:
        _render_stat_pill("Memory Footprint", f"{profile['memory_mb']:.2f} MB", tokens["teal"])
    with m4:
        missing_color = tokens["warning"] if profile["missing_total"] > 0 else tokens["success"]
        _render_stat_pill("Missing Cells", f"{profile['missing_total']:,} ({profile['missing_pct']:.1f}%)", missing_color)
    with m5:
        dup_color = tokens["danger"] if profile["duplicate_count"] > 0 else tokens["success"]
        _render_stat_pill("Duplicate Rows", f"{profile['duplicate_count']:,}", dup_color)

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # Tabbed Explorer
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Dataset Viewer",
        "📊 Column Schema & Stats",
        "📈 Attribute Distributions",
        "🔥 Correlation Heatmap",
    ])

    with tab1:
        render_section_header("Tabular Records", subtitle="Search, filter, and inspect records across all dataset columns.")
        
        # Download button row
        d_col1, d_col2 = st.columns([4, 1])
        with d_col2:
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Export CSV",
                data=csv_data,
                file_name="insightiq_dataset_export.csv",
                mime="text/csv",
                use_container_width=True,
                help="Download full active dataset as CSV",
            )
        
        render_paginated_table(df, page_size=15, key_prefix="explorer_raw")

    with tab2:
        render_section_header("Column Metadata & Type Profiling", subtitle="Inferred data types, missing value ratios, and cardinality.")
        if profile.get("column_details"):
            col_df = pd.DataFrame(profile["column_details"])
            col_df["sample"] = col_df["sample"].apply(lambda x: ", ".join([str(i) for i in x]) if isinstance(x, list) else str(x))
            if not hasattr(st, "column_config") or isinstance(getattr(st, "column_config", None), type):
                col_df["null_pct"] = col_df["null_pct"].apply(lambda v: f"{v:.2f}%")
            st.dataframe(
                col_df,
                column_config={
                    "name": "Column Name",
                    "type": "Inferred Category",
                    "dtype": "Data Type",
                    "null_count": "Null Count",
                    "null_pct": st.column_config.NumberColumn("Missing %", format="%.2f%%"),
                    "unique_count": "Unique Values",
                    "sample": "Sample Values",
                },
                use_container_width=True,
                hide_index=True,
            )

        render_section_header("Summary Statistics", subtitle="Parametric summary measures for numeric variables.")
        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            st.dataframe(numeric_df.describe().round(2).T, use_container_width=True)
        else:
            st.info("No numeric columns detected for statistical summary.")

    with tab3:
        render_section_header("Attribute Distributions", subtitle="Univariate histogram, spread, and discrete category frequencies.")
        selected_col = st.selectbox("Select Attribute to Inspect", options=list(df.columns), key="explorer_dist_col")

        if selected_col:
            if np.issubdtype(df[selected_col].dtype, np.number):
                fig = px.histogram(
                    df,
                    x=selected_col,
                    nbins=30,
                    marginal="box",
                    title=f"Distribution & Spread: {selected_col}",
                    color_discrete_sequence=[tokens["brand_primary"]],
                )
                fig = apply_theme(fig, height=380)
                st.plotly_chart(fig, use_container_width=True)
            else:
                top_cats = df[selected_col].value_counts().head(15).reset_index()
                top_cats.columns = [selected_col, "Count"]
                fig = px.bar(
                    top_cats,
                    x=selected_col,
                    y="Count",
                    title=f"Frequency Count: {selected_col} (Top 15)",
                    color="Count",
                    color_continuous_scale=[tokens["brand_light"], tokens["brand_primary"]],
                )
                fig = apply_theme(fig, height=380)
                fig.update_layout(coloraxis_showscale=False, xaxis_tickangle=-30)
                st.plotly_chart(fig, use_container_width=True)

    with tab4:
        render_section_header("Feature Correlation Heatmap", subtitle="Pairwise Pearson correlation coefficients between numeric variables.")
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(num_cols) >= 2:
            corr = df[num_cols].corr().round(2)
            fig_corr = px.imshow(
                corr,
                text_auto=True,
                color_continuous_scale="RdBu_r",
                zmin=-1,
                zmax=1,
                title="Numeric Feature Correlation Matrix",
            )
            fig_corr = apply_theme(fig_corr, height=460)
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("At least 2 numeric columns are required to construct a correlation matrix.")


def _render_stat_pill(label: str, value: str, accent_color: str):
    """Render a clean metric stat card."""
    tokens = get_theme_tokens()
    st.markdown(
        f"""
        <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 10px; padding: 1rem; box-shadow: {tokens['card_shadow']};">
            <div style="font-size: 0.75rem; font-weight: 600; color: {tokens['text_muted']}; text-transform: uppercase; letter-spacing: 0.04em;">{label}</div>
            <div style="font-size: 1.35rem; font-weight: 700; color: {tokens['text_primary']}; margin-top: 4px; font-variant-numeric: tabular-nums;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
