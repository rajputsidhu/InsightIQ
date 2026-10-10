"""
Unit tests for Business Metrics Engine.
"""

import pandas as pd
import numpy as np
import pytest
from services.business_metrics import (
    infer_business_columns,
    calculate_executive_kpis,
    compute_category_breakdown,
    compute_top_products,
)


def test_infer_business_columns():
    df = pd.DataFrame({
        "Order_Date": ["2023-01-01"],
        "Customer_ID": ["C1"],
        "Net_Revenue": [150.0],
        "Profit": [35.0],
        "Category": ["Electronics"],
        "Product_Name": ["Headphones"],
    })
    col_map = infer_business_columns(df)
    assert col_map["date"] == "Order_Date"
    assert col_map["customer_id"] == "Customer_ID"
    assert col_map["revenue"] == "Net_Revenue"
    assert col_map["profit"] == "Profit"
    assert col_map["category"] == "Category"
    assert col_map["product"] == "Product_Name"


def test_calculate_executive_kpis():
    df = pd.DataFrame({
        "order_id": ["O1", "O2", "O3", "O4"],
        "customer_id": ["C1", "C1", "C2", "C3"],
        "net_revenue": [100.0, 200.0, 150.0, 50.0],
        "profit": [20.0, 50.0, 30.0, 10.0],
    })
    kpis = calculate_executive_kpis(df)
    assert kpis["total_revenue"] == 500.0
    assert kpis["total_profit"] == 110.0
    assert kpis["total_orders"] == 4
    assert kpis["unique_customers"] == 3
    assert kpis["average_order_value"] == 125.0
    assert kpis["profit_margin_pct"] == 22.0
    assert kpis["repeat_customer_pct"] == round((1 / 3) * 100, 1)


def test_empty_kpi_handling():
    kpis = calculate_executive_kpis(pd.DataFrame())
    assert kpis["available"] is False
