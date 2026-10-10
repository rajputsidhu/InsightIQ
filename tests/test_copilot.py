"""
Unit tests for Analytics Copilot Service (Workstream 2).
"""

import pytest
import pandas as pd
import numpy as np
from services.copilot import AnalyticsCopilotService


@pytest.fixture
def sample_sales_df():
    return pd.DataFrame({
        "Order_ID": [101, 102, 103, 104, 105],
        "Category": ["Electronics", "Electronics", "Furniture", "Furniture", "Office"],
        "Revenue": [500.0, 750.0, 200.0, 450.0, 120.0],
        "Profit": [120.0, 180.0, 40.0, 90.0, 30.0],
        "Order_Date": ["2024-01-15", "2024-01-20", "2024-02-10", "2024-02-15", "2024-03-01"],
    })


def test_copilot_schema_summary(sample_sales_df):
    copilot = AnalyticsCopilotService()
    schema = copilot.get_schema_summary(sample_sales_df)
    assert schema["row_count"] == 5
    assert "Revenue" in schema["columns"]
    assert "Category" in schema["columns"]


def test_copilot_ask_category_question(sample_sales_df):
    copilot = AnalyticsCopilotService()
    res = copilot.ask("Which category has highest revenue?", sample_sales_df)

    assert res["success"] is True
    assert "result_df" in res
    assert not res["result_df"].empty
    assert "response_text" in res
    assert res["execution_time_ms"] >= 0


def test_copilot_empty_dataset():
    copilot = AnalyticsCopilotService()
    res = copilot.ask("Top products", pd.DataFrame())
    assert res["success"] is False
    assert "No active dataset" in res["error"]
