"""
InsightIQ Enterprise Design System & Semantic Token Architecture.
Provides unified color tokens, typography scales, spacing tokens,
theme management helpers, cross-version Streamlit compatibility,
and dynamic CSS injection for Light & Dark modes.
"""

import inspect
import streamlit as st
import pandas as pd
from typing import Dict, Any, List


# ---------------------------------------------------------------------------
# Cross-version Streamlit compatibility shim
# ---------------------------------------------------------------------------

class _ColumnConfigShim:
    """Safe fallback shim when running on Streamlit < 1.23.0."""
    class Column:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
    NumberColumn = Column
    TextColumn = Column
    ProgressColumn = Column
    CheckboxColumn = Column
    SelectboxColumn = Column
    DateColumn = Column
    DatetimeColumn = Column
    TimeColumn = Column
    ListColumn = Column
    LinkColumn = Column
    BarChartColumn = Column
    LineChartColumn = Column
    ImageColumn = Column


if not hasattr(st, "column_config"):
    st.column_config = _ColumnConfigShim()

if not hasattr(st, "rerun"):
    st.rerun = getattr(st, "experimental_rerun", lambda: None)


_original_st_dataframe = getattr(st, "_insightiq_orig_dataframe", st.dataframe)
st._insightiq_orig_dataframe = _original_st_dataframe

def _safe_st_dataframe(data, *args, **kwargs):
    sig = inspect.signature(_original_st_dataframe)
    supported_kwargs = {}
    for k, v in kwargs.items():
        if k in sig.parameters:
            supported_kwargs[k] = v
    return _original_st_dataframe(data, *args, **supported_kwargs)

st.dataframe = _safe_st_dataframe

_original_st_download_button = getattr(st, "_insightiq_orig_download_button", st.download_button)
st._insightiq_orig_download_button = _original_st_download_button

def _safe_st_download_button(label, data, *args, **kwargs):
    sig = inspect.signature(_original_st_download_button)
    supported_kwargs = {}
    for k, v in kwargs.items():
        if k in sig.parameters:
            supported_kwargs[k] = v
    return _original_st_download_button(label, data, *args, **supported_kwargs)

st.download_button = _safe_st_download_button



# Exact Semantic Tokens as specified in Design System
THEME_TOKENS: Dict[str, Dict[str, Any]] = {
    "light": {
        "name": "light",
        "bg_app": "#F5F7FC",
        "surface": "#FFFFFF",
        "surface_subtle": "#F1F4F9",
        "surface_elevated": "#FFFFFF",
        "text_primary": "#172033",
        "text_secondary": "#64748B",
        "text_muted": "#94A3B8",
        "border": "#E2E8F0",
        "border_subtle": "#F1F5F9",
        "brand_primary": "#4F46E5",
        "brand_hover": "#4338CA",
        "brand_light": "#EEF2FF",
        "primary_gradient": "linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)",
        "teal": "#14B8A6",
        "teal_bg": "#F0FDFA",
        "blue": "#3B82F6",
        "secondary_blue": "#3B82F6",
        "blue_secondary": "#3B82F6",
        "purple": "#8B5CF6",
        "purple_bg": "#F5F3FF",
        "amber": "#F59E0B",
        "warning": "#F59E0B",
        "warning_bg": "#FFFBEB",
        "success": "#10B981",
        "success_bg": "#ECFDF5",
        "danger": "#EF4444",
        "danger_bg": "#FEF2F2",
        "chart_colors": [
            "#4F46E5",  # Brand Indigo
            "#14B8A6",  # Teal
            "#3B82F6",  # Blue
            "#8B5CF6",  # Purple
            "#F59E0B",  # Amber
            "#EC4899",  # Pink
            "#10B981",  # Emerald Green
            "#64748B",  # Slate
        ],
        "chart_grid": "#F1F5F9",
        "chart_border": "#E2E8F0",
        "sidebar_bg": "#FFFFFF",
        "sidebar_text": "#172033",
        "sidebar_text_muted": "#64748B",
        "sidebar_active_bg": "#EEF2FF",
        "sidebar_active_text": "#3730A3",
        "sidebar_active_accent": "#4F46E5",
        "sidebar_hover_bg": "#F8FAFC",
        "sidebar_border": "#E2E8F0",
        "shadow_sm": "0 1px 2px 0 rgba(15, 23, 42, 0.05)",
        "shadow_card": "0 1px 3px 0 rgba(15, 23, 42, 0.06), 0 1px 2px -1px rgba(15, 23, 42, 0.04)",
        "card_shadow": "0 1px 3px 0 rgba(15, 23, 42, 0.06), 0 1px 2px -1px rgba(15, 23, 42, 0.04)",
        "shadow_hover": "0 4px 6px -1px rgba(15, 23, 42, 0.08), 0 2px 4px -2px rgba(15, 23, 42, 0.04)",
    },
    "dark": {
        "name": "dark",
        "bg_app": "#0B1020",
        "surface": "#121A2B",
        "surface_subtle": "#182235",
        "surface_elevated": "#1F2937",
        "text_primary": "#F1F5F9",
        "text_secondary": "#A7B3C7",
        "text_muted": "#7C8AA5",
        "border": "#273449",
        "border_subtle": "#1E293B",
        "brand_primary": "#6366F1",
        "brand_hover": "#818CF8",
        "brand_light": "#1E1B4B",
        "primary_gradient": "linear-gradient(135deg, #6366F1 0%, #A855F7 100%)",
        "teal": "#14B8A6",
        "teal_bg": "#134E4A",
        "blue": "#3B82F6",
        "secondary_blue": "#60A5FA",
        "blue_secondary": "#60A5FA",
        "purple": "#8B5CF6",
        "purple_bg": "#3B0764",
        "amber": "#F59E0B",
        "warning": "#F59E0B",
        "warning_bg": "#78350F",
        "success": "#10B981",
        "success_bg": "#064E3B",
        "danger": "#EF4444",
        "danger_bg": "#7F1D1D",
        "chart_colors": [
            "#6366F1",  # Brand Indigo
            "#14B8A6",  # Teal
            "#60A5FA",  # Blue
            "#A78BFA",  # Purple
            "#F59E0B",  # Amber
            "#F472B6",  # Pink
            "#10B981",  # Emerald Green
            "#94A3B8",  # Slate
        ],
        "chart_grid": "#1F2937",
        "chart_border": "#273449",
        "sidebar_bg": "#0F172A",
        "sidebar_text": "#F1F5F9",
        "sidebar_text_muted": "#A7B3C7",
        "sidebar_active_bg": "#211D43",
        "sidebar_active_text": "#E0E7FF",
        "sidebar_active_accent": "#818CF8",
        "sidebar_hover_bg": "#1E293B",
        "sidebar_border": "#263449",
        "shadow_sm": "0 1px 2px 0 rgba(0, 0, 0, 0.25)",
        "shadow_card": "0 1px 3px 0 rgba(0, 0, 0, 0.3), 0 1px 2px -1px rgba(0, 0, 0, 0.2)",
        "card_shadow": "0 1px 3px 0 rgba(0, 0, 0, 0.3), 0 1px 2px -1px rgba(0, 0, 0, 0.2)",
        "shadow_hover": "0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -2px rgba(0, 0, 0, 0.3)",
    }
}


def get_current_theme() -> str:
    """Return active theme string ('light' or 'dark')."""
    return st.session_state.get("theme", "light")


def set_current_theme(theme: str):
    """Update active theme and ensure session state consistency."""
    if theme in ("light", "dark"):
        st.session_state["theme"] = theme


def toggle_theme():
    """Toggle between light and dark themes."""
    curr = get_current_theme()
    set_current_theme("dark" if curr == "light" else "light")


def get_theme_tokens() -> Dict[str, Any]:
    """Return semantic color tokens dictionary for current active theme."""
    theme = get_current_theme()
    return THEME_TOKENS.get(theme, THEME_TOKENS["light"])


def inject_design_system_css():
    """Inject dynamic design tokens and theme-aware styling directly into Streamlit DOM."""
    tokens = get_theme_tokens()

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {{
        --bg-app: {tokens['bg_app']};
        --surface: {tokens['surface']};
        --surface-subtle: {tokens['surface_subtle']};
        --surface-elevated: {tokens['surface_elevated']};
        --text-primary: {tokens['text_primary']};
        --text-secondary: {tokens['text_secondary']};
        --text-muted: {tokens['text_muted']};
        --border: {tokens['border']};
        --border-subtle: {tokens['border_subtle']};
        --brand-primary: {tokens['brand_primary']};
        --brand-hover: {tokens['brand_hover']};
        --brand-light: {tokens['brand_light']};
        --primary-gradient: {tokens['primary_gradient']};
        --success: {tokens['success']};
        --success-bg: {tokens['success_bg']};
        --warning: {tokens['warning']};
        --warning-bg: {tokens['warning_bg']};
        --danger: {tokens['danger']};
        --danger-bg: {tokens['danger_bg']};
        --purple: {tokens['purple']};
        --teal: {tokens['teal']};
        --sidebar-bg: {tokens['sidebar_bg']};
        --sidebar-text: {tokens['sidebar_text']};
        --sidebar-text-muted: {tokens['sidebar_text_muted']};
        --sidebar-active-bg: {tokens['sidebar_active_bg']};
        --sidebar-active-text: {tokens['sidebar_active_text']};
        --sidebar-active-accent: {tokens['sidebar_active_accent']};
        --sidebar-hover-bg: {tokens['sidebar_hover_bg']};
        --sidebar-border: {tokens['sidebar_border']};
        --shadow-sm: {tokens['shadow_sm']};
        --shadow-card: {tokens['shadow_card']};
        --shadow-hover: {tokens['shadow_hover']};
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
    }}

    /* Global Base */
    html, body, [class*="css"], .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        background-color: var(--bg-app) !important;
        color: var(--text-primary) !important;
    }}

    /* Hide Streamlit default native multipage navigation completely */
    div[data-testid="stSidebarNav"],
    ul[data-testid="stSidebarNavItems"] {{
        display: none !important;
        height: 0 !important;
        visibility: hidden !important;
    }}

    /* Streamlit Main Container Spacing */
    .block-container {{
        padding-top: 1.25rem !important;
        padding-bottom: 3.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1440px !important;
    }}

    /* Typography */
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Inter', sans-serif !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
    }}

    p, span, label, div {{
        color: var(--text-primary);
    }}

    /* Sidebar Shell — Enterprise SaaS styling */
    section[data-testid="stSidebar"] {{
        background-color: var(--sidebar-bg) !important;
        border-right: 1px solid var(--sidebar-border) !important;
        width: 300px !important;
        min-width: 300px !important;
    }}

    /* Remove excessive top whitespace and Streamlit 1.22 default 6rem sidebar padding */
    section[data-testid="stSidebar"] > div:first-child {{
        padding-top: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }}

    section[data-testid="stSidebar"] > div > div:last-child {{
        padding-top: 0 !important;
    }}

    section[data-testid="stSidebar"] .block-container {{
        padding-top: 24px !important;
        padding-bottom: 2.5rem !important;
        padding-left: 16px !important;
        padding-right: 16px !important;
        max-width: 100% !important;
    }}

    /* Native sidebar collapse control container & button positioned cleanly */
    section[data-testid="stSidebar"] > div > div:first-child {{
        top: 22px !important;
        right: 14px !important;
        z-index: 50 !important;
    }}

    section[data-testid="stSidebar"] button[kind="header"] {{
        width: 28px !important;
        height: 28px !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        color: var(--sidebar-text-muted) !important;
        opacity: 0.65 !important;
        transition: all 0.15s ease !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 6px !important;
    }}

    section[data-testid="stSidebar"] button[kind="header"]:hover {{
        opacity: 1 !important;
        background: var(--sidebar-hover-bg) !important;
        border-color: var(--sidebar-border) !important;
        color: var(--sidebar-text) !important;
    }}

    section[data-testid="stSidebar"] button[kind="header"] svg {{
        width: 14px !important;
        height: 14px !important;
    }}

    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {{
        color: var(--sidebar-text);
    }}

    /* Clean, flat radiogroup container with no outer oval/pill shape */
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {{
        display: flex !important;
        flex-direction: column !important;
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        padding: 0 !important;
        gap: 0 !important;
        width: 100% !important;
    }}

    /* Remove native radio circle indicators */
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label input[type="radio"],
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > div:first-child {{
        display: none !important;
    }}

    /* Individual navigation items: 42px height, 8px spacing, 10px rounded corners */
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {{
        position: relative !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        padding: 0 12px !important;
        height: 42px !important;
        min-height: 42px !important;
        max-height: 42px !important;
        margin-bottom: 8px !important;
        margin-top: 0 !important;
        border-radius: 10px !important;
        transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer !important;
        display: flex !important;
        align-items: center !important;
        border-left: 3px solid transparent !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        background-color: transparent !important;
    }}

    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label * {{
        white-space: nowrap !important;
    }}

    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label p,
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label span,
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label div {{
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        color: var(--sidebar-text-muted) !important;
        margin: 0 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        transition: color 0.15s ease !important;
    }}

    /* Hover State */
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {{
        background-color: var(--sidebar-hover-bg) !important;
    }}

    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover p,
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover span {{
        color: var(--sidebar-text) !important;
    }}

    /* Active navigation item: slim 3px indicator, mode-specific background & text */
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"],
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) {{
        background-color: var(--sidebar-active-bg) !important;
        border-left: 3px solid var(--sidebar-active-accent) !important;
    }}

    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"] p,
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"] span,
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) p,
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) span,
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) div {{
        color: var(--sidebar-active-text) !important;
        font-weight: 600 !important;
    }}

    /* Group Separators & Section Headers (ANALYTICS, AI & REPORTING, SYSTEM) */
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-child(4) {{
        margin-top: 36px !important;
    }}
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-child(4)::before {{
        content: "ANALYTICS";
        position: absolute;
        top: -24px;
        left: 10px;
        font-size: 0.68rem;
        font-weight: 700;
        color: var(--sidebar-text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        pointer-events: none;
    }}
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-child(4)::after {{
        content: "";
        position: absolute;
        top: -30px;
        left: 4px;
        right: 4px;
        height: 1px;
        background-color: var(--sidebar-border);
        pointer-events: none;
    }}

    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-child(9) {{
        margin-top: 36px !important;
    }}
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-child(9)::before {{
        content: "AI & REPORTING";
        position: absolute;
        top: -24px;
        left: 10px;
        font-size: 0.68rem;
        font-weight: 700;
        color: var(--sidebar-text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        pointer-events: none;
    }}
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-child(9)::after {{
        content: "";
        position: absolute;
        top: -30px;
        left: 4px;
        right: 4px;
        height: 1px;
        background-color: var(--sidebar-border);
        pointer-events: none;
    }}

    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-child(11) {{
        margin-top: 36px !important;
    }}
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-child(11)::before {{
        content: "SYSTEM";
        position: absolute;
        top: -24px;
        left: 10px;
        font-size: 0.68rem;
        font-weight: 700;
        color: var(--sidebar-text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        pointer-events: none;
    }}
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:nth-child(11)::after {{
        content: "";
        position: absolute;
        top: -30px;
        left: 4px;
        right: 4px;
        height: 1px;
        background-color: var(--sidebar-border);
        pointer-events: none;
    }}

    /* Header Theme Switcher Segmented Control (strictly in main content, never sidebar) */
    .app-header .stRadio div[role="radiogroup"],
    section.main .stRadio div[role="radiogroup"] {{
        display: inline-flex !important;
        flex-direction: row !important;
        background: var(--surface-subtle) !important;
        border: 1px solid var(--border) !important;
        border-radius: 9999px !important;
        padding: 3px !important;
        gap: 3px !important;
        align-items: center !important;
        box-shadow: var(--shadow-sm) !important;
    }}

    .app-header .stRadio div[role="radiogroup"] > label input[type="radio"],
    .app-header .stRadio div[role="radiogroup"] > label > div:first-child,
    section.main .stRadio div[role="radiogroup"] > label input[type="radio"],
    section.main .stRadio div[role="radiogroup"] > label > div:first-child {{
        display: none !important;
    }}

    .app-header .stRadio div[role="radiogroup"] > label,
    section.main .stRadio div[role="radiogroup"] > label {{
        margin: 0 !important;
        padding: 3px 12px !important;
        height: 28px !important;
        min-height: 28px !important;
        max-height: 28px !important;
        border-radius: 9999px !important;
        cursor: pointer !important;
        font-size: 0.775rem !important;
        font-weight: 500 !important;
        color: var(--text-secondary) !important;
        transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: 1px solid transparent !important;
        background: transparent !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}

    .app-header .stRadio div[role="radiogroup"] > label p,
    section.main .stRadio div[role="radiogroup"] > label p {{
        margin: 0 !important;
        font-size: 0.775rem !important;
        font-weight: 500 !important;
        color: var(--text-secondary) !important;
        white-space: nowrap !important;
        transition: color 0.15s ease !important;
    }}

    .app-header .stRadio div[role="radiogroup"] > label:hover p,
    section.main .stRadio div[role="radiogroup"] > label:hover p {{
        color: var(--text-primary) !important;
    }}

    .app-header .stRadio div[role="radiogroup"] > label[data-checked="true"],
    .app-header .stRadio div[role="radiogroup"] > label:has(input:checked),
    section.main .stRadio div[role="radiogroup"] > label[data-checked="true"],
    section.main .stRadio div[role="radiogroup"] > label:has(input:checked) {{
        background: var(--surface) !important;
        border-color: var(--border) !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    }}

    .app-header .stRadio div[role="radiogroup"] > label[data-checked="true"] p,
    .app-header .stRadio div[role="radiogroup"] > label:has(input:checked) p,
    section.main .stRadio div[role="radiogroup"] > label[data-checked="true"] p,
    section.main .stRadio div[role="radiogroup"] > label:has(input:checked) p {{
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }}

    /* Native Widget Form Controls */
    .stSelectbox > div > div, .stTextInput > div > div, .stMultiSelect > div > div {{
        background-color: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
        box-shadow: var(--shadow-sm) !important;
        font-size: 0.875rem !important;
    }}

    .stSelectbox label, .stTextInput label, .stMultiSelect label, .stSlider label {{
        font-size: 0.825rem !important;
        font-weight: 500 !important;
        color: var(--text-secondary) !important;
        margin-bottom: 4px !important;
    }}

    /* Buttons */
    button[kind="primary"] {{
        background: var(--brand-primary) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        padding: 0.5rem 1.15rem !important;
        box-shadow: 0 1px 2px rgba(79, 70, 229, 0.2) !important;
        transition: all 0.15s ease !important;
    }}

    button[kind="primary"]:hover {{
        background: var(--brand-hover) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(79, 70, 229, 0.3) !important;
    }}

    button[kind="secondary"] {{
        background: var(--surface) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        transition: all 0.15s ease !important;
    }}

    button[kind="secondary"]:hover {{
        background: var(--surface-subtle) !important;
        border-color: var(--text-muted) !important;
    }}

    /* Tabs — Enhanced Enterprise Component */
    div[data-baseweb="tab-list"] {{
        background-color: var(--surface-subtle) !important;
        border-radius: var(--radius-md) !important;
        padding: 4px !important;
        gap: 4px !important;
        border: 1px solid var(--border) !important;
        display: flex !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        scrollbar-width: none !important;
        margin-bottom: 1.25rem !important;
    }}

    div[data-baseweb="tab-list"]::-webkit-scrollbar {{
        display: none !important;
    }}

    div[data-baseweb="tab-border"],
    div[data-baseweb="tab-highlight"] {{
        display: none !important;
        height: 0 !important;
        background: transparent !important;
    }}

    div[data-baseweb="tab"],
    button[data-baseweb="tab"] {{
        border-radius: var(--radius-sm) !important;
        padding: 0.5rem 1.15rem !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        color: var(--text-secondary) !important;
        border: 1px solid transparent !important;
        background: transparent !important;
        background-color: transparent !important;
        transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer !important;
        white-space: nowrap !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}

    div[data-baseweb="tab"]:hover,
    button[data-baseweb="tab"]:hover {{
        background-color: var(--surface) !important;
        color: var(--text-primary) !important;
    }}

    div[data-baseweb="tab"][aria-selected="true"],
    button[data-baseweb="tab"][aria-selected="true"] {{
        background-color: var(--surface) !important;
        color: var(--brand-primary) !important;
        font-weight: 600 !important;
        border: 1px solid var(--border) !important;
        box-shadow: var(--shadow-sm) !important;
    }}

    div[data-baseweb="tab"] p,
    div[data-baseweb="tab"] span,
    button[data-baseweb="tab"] p,
    button[data-baseweb="tab"] span {{
        color: inherit !important;
        font-size: 0.85rem !important;
        font-weight: inherit !important;
        margin: 0 !important;
        white-space: nowrap !important;
    }}

    /* Dataframe Table Container */
    div[data-testid="stDataFrame"] {{
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        background-color: var(--surface) !important;
        overflow: hidden !important;
        box-shadow: var(--shadow-card) !important;
    }}

    /* Expanders */
    div[data-testid="stExpander"] {{
        background-color: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        box-shadow: var(--shadow-sm) !important;
        margin-bottom: 1rem !important;
    }}

    div[data-testid="stExpander"] summary {{
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 0.75rem 1rem !important;
    }}

    /* Metric Cards */
    div[data-testid="stMetric"] {{
        background-color: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        padding: 1.15rem 1.35rem !important;
        box-shadow: var(--shadow-card) !important;
    }}

    div[data-testid="stMetricLabel"] {{
        color: var(--text-secondary) !important;
        font-size: 0.785rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
    }}

    div[data-testid="stMetricValue"] {{
        color: var(--text-primary) !important;
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }}

    /* Alert Boxes — Theme-Aware */
    .alert-box {{
        display: flex !important;
        align-items: flex-start !important;
        gap: 0.75rem !important;
        padding: 0.85rem 1.15rem !important;
        border-radius: var(--radius-sm) !important;
        font-size: 0.85rem !important;
        line-height: 1.45 !important;
        margin-bottom: 1rem !important;
        background-color: var(--surface) !important;
        border: 1px solid var(--border) !important;
    }}

    .alert-box.info {{
        background-color: var(--brand-light) !important;
        border: 1px solid var(--border) !important;
        color: var(--brand-primary) !important;
    }}

    .alert-box.warning {{
        background-color: var(--warning-bg) !important;
        border: 1px solid var(--warning) !important;
        color: var(--warning) !important;
    }}

    .alert-box.success {{
        background-color: var(--success-bg) !important;
        border: 1px solid var(--success) !important;
        color: var(--success) !important;
    }}

    .alert-box.danger,
    .alert-box.error {{
        background-color: var(--danger-bg) !important;
        border: 1px solid var(--danger) !important;
        color: var(--danger) !important;
    }}

    /* Responsive Adaptations */
    @media (max-width: 1024px) {{
        .block-container {{
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
            padding-top: 1rem !important;
        }}

        div[data-testid="stMetric"] {{
            padding: 0.85rem 1rem !important;
        }}

        div[data-testid="stMetricValue"] {{
            font-size: 1.5rem !important;
        }}
    }}

    @media (max-width: 768px) {{
        .block-container {{
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
            padding-top: 0.75rem !important;
            padding-bottom: 2rem !important;
        }}

        div[data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important;
            gap: 0.75rem !important;
        }}

        div[data-testid="column"] {{
            min-width: calc(50% - 0.5rem) !important;
            flex: 1 1 calc(50% - 0.5rem) !important;
        }}

        section.main .stRadio div[role="radiogroup"] {{
            padding: 2px !important;
        }}

        section.main .stRadio div[role="radiogroup"] > label {{
            padding: 2px 8px !important;
            font-size: 0.725rem !important;
        }}

        .js-plotly-plot, .plot-container {{
            width: 100% !important;
            max-width: 100% !important;
        }}

        div[data-testid="stDataFrame"] {{
            width: 100% !important;
            overflow-x: auto !important;
        }}
    }}

    @media (max-width: 480px) {{
        div[data-testid="column"] {{
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }}

        h1 {{
            font-size: 1.4rem !important;
        }}

        div[data-testid="stMetricValue"] {{
            font-size: 1.35rem !important;
        }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
