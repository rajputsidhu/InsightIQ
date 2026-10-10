"""
Unit tests for Customer Analytics and RFM Segmentation.
"""

import pandas as pd
import numpy as np
import pytest
from services.customer_analysis import compute_rfm_metrics, run_kmeans_clustering


def test_rfm_computation():
    df = pd.DataFrame({
        "cust_id": ["C1", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10"],
        "date": ["2024-01-01", "2024-01-10", "2024-01-05", "2024-01-08", "2024-01-02", "2024-01-04", "2024-01-09", "2024-01-07", "2024-01-03", "2024-01-06", "2024-01-08"],
        "revenue": [50.0, 150.0, 200.0, 30.0, 80.0, 90.0, 120.0, 45.0, 60.0, 110.0, 300.0],
        "order_id": ["O1", "O2", "O3", "O4", "O5", "O6", "O7", "O8", "O9", "O10", "O11"],
    })
    rfm = compute_rfm_metrics(df, customer_col="cust_id", date_col="date", revenue_col="revenue", order_col="order_id")
    assert len(rfm) == 10
    assert "recency" in rfm.columns
    assert "frequency" in rfm.columns
    assert "monetary" in rfm.columns
    assert "rfm_segment" in rfm.columns
    assert "estimated_clv_2yr" in rfm.columns

    # C1 placed 2 orders totaling $200
    c1_row = rfm[rfm["cust_id"] == "C1"].iloc[0]
    assert c1_row["frequency"] == 2
    assert c1_row["monetary"] == 200.0


def test_kmeans_clustering():
    df = pd.DataFrame({
        "cust_id": [f"C{i}" for i in range(25)],
        "date": ["2024-01-01"] * 25,
        "revenue": [float(i * 10 + 5) for i in range(25)],
        "order_id": [f"O{i}" for i in range(25)],
    })
    rfm = compute_rfm_metrics(df, "cust_id", "date", "revenue", "order_id")
    clustered, meta = run_kmeans_clustering(rfm, n_clusters=3)
    assert "cluster" in clustered.columns
    assert meta["n_clusters"] == 3
    assert len(meta["profiles"]) == 3
