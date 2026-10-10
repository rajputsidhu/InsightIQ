"""
Plotly Visualizations Component for InsightIQ.
Provides standardized, interactive, enterprise charts matching the design system
with automatic dynamic adaptation to Light and Dark themes.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from components.design_system import get_theme_tokens


def apply_theme(fig: go.Figure, height: int = 380) -> go.Figure:
    """Apply consistent enterprise SaaS layout parameters to Plotly figures according to active theme."""
    tokens = get_theme_tokens()
    is_dark = (tokens["name"] == "dark")

    fig.update_layout(
        height=height,
        margin=dict(l=16, r=16, t=44, b=16),
        paper_bgcolor=tokens["surface"],
        plot_bgcolor=tokens["surface"],
        font=dict(family="Inter, -apple-system, sans-serif", size=12, color=tokens["text_primary"]),
        title=dict(
            font=dict(size=14, color=tokens["text_primary"]),
            x=0.01,
            xanchor="left",
            y=0.96,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color=tokens["text_secondary"]),
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor=tokens["chart_grid"],
            gridwidth=1,
            zeroline=False,
            showline=True,
            linecolor=tokens["chart_border"],
            tickfont=dict(size=11, color=tokens["text_secondary"]),
            title_font=dict(size=12, color=tokens["text_secondary"]),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=tokens["chart_grid"],
            gridwidth=1,
            zeroline=False,
            showline=True,
            linecolor=tokens["chart_border"],
            tickfont=dict(size=11, color=tokens["text_secondary"]),
            title_font=dict(size=12, color=tokens["text_secondary"]),
        ),
        hoverlabel=dict(
            bgcolor=tokens["surface_subtle"] if is_dark else tokens["text_primary"],
            font_size=12,
            font_family="Inter, sans-serif",
            font_color="#FFFFFF" if not is_dark else tokens["text_primary"],
            bordercolor=tokens["border"],
        ),
    )
    return fig


def plot_revenue_profit_trend(ts_df: pd.DataFrame) -> go.Figure:
    """Interactive line chart of revenue and profit over time."""
    tokens = get_theme_tokens()
    fig = go.Figure()

    if "Revenue" in ts_df.columns:
        fig.add_trace(go.Scatter(
            x=ts_df["Date_Str"],
            y=ts_df["Revenue"],
            name="Net Revenue",
            mode="lines+markers",
            line=dict(color=tokens["brand_primary"], width=2.8),
            marker=dict(size=5),
            hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>",
        ))

    if "Profit" in ts_df.columns:
        fig.add_trace(go.Scatter(
            x=ts_df["Date_Str"],
            y=ts_df["Profit"],
            name="Operating Profit",
            mode="lines+markers",
            line=dict(color=tokens["teal"], width=2.2, dash="dot"),
            marker=dict(size=5),
            hovertemplate="<b>%{x}</b><br>Profit: $%{y:,.2f}<extra></extra>",
        ))

    fig.update_layout(title="Revenue & Profit Trajectory Over Time")
    return apply_theme(fig)


def plot_category_breakdown(cat_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of revenue by category."""
    tokens = get_theme_tokens()
    fig = px.bar(
        cat_df,
        x="Revenue",
        y="Category",
        orientation="h",
        color="Revenue",
        color_continuous_scale=[tokens["brand_light"], tokens["brand_primary"]],
        title="Revenue Breakdown by Product Category",
    )
    fig.update_layout(coloraxis_showscale=False, yaxis={'categoryorder': 'total ascending'})
    fig.update_traces(hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.2f}<extra></extra>")
    return apply_theme(fig)


def plot_top_products(prod_df: pd.DataFrame) -> go.Figure:
    """Bar chart for top products with profit margin indicators."""
    tokens = get_theme_tokens()
    fig = px.bar(
        prod_df,
        x="Product",
        y="Revenue",
        color="Profit" if "Profit" in prod_df.columns else None,
        color_continuous_scale=[tokens["teal_bg"], tokens["teal"]],
        title="Top Performing Products by Revenue",
    )
    fig.update_layout(coloraxis_showscale=False, xaxis_tickangle=-25)
    fig.update_traces(hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>")
    return apply_theme(fig)


def plot_rfm_scatter(rfm_df: pd.DataFrame) -> go.Figure:
    """Scatter plot of Customer Recency vs Monetary spend with Segment color coding."""
    tokens = get_theme_tokens()
    fig = px.scatter(
        rfm_df,
        x="recency",
        y="monetary",
        color="rfm_segment" if "rfm_segment" in rfm_df.columns else None,
        size="frequency",
        hover_data=["customer_id", "avg_order_value"],
        title="Customer Recency vs. Monetary Spend (RFM Mapping)",
        labels={"recency": "Days Since Last Purchase", "monetary": "Total Spend ($)"},
        color_discrete_sequence=tokens["chart_colors"],
    )
    fig.update_traces(marker=dict(opacity=0.85, line=dict(width=0.5, color=tokens["border"])))
    return apply_theme(fig)


def plot_cluster_profiles(profiles_df: pd.DataFrame) -> go.Figure:
    """Grouped bar chart for K-Means cluster characteristics."""
    tokens = get_theme_tokens()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=profiles_df["cluster"],
        y=profiles_df["avg_monetary"],
        name="Avg Spend ($)",
        marker_color=tokens["brand_primary"],
    ))
    fig.add_trace(go.Bar(
        x=profiles_df["cluster"],
        y=profiles_df["avg_recency"],
        name="Avg Recency (Days)",
        marker_color=tokens["warning"],
    ))
    fig.update_layout(title="K-Means Cluster Behavioral Profile Comparison", barmode="group")
    return apply_theme(fig)


def plot_roc_curves(eval_results: Dict[str, Dict[str, Any]]) -> go.Figure:
    """ROC curves comparison across all trained models."""
    tokens = get_theme_tokens()
    fig = go.Figure()

    colors_list = tokens["chart_colors"]
    i = 0
    for name, res in eval_results.items():
        if "fpr" in res and "tpr" in res:
            color = colors_list[i % len(colors_list)]
            fig.add_trace(go.Scatter(
                x=res["fpr"],
                y=res["tpr"],
                mode="lines",
                name=f"{name} (AUC: {res.get('roc_auc', 0):.2f})",
                line=dict(color=color, width=2.5),
            ))
            i += 1

    # Diagonal reference line
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1],
        mode="lines",
        name="Random Baseline (0.50)",
        line=dict(color=tokens["text_muted"], dash="dash", width=1.5),
    ))

    fig.update_layout(
        title="ROC Curves (Receiver Operating Characteristic)",
        xaxis_title="False Positive Rate",
        yaxis_title="True Positive Rate (Recall)",
    )
    return apply_theme(fig)


def plot_pr_curves(eval_results: Dict[str, Dict[str, Any]]) -> go.Figure:
    """Precision-Recall curves for imbalanced churn classification."""
    tokens = get_theme_tokens()
    fig = go.Figure()

    colors_list = tokens["chart_colors"]
    i = 0
    for name, res in eval_results.items():
        if "precision_curve" in res and "recall_curve" in res:
            color = colors_list[i % len(colors_list)]
            fig.add_trace(go.Scatter(
                x=res["recall_curve"],
                y=res["precision_curve"],
                mode="lines",
                name=f"{name} (PR-AUC: {res.get('pr_auc', 0):.2f})",
                line=dict(color=color, width=2.5),
            ))
            i += 1

    fig.update_layout(
        title="Precision-Recall Curves (Holdout Validation)",
        xaxis_title="Recall (Coverage)",
        yaxis_title="Precision (Exactness)",
    )
    return apply_theme(fig)


def plot_confusion_matrix_heatmap(cm: List[List[int]], labels: List[str] = ["Retained (0)", "Churned (1)"]) -> go.Figure:
    """Confusion matrix heatmap."""
    tokens = get_theme_tokens()
    cm_arr = np.array(cm)
    total = np.sum(cm_arr)
    annotations = []

    for i in range(len(labels)):
        for j in range(len(labels)):
            val = cm_arr[i, j]
            pct = (val / total * 100) if total > 0 else 0
            annotations.append(dict(
                x=labels[j],
                y=labels[i],
                text=f"<b>{val:,}</b><br>({pct:.1f}%)",
                showarrow=False,
                font=dict(color="#FFFFFF" if val > np.mean(cm_arr) else tokens["text_primary"], size=12),
            ))

    fig = go.Figure(data=go.Heatmap(
        z=cm_arr,
        x=labels,
        y=labels,
        colorscale=[[0, tokens["brand_light"]], [1, tokens["brand_primary"]]],
        showscale=False,
    ))

    fig.update_layout(
        title="Confusion Matrix (Holdout Test Set)",
        xaxis_title="Predicted Class",
        yaxis_title="Actual Class",
        annotations=annotations,
        yaxis=dict(autorange="reversed"),
    )
    return apply_theme(fig, height=320)


def plot_feature_importance_bar(imp_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart for top predictive features."""
    tokens = get_theme_tokens()
    fig = px.bar(
        imp_df,
        x="importance" if "importance" in imp_df.columns else "Importance",
        y="feature" if "feature" in imp_df.columns else "Feature",
        orientation="h",
        color="importance" if "importance" in imp_df.columns else "Importance",
        color_continuous_scale=[tokens["teal_bg"], tokens["teal"]],
        title="Feature Importance & Attribution (Top Drivers)",
    )
    fig.update_layout(coloraxis_showscale=False, yaxis={'categoryorder': 'total ascending'})
    fig.update_traces(hovertemplate="<b>%{y}</b><br>Importance: %{x:.4f}<extra></extra>")
    return apply_theme(fig)


def plot_time_series_forecast(historical_df: pd.DataFrame, forecast_df: pd.DataFrame, metric_name: str = "Revenue") -> go.Figure:
    """Time-series forecast plot with 80% and 95% confidence intervals."""
    tokens = get_theme_tokens()
    fig = go.Figure()

    # Historical
    fig.add_trace(go.Scatter(
        x=historical_df["Date"],
        y=historical_df["Actual"],
        name=f"Historical {metric_name}",
        mode="lines+markers",
        line=dict(color=tokens["brand_primary"], width=2.5),
        marker=dict(size=5),
        hovertemplate="<b>%{x}</b><br>Actual: $%{y:,.2f}<extra></extra>",
    ))

    # 95% Confidence Band
    fig.add_trace(go.Scatter(
        x=list(forecast_df["Date"]) + list(forecast_df["Date"])[::-1],
        y=list(forecast_df["Upper_95"]) + list(forecast_df["Lower_95"])[::-1],
        fill="toself",
        fillcolor="rgba(13, 148, 136, 0.12)",
        line=dict(color="rgba(255,255,255,0)"),
        hoverinfo="skip",
        showlegend=True,
        name="95% Confidence Interval",
    ))

    # 80% Confidence Band
    fig.add_trace(go.Scatter(
        x=list(forecast_df["Date"]) + list(forecast_df["Date"])[::-1],
        y=list(forecast_df["Upper_80"]) + list(forecast_df["Lower_80"])[::-1],
        fill="toself",
        fillcolor="rgba(13, 148, 136, 0.22)",
        line=dict(color="rgba(255,255,255,0)"),
        hoverinfo="skip",
        showlegend=True,
        name="80% Confidence Interval",
    ))

    # Point Forecast
    fig.add_trace(go.Scatter(
        x=forecast_df["Date"],
        y=forecast_df["Forecast"],
        name="Projected Forecast",
        mode="lines+markers",
        line=dict(color=tokens["teal"], width=2.8, dash="dash"),
        marker=dict(size=6, symbol="diamond"),
        hovertemplate="<b>%{x}</b><br>Projected: $%{y:,.2f}<extra></extra>",
    ))

    fig.update_layout(
        title=f"Statistical {metric_name} Forecast with Prediction Intervals",
        xaxis_title="Timeline Period",
        yaxis_title=f"{metric_name} ($)",
    )
    return apply_theme(fig, height=400)
