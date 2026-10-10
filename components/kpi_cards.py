"""
KPI Card Component for InsightIQ.
Renders minimalist, modern enterprise metric cards with semantic icons,
tabular numerals, delta indicators, and compact SVG trend sparklines.
"""

import streamlit as st
from typing import Optional, List
import numpy as np
from components.design_system import get_theme_tokens


def _generate_svg_sparkline(data: List[float], color: str = "#4F46E5") -> str:
    """Generate lightweight inline SVG sparkline polyline from historical numbers."""
    if not data or len(data) < 2:
        return ""

    arr = np.array(data, dtype=float)
    min_v, max_v = np.min(arr), np.max(arr)
    rng = max_v - min_v if max_v != min_v else 1.0

    width, height = 110, 28
    padding = 3

    points = []
    n = len(arr)
    for i, val in enumerate(arr):
        x = (i / (n - 1)) * width
        # Invert y because SVG y=0 is at the top
        y = height - padding - ((val - min_v) / rng) * (height - 2 * padding)
        points.append(f"{x:.1f},{y:.1f}")

    points_str = " ".join(points)
    return f"""
    <div style="margin-top: 8px; width: 100%; height: 28px;">
        <svg viewBox="0 0 {width} {height}" style="width: 100%; height: 100%; overflow: visible;">
            <polyline fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" points="{points_str}" />
        </svg>
    </div>
    """


def _get_semantic_icon(icon_type: str) -> str:
    """Return sleek inline SVG icon for metric card."""
    icons = {
        "revenue": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>""",
        "orders": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-2z"></path><line x1="3" y1="6" x2="21" y2="6"></line><path d="M16 10a4 4 0 0 1-8 0"></path></svg>""",
        "profit": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>""",
        "customers": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>""",
        "metric": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>"""
    }
    return icons.get(icon_type, icons["metric"])


def render_kpi_card(
    label: str,
    value: str,
    subtext: str = "",
    delta: Optional[str] = None,
    delta_positive: bool = True,
    accent: str = "blue",
    icon_type: Optional[str] = None,
    sparkline_data: Optional[List[float]] = None
):
    """Render an individual enterprise styled KPI metric card with optional sparkline and semantic icon."""
    tokens = get_theme_tokens()

    # Determine icon type from label if not provided
    if not icon_type:
        l_low = label.lower()
        if "rev" in l_low or "sales" in l_low:
            icon_type = "revenue"
        elif "order" in l_low or "trans" in l_low:
            icon_type = "orders"
        elif "profit" in l_low or "margin" in l_low:
            icon_type = "profit"
        elif "cust" in l_low or "reach" in l_low or "account" in l_low:
            icon_type = "customers"
        else:
            icon_type = "metric"

    icon_svg = _get_semantic_icon(icon_type)

    delta_html = ""
    if delta:
        delta_color = tokens["success"] if delta_positive else tokens["danger"]
        arrow = "▲" if delta_positive else "▼"
        delta_html = f'<span style="color: {delta_color}; font-weight: 600; margin-right: 4px;">{arrow} {delta}</span>'

    sub_combined = f"{delta_html} {subtext}".strip()
    sub_html = f'<div style="font-size: 0.8rem; color: {tokens["text_secondary"]}; margin-top: 4px;">{sub_combined}</div>' if sub_combined else ""

    spark_color = tokens["brand_primary"]
    sparkline_html = _generate_svg_sparkline(sparkline_data, color=spark_color) if sparkline_data else ""

    card_html = f"""
    <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 12px; padding: 1.2rem 1.35rem; box-shadow: {tokens['shadow_card']}; margin-bottom: 0.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 0.775rem; font-weight: 600; color: {tokens['text_secondary']}; text-transform: uppercase; letter-spacing: 0.04em;">{label}</span>
            <div style="width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; background: {tokens['surface_subtle']}; color: {tokens['brand_primary']};">
                {icon_svg}
            </div>
        </div>
        <div style="font-size: 1.95rem; font-weight: 700; color: {tokens['text_primary']}; letter-spacing: -0.03em; line-height: 1.1; font-variant-numeric: tabular-nums;">
            {value}
        </div>
        {sub_html}
        {sparkline_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
