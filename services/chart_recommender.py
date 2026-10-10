"""
Automatic Chart Recommender for InsightIQ Conversational Copilot.
Inspects tabular query results and constructs optimal, clear Plotly visualizations.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Dict, Any, Tuple


def recommend_and_build_chart(
    df: pd.DataFrame,
    title: Optional[str] = None
) -> Tuple[Optional[go.Figure], str]:
    """
    Analyzes DataFrame structure and returns (Plotly Figure, chart_type_label).
    """
    if df is None or df.empty or len(df.columns) < 1:
        return None, "Empty Data"

    cols = list(df.columns)
    n_rows, n_cols = df.shape

    # Identify column data types
    date_cols = []
    num_cols = []
    cat_cols = []

    for col in cols:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
        elif pd.api.types.is_numeric_dtype(df[col]):
            num_cols.append(col)
        else:
            # Check if strings are parsable dates
            sample_val = str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else ""
            if any(term in col.lower() for term in ["date", "month", "period", "year"]) and len(sample_val) >= 4:
                date_cols.append(col)
            else:
                cat_cols.append(col)

    chart_title = title or "Query Result Visualization"

    # Pattern 1: Time Series (Date + Numeric)
    if date_cols and num_cols:
        d_col = date_cols[0]
        y_col = num_cols[0]
        sorted_df = df.sort_values(d_col)
        fig = px.line(
            sorted_df,
            x=d_col,
            y=num_cols[:3],
            title=chart_title,
            markers=True,
            template="plotly_white",
            color_discrete_sequence=["#2563EB", "#059669", "#D97706"]
        )
        fig.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20))
        return fig, "Time-Series Trend"

    # Pattern 2: Category Comparison (1 Categorical + 1 Numeric)
    if cat_cols and num_cols:
        c_col = cat_cols[0]
        y_col = num_cols[0]

        # If categories <= 5 and user asked for composition, pie is viable; otherwise clean sorted bar
        if len(df) <= 5 and "share" in y_col.lower():
            fig = px.pie(
                df,
                names=c_col,
                values=y_col,
                title=chart_title,
                hole=0.4,
                template="plotly_white",
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20))
            return fig, "Category Composition (Donut)"

        sorted_df = df.sort_values(y_col, ascending=False).head(15)
        fig = px.bar(
            sorted_df,
            x=c_col,
            y=y_col,
            title=chart_title,
            text_auto=".2s",
            template="plotly_white",
            color_discrete_sequence=["#1E3A8A"]
        )
        fig.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20))
        return fig, "Category Comparison (Bar)"

    # Pattern 3: Two Numerical Variables (Scatter / Correlation)
    if len(num_cols) >= 2:
        x_col = num_cols[0]
        y_col = num_cols[1]
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            title=chart_title,
            template="plotly_white",
            color_discrete_sequence=["#2563EB"]
        )
        fig.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20))
        return fig, "Bivariate Scatter"

    # Pattern 4: Single Numeric Column (Histogram distribution)
    if num_cols and not cat_cols:
        col = num_cols[0]
        fig = px.histogram(
            df,
            x=col,
            nbins=20,
            title=f"Distribution of {col}",
            template="plotly_white",
            color_discrete_sequence=["#059669"]
        )
        fig.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20))
        return fig, "Distribution Histogram"

    return None, "Table View"
