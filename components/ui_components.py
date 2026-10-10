"""
Reusable UI Components for InsightIQ Design System.
Provides page titles, section headings, empty states, status badges, and cards.
"""

import streamlit as st
from typing import Optional, Callable
from components.design_system import get_theme_tokens


def render_page_title(title: str, subtitle: Optional[str] = None):
    """Render a clean, modern SaaS page title and subtitle."""
    tokens = get_theme_tokens()
    subtitle_html = (
        f'<p style="margin: 4px 0 0 0; color: {tokens["text_secondary"]}; font-size: 0.925rem; font-weight: 400; line-height: 1.5;">{subtitle}</p>'
        if subtitle
        else ""
    )
    title_html = (
        f'<div style="margin-bottom: 1.5rem;">'
        f'<h1 style="margin: 0; color: {tokens["text_primary"]}; font-size: 1.75rem; font-weight: 700; letter-spacing: -0.025em; line-height: 1.25;">{title}</h1>'
        f'{subtitle_html}'
        f'</div>'
    )
    st.markdown(title_html, unsafe_allow_html=True)



def render_section_header(title: str, subtitle: Optional[str] = None, badge: Optional[str] = None):
    """Render a consistent section header with optional badge and subtitle."""
    tokens = get_theme_tokens()
    badge_html = (
        f'<span style="background: {tokens["brand_light"]}; color: {tokens["brand_primary"]}; font-size: 0.725rem; font-weight: 600; padding: 2px 8px; border-radius: 9999px; border: 1px solid {tokens["border"]};">{badge}</span>'
        if badge
        else ""
    )
    subtitle_html = (
        f'<div style="font-size: 0.825rem; color: {tokens["text_muted"]}; margin-top: 2px;">{subtitle}</div>'
        if subtitle
        else ""
    )
    header_html = (
        f'<div style="margin: 1.5rem 0 0.85rem 0; padding-bottom: 0.45rem; border-bottom: 1px solid {tokens["border"]};">'
        f'<div style="display: flex; align-items: center; gap: 0.5rem;">'
        f'<h3 style="margin: 0; color: {tokens["text_primary"]}; font-size: 1.15rem; font-weight: 600; letter-spacing: -0.015em;">{title}</h3>'
        f'{badge_html}'
        f'</div>'
        f'{subtitle_html}'
        f'</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)



def render_empty_state(
    title: str,
    description: str,
    icon: str = "📊",
    button_label: Optional[str] = None,
    button_key: Optional[str] = None,
    on_click: Optional[Callable] = None,
):
    """Render a clean, professional empty state container."""
    tokens = get_theme_tokens()
    st.markdown(
        f"""
        <div style="background: {tokens['surface']}; border: 1px dashed {tokens['border']}; border-radius: 12px; padding: 3rem 2rem; text-align: center; margin: 1.5rem 0;">
            <div style="font-size: 2.25rem; margin-bottom: 0.75rem;">{icon}</div>
            <h4 style="margin: 0 0 0.5rem 0; color: {tokens['text_primary']}; font-size: 1.1rem; font-weight: 600;">{title}</h4>
            <p style="margin: 0 auto; max-width: 460px; color: {tokens['text_secondary']}; font-size: 0.875rem; line-height: 1.5;">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if button_label:
        col_s1, col_btn, col_s2 = st.columns([2, 1.5, 2])
        with col_btn:
            if st.button(button_label, key=button_key or f"btn_{title[:10]}", use_container_width=True):
                if on_click:
                    on_click()


def get_status_badge(text: str, status_type: str = "info") -> str:
    """Return an HTML snippet for a status pill."""
    tokens = get_theme_tokens()
    bg_map = {
        "success": (tokens["success_bg"], tokens["success"]),
        "warning": (tokens["warning_bg"], tokens["warning"]),
        "danger": (tokens["danger_bg"], tokens["danger"]),
        "info": (tokens["brand_light"], tokens["brand_primary"]),
        "neutral": (tokens["surface_subtle"], tokens["text_secondary"]),
    }
    bg, fg = bg_map.get(status_type, (tokens["surface_subtle"], tokens["text_secondary"]))
    return f'<span style="background: {bg}; color: {fg}; font-size: 0.75rem; font-weight: 600; padding: 2px 10px; border-radius: 9999px; border: 1px solid {fg}26;">{text}</span>'
