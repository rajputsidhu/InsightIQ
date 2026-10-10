"""
Customer Analytics & RFM Segmentation Engine for InsightIQ.
Calculates RFM metrics, segment groupings, K-Means clustering, and estimated Customer Lifetime Value (CLV).
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


def compute_rfm_metrics(
    df: pd.DataFrame,
    customer_col: str,
    date_col: str,
    revenue_col: str,
    order_col: Optional[str] = None
) -> pd.DataFrame:
    """
    Compute customer-level Recency, Frequency, and Monetary metrics.
    """
    temp_df = df[[customer_col, date_col, revenue_col]].copy()
    if order_col and order_col in df.columns:
        temp_df["order_id"] = df[order_col]
    else:
        temp_df["order_id"] = np.arange(len(df))

    temp_df["order_date"] = pd.to_datetime(temp_df[date_col], errors="coerce")
    temp_df = temp_df.dropna(subset=[customer_col, "order_date", revenue_col])

    if temp_df.empty:
        return pd.DataFrame()

    ref_date = temp_df["order_date"].max() + pd.Timedelta(days=1)

    rfm = temp_df.groupby(customer_col).agg(
        recency=("order_date", lambda x: (ref_date - x.max()).days),
        frequency=("order_id", "nunique"),
        monetary=(revenue_col, "sum"),
        first_purchase=("order_date", "min"),
        last_purchase=("order_date", "max"),
    ).reset_index()

    rfm["monetary"] = rfm["monetary"].round(2)
    rfm["avg_order_value"] = (rfm["monetary"] / rfm["frequency"]).round(2)
    rfm["tenure_days"] = (rfm["last_purchase"] - rfm["first_purchase"]).dt.days

    # Calculate RFM Scores (1 to 5 quintiles)
    # Recency: lower is better (so reverse quantile score)
    try:
        rfm["r_score"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1], duplicates="drop").astype(int)
    except Exception:
        rfm["r_score"] = pd.cut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)

    try:
        rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    except Exception:
        rfm["f_score"] = 3

    try:
        rfm["m_score"] = pd.qcut(rfm["monetary"], 5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)
    except Exception:
        rfm["m_score"] = pd.cut(rfm["monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)

    rfm["rfm_score"] = rfm["r_score"].astype(str) + rfm["f_score"].astype(str) + rfm["m_score"].astype(str)

    # Assign Rule-Based Customer Segments
    def assign_segment(row):
        r, f, m = row["r_score"], row["f_score"], row["m_score"]
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        elif f >= 3 and m >= 3:
            return "Loyal Customers"
        elif r >= 4 and f <= 2:
            return "Promising & Recent"
        elif r >= 3 and f >= 2:
            return "Potential Loyalists"
        elif r == 3 and f <= 2:
            return "Needs Attention"
        elif r <= 2 and f >= 3:
            return "At Risk"
        elif r <= 2 and f <= 2 and m >= 3:
            return "About to Sleep (High Value)"
        elif r == 1 and f == 1:
            return "Lost / Hibernating"
        else:
            return "Standard Customers"

    rfm["rfm_segment"] = rfm.apply(assign_segment, axis=1)

    # Estimate Customer Lifetime Value (CLV proxy)
    # Annualized spend * estimated margin factor (assumed baseline 25% or empirical)
    avg_annual_freq = rfm["frequency"] * (365 / np.maximum(rfm["tenure_days"] + 30, 90))
    estimated_annual_spend = rfm["avg_order_value"] * avg_annual_freq
    # Projected 2-year value
    rfm["estimated_clv_2yr"] = (estimated_annual_spend * 2 * 0.28).round(2)

    return rfm


def run_kmeans_clustering(
    rfm_df: pd.DataFrame,
    n_clusters: int = 4
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Perform K-Means clustering on scaled Recency, Frequency, Monetary features.
    Returns clustered DataFrame and diagnostics metadata.
    """
    if rfm_df is None or len(rfm_df) < n_clusters * 3:
        return rfm_df, {"error": "Insufficient customer records for clustering (need at least 15 records)."}

    features = ["recency", "frequency", "monetary"]
    X = rfm_df[features].copy()

    # Log transform monetary & frequency to handle skewness
    X_log = X.copy()
    X_log["recency"] = np.log1p(X_log["recency"])
    X_log["frequency"] = np.log1p(X_log["frequency"])
    X_log["monetary"] = np.log1p(np.maximum(X_log["monetary"], 0))

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_log)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)

    clustered_df = rfm_df.copy()
    clustered_df["cluster"] = [f"Cluster {c+1}" for c in clusters]

    sil_score = None
    if len(rfm_df) >= 10:
        try:
            sil_score = round(float(silhouette_score(X_scaled, clusters)), 3)
        except Exception:
            pass

    # Profile clusters
    profiles = clustered_df.groupby("cluster").agg(
        customer_count=("cluster", "count"),
        avg_recency=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        total_revenue=("monetary", "sum"),
    ).round(2).reset_index()

    profiles["revenue_share_pct"] = (profiles["total_revenue"] / profiles["total_revenue"].sum() * 100).round(1)

    return clustered_df, {
        "n_clusters": n_clusters,
        "silhouette_score": sil_score,
        "profiles": profiles.to_dict(orient="records"),
        "cluster_profiles_df": profiles,
    }
