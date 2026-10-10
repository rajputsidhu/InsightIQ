"""
Application Header Component for InsightIQ.
Renders breadcrumbs, active workspace indicator, compact dataset status badge,
and the top-level Light/Dark theme switcher.
"""

import streamlit as st
from components.design_system import get_current_theme, set_current_theme, get_theme_tokens


def render_header(page_title: str, category: str = "Analytics"):
    """Render top application header with breadcrumb trail, dataset status, and theme toggle."""
    tokens = get_theme_tokens()
    current_theme = get_current_theme()

    active_dataset = st.session_state.get("active_dataset_name", "No Dataset Loaded")
    row_count = len(st.session_state.get("raw_df", [])) if st.session_state.get("raw_df") is not None else 0

    col_left, col_right = st.columns([1.5, 1.5])

    with col_left:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; height: 38px; gap: 0.5rem; font-size: 0.85rem; color: {tokens['text_secondary']};">
                <span style="font-weight: 700; color: {tokens['brand_primary']};">InsightIQ</span>
                <span style="color: {tokens['text_muted']};">/</span>
                <span>{category}</span>
                <span style="color: {tokens['text_muted']};">/</span>
                <span style="font-weight: 600; color: {tokens['text_primary']};">{page_title}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        ds_col, theme_col = st.columns([1.1, 0.9])

        with ds_col:
            if row_count > 0:
                pill_bg = tokens["brand_light"]
                pill_color = tokens["brand_primary"]
                pill_border = tokens["border"]
                pill_text = f"● {active_dataset} ({row_count:,} rows)"
            else:
                pill_bg = tokens["warning_bg"]
                pill_color = tokens["warning"]
                pill_border = tokens["warning"]
                pill_text = "○ No Dataset"

            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-end; align-items: center; height: 38px;">
                    <div style="background: {pill_bg}; color: {pill_color}; border: 1px solid {pill_border}; border-radius: 9999px; padding: 4px 12px; font-size: 0.775rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 250px;" title="{active_dataset} ({row_count:,} rows)">
                        {pill_text}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with theme_col:
            # Segmented theme control: ☀️ Light and 🌙 Dark
            st.markdown('<div class="header-theme-switcher" style="display: flex; justify-content: flex-end; align-items: center; height: 38px;">', unsafe_allow_html=True)
            theme_choice = st.radio(
                "Theme Mode",
                options=["☀️ Light", "🌙 Dark"],
                index=0 if current_theme == "light" else 1,
                horizontal=True,
                label_visibility="collapsed",
                key=f"hdr_theme_seg_{current_theme}",
            )
            st.markdown('</div>', unsafe_allow_html=True)

            selected_mode = "dark" if "Dark" in theme_choice else "light"
            if selected_mode != current_theme:
                set_current_theme(selected_mode)
                st.rerun()


    # Subtle bottom border
    st.markdown(
        f"<div style='border-bottom: 1px solid {tokens['border']}; margin-bottom: 1.25rem;'></div>",
        unsafe_allow_html=True,
    )
