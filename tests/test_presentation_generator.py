"""
Unit tests for Executive Presentation Generator (Workstream 4).
"""

import pytest
from services.presentation_generator import PresentationGenerator


def test_generate_powerpoint_deck():
    sample_kpis = {
        "total_revenue": 245000.50,
        "total_orders": 1250,
        "average_order_value": 196.00,
        "total_profit": 61250.10,
        "profit_margin_pct": 25.0,
        "unique_customers": 450,
        "repeat_customer_pct": 38.5,
        "revenue_growth_pct": 14.2,
    }

    sample_insights = [
        {
            "title": "Strong Revenue Expansion",
            "category": "Revenue & Growth",
            "finding": "Net revenue expanded by +14.2%.",
            "supporting_metric": "+14.2% Growth",
            "recommended_actions": ["Scale marketing investment in top performing channels."],
        },
        {
            "title": "Category Dominance in Technology",
            "category": "Product Strategy",
            "finding": "Technology generated 48% of total revenue.",
            "supporting_metric": "48% Share",
            "recommended_actions": ["Create bundle discounts with accessories."],
        }
    ]

    deck_bytes = PresentationGenerator.generate_deck(
        kpis=sample_kpis,
        insights=sample_insights,
        dataset_name="Test Enterprise E-Commerce"
    )

    assert isinstance(deck_bytes, bytes)
    assert len(deck_bytes) > 5000  # Valid PPTX binary has substantial zip size
    # Check magic zip header bytes 'PK' (0x50, 0x4B)
    assert deck_bytes[:2] == b"PK"
