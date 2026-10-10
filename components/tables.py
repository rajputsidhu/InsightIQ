"""
Data Table Components for InsightIQ.
Provides formatted, paginated tables with search, styled status tags, risk badges,
and cross-version compatibility for Streamlit (including versions < 1.23.0).
"""

import inspect
import streamlit as st
import pandas as pd
from typing import Optional, List, Dict, Any


# ---------------------------------------------------------------------------
# Cross-version Streamlit compatibility shim
# Streamlit < 1.23.0 does not have st.column_config and does not support
# column_config or hide_index in st.dataframe().
# ---------------------------------------------------------------------------

class _ColumnConfigShim:
    """Safe fallback shim when running on Streamlit < 1.23.0."""
    class Column:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
    NumberColumn = Column
    TextColumn = Column
    ProgressColumn = Column
    CheckboxColumn = Column
    SelectboxColumn = Column
    DateColumn = Column
    DatetimeColumn = Column
    TimeColumn = Column
    ListColumn = Column
    LinkColumn = Column
    BarChartColumn = Column
    LineChartColumn = Column
    ImageColumn = Column


# Attach fallback shim to streamlit module if missing
if not hasattr(st, "column_config"):
    st.column_config = _ColumnConfigShim()


# Wrap st.dataframe safely to prevent unexpected argument errors on older Streamlit
_original_st_dataframe = getattr(st, "_insightiq_orig_dataframe", st.dataframe)
st._insightiq_orig_dataframe = _original_st_dataframe

def _safe_st_dataframe(data, *args, **kwargs):
    sig = inspect.signature(_original_st_dataframe)
    supported_kwargs = {}
    for k, v in kwargs.items():
        if k in sig.parameters:
            supported_kwargs[k] = v
    return _original_st_dataframe(data, *args, **supported_kwargs)

st.dataframe = _safe_st_dataframe


def render_paginated_table(
    df: pd.DataFrame,
    page_size: int = 15,
    key_prefix: str = "table",
    title: Optional[str] = None
):
    """Render a DataFrame with search, pagination controls, and styled columns."""
    if df is None or df.empty:
        st.info("No records available to display.")
        return

    working_df = df.copy()

    # Search bar & Controls
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([3, 1, 1])
    with ctrl_col1:
        search_query = st.text_input(
            "Search Table",
            placeholder="🔍 Type keyword to search records...",
            key=f"{key_prefix}_search",
            label_visibility="collapsed"
        )
    with ctrl_col2:
        page_size = st.selectbox(
            "Rows per page",
            options=[10, 15, 25, 50, 100],
            index=1,
            key=f"{key_prefix}_size",
            label_visibility="collapsed"
        )
    with ctrl_col3:
        pass

    # Apply search filter if entered
    if search_query:
        mask = working_df.astype(str).apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)
        working_df = working_df[mask]

    total_rows = len(working_df)
    total_pages = max(1, (total_rows + page_size - 1) // page_size)

    page_col1, page_col2 = st.columns([2, 2])
    with page_col1:
        if title:
            st.markdown(f"**{title}** • Showing {len(working_df):,} of {len(df):,} records")
        else:
            st.caption(f"Showing {len(working_df):,} of {len(df):,} records")

    with page_col2:
        current_page = st.number_input(
            "Page",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
            key=f"{key_prefix}_page_num",
            label_visibility="collapsed"
        )

    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)
    page_df = working_df.iloc[start_idx:end_idx].copy()

    # Build dynamic column config based on column types
    column_config = {}
    for col in page_df.columns:
        c_low = col.lower()
        if "revenue" in c_low or "spend" in c_low or "profit" in c_low or "charges" in c_low or "cost" in c_low or "price" in c_low or "clv" in c_low:
            column_config[col] = st.column_config.NumberColumn(col.replace("_", " ").title(), format="$%.2f")
        elif "pct" in c_low or "rate" in c_low or "growth" in c_low or "margin" in c_low:
            column_config[col] = st.column_config.NumberColumn(col.replace("_", " ").title(), format="%.1f%%")
        elif "prob" in c_low:
            column_config[col] = st.column_config.ProgressColumn(col.replace("_", " ").title(), format="%.2f", min_value=0.0, max_value=1.0)
        else:
            column_config[col] = st.column_config.TextColumn(col.replace("_", " ").title())

    st.dataframe(page_df, column_config=column_config, use_container_width=True, hide_index=True)


def render_risk_table(risk_df: pd.DataFrame, page_size: int = 15, key_prefix: str = "risk"):
    """Render customer churn risk scoring table with styled risk tiers and progress bars."""
    if risk_df is None or risk_df.empty:
        st.info("No churn risk scoring records available.")
        return

    working_df = risk_df.copy()

    # Search & Tier Filters
    f_col1, f_col2, f_col3 = st.columns([2, 2, 1])
    with f_col1:
        tier_filter = st.multiselect(
            "Filter by Risk Tier",
            options=["High Risk", "Medium Risk", "Low Risk"],
            default=["High Risk", "Medium Risk", "Low Risk"],
            key=f"{key_prefix}_tier_filter",
        )
    with f_col2:
        search_cust = st.text_input(
            "Search Customer ID",
            placeholder="🔍 Search by Customer ID...",
            key=f"{key_prefix}_cust_search",
        )
    with f_col3:
        page_size_choice = st.selectbox(
            "Rows / Page",
            options=[10, 15, 25, 50],
            index=1,
            key=f"{key_prefix}_page_size",
        )

    # Apply filters
    if tier_filter:
        working_df = working_df[working_df["Risk_Tier"].isin(tier_filter)]
    if search_cust:
        working_df = working_df[working_df["Customer_ID"].astype(str).str.contains(search_cust, case=False)]

    total_rows = len(working_df)
    total_pages = max(1, (total_rows + page_size_choice - 1) // page_size_choice)

    p_info_col, p_nav_col = st.columns([3, 1])
    with p_info_col:
        st.caption(f"Displaying **{len(working_df):,}** of **{len(risk_df):,}** scored customer accounts (Page {1} of {total_pages})")
    with p_nav_col:
        page_num = st.number_input(
            "Page Number",
            min_value=1,
            max_value=total_pages,
            value=1,
            key=f"{key_prefix}_p_num",
            label_visibility="collapsed"
        )

    start_idx = (page_num - 1) * page_size_choice
    end_idx = min(start_idx + page_size_choice, total_rows)
    page_df = working_df.iloc[start_idx:end_idx].copy()

    # Configure Column Visuals
    column_config = {
        "Customer_ID": st.column_config.TextColumn("Customer ID", width="medium"),
        "Churn_Probability": st.column_config.ProgressColumn(
            "Churn Risk Probability",
            help="Predicted likelihood of account churn (0.00 = Safe, 1.00 = Definite Churn)",
            format="%.2f",
            min_value=0.0,
            max_value=1.0,
            width="large",
        ),
        "Churn_Risk_Pct": st.column_config.NumberColumn(
            "Risk %",
            help="Calculated churn percentage",
            format="%.1f%%",
            width="small",
        ),
        "Risk_Tier": st.column_config.TextColumn(
            "Risk Category",
            help="Tier based on probability threshold (High >= 65%, Medium 35-65%, Low < 35%)",
            width="medium",
        ),
    }

    # Add numeric formatters for charges/revenue if in columns
    for col in page_df.columns:
        c_low = col.lower()
        if col not in column_config:
            if "charges" in c_low or "spend" in c_low or "revenue" in c_low or "amount" in c_low:
                column_config[col] = st.column_config.NumberColumn(col.replace("_", " ").title(), format="$%.2f")
            elif "tenure" in c_low:
                column_config[col] = st.column_config.NumberColumn("Tenure (Months)", format="%d mo")
            else:
                column_config[col] = st.column_config.TextColumn(col.replace("_", " ").title())

    st.dataframe(
        page_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
    )
