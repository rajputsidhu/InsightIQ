"""
Unit tests for Deterministic Business Insight Engine.
"""

import pandas as pd
import numpy as np
import pytest
from services.insight_engine import generate_business_insights, generate_llm_executive_summary


def test_generate_business_insights():
    df = pd.DataFrame({
        "order_id": [f"O{i}" for i in range(100)],
        "customer_id": [f"C{i%20}" for i in range(100)],
        "net_revenue": [100.0 if i < 90 else 5000.0 for i in range(100)],
        "profit": [20.0 if i < 90 else 1200.0 for i in range(100)],
        "category": ["Hardware" if i % 2 == 0 else "Software" for i in range(100)],
    })

    col_map = {
        "revenue": "net_revenue",
        "profit": "profit",
        "customer_id": "customer_id",
        "category": "category",
        "order_id": "order_id",
    }

    kpis = {
        "total_revenue": df["net_revenue"].sum(),
        "total_orders": 100,
        "profit_margin_pct": 24.5,
        "revenue_growth_pct": 14.2,
        "repeat_customer_pct": 95.0,
    }

    insights = generate_business_insights(df, col_map, kpis)
    assert len(insights) >= 2
    for ins in insights:
        assert "title" in ins
        assert "finding" in ins
        assert "supporting_metric" in ins
        assert "recommended_actions" in ins
        assert len(ins["recommended_actions"]) > 0


def test_executive_summary_synthesis():
    insights = [{
        "title": "Revenue Expansion",
        "finding": "Net revenue increased by 15%",
        "recommended_actions": ["Scale ad spend"],
    }]
    kpis = {"total_revenue": 150000.0, "profit_margin_pct": 28.0, "total_orders": 1200}
    summary = generate_llm_executive_summary(insights, kpis)
    assert "Executive Intelligence Briefing" in summary
    assert "150,000" in summary
