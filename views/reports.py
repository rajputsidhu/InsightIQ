"""
Reports and Export Center Page for InsightIQ.
Provides 1-click executive PDF generation, 16:9 widescreen PowerPoint deck compilation,
and unified CSV analytical datasets exports.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from components.header import render_header
from components.ui_components import render_page_title, render_section_header, render_empty_state
from components.alerts import render_alert, render_methodology_disclaimer
from components.design_system import get_theme_tokens
from services.business_metrics import infer_business_columns, calculate_executive_kpis
from services.insight_engine import generate_business_insights
from services.data_validation import compute_data_quality_report
from services.report_generator import generate_pdf_report, export_dataframe_to_csv_bytes
from services.presentation_generator import PresentationGenerator


def render_reports_page():
    """Render PDF report generation, PowerPoint compilation, and CSV export hub."""
    render_header("Reports & Exports", "Reporting")

    df: pd.DataFrame = st.session_state.get("active_df")
    active_name = st.session_state.get("active_dataset_name", "Active Workspace Dataset")

    if df is None or df.empty:
        render_empty_state(
            title="No Active Dataset Available",
            description="Load a business or transaction dataset from the sidebar to generate executive reports and exports.",
            icon="📄"
        )
        return

    tokens = get_theme_tokens()
    render_page_title(
        "Executive Reports & Export Center",
        "Generate publication-ready PDF briefs, 16:9 PowerPoint pitch decks, and normalized CSV analytical exports."
    )

    col_map = st.session_state.get("col_map") or infer_business_columns(df)
    kpis = st.session_state.get("kpis") or calculate_executive_kpis(df, col_map)
    dq_report = compute_data_quality_report(df)
    insights = st.session_state.get("business_insights") or generate_business_insights(df, col_map, kpis)

    tab_pdf, tab_pptx, tab_exports = st.tabs([
        "📄 Executive PDF Report Builder",
        "📊 PowerPoint Presentation (.pptx)",
        "📦 Unified Data Export Center",
    ])

    with tab_pdf:
        render_section_header("1-Click Executive PDF Briefing", subtitle="Formal printable briefing with computed KPIs, data quality health, and insights.")
        render_alert(
            "Generates a formal, printable PDF document containing computed business KPIs, "
            "data quality diagnostics, evidence-based insights, and methodological boundary notices.",
            level="info"
        )

        p_col1, p_col2 = st.columns([2, 1.2])
        with p_col1:
            st.markdown(
                f"""
                <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 10px; padding: 1.25rem; font-size: 0.9rem; line-height: 1.6; color: {tokens['text_secondary']}; box-shadow: {tokens['card_shadow']};">
                    <div><strong style="color: {tokens['text_primary']};">Target Dataset:</strong> <code>{active_name}</code> ({len(df):,} records)</div>
                    <div><strong style="color: {tokens['text_primary']};">Generation Date:</strong> {datetime.now().strftime('%B %d, %Y')}</div>
                    <div><strong style="color: {tokens['text_primary']};">Verified Insights:</strong> {len(insights)} analytical findings included</div>
                    <div><strong style="color: {tokens['text_primary']};">Quality Health Score:</strong> {dq_report.get('overall_score', 0):.0f}/100 ({dq_report.get('grade', 'N/A')})</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with p_col2:
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            cached_pdf = st.session_state.get("cached_pdf_report")
            cached_pdf_ds = st.session_state.get("cached_pdf_dataset")
            if cached_pdf is None or cached_pdf_ds != active_name:
                with st.spinner("Compiling PDF document layout..."):
                    cached_pdf = generate_pdf_report(
                        kpis=kpis,
                        insights=insights,
                        data_quality=dq_report,
                        dataset_name=active_name
                    )
                    st.session_state["cached_pdf_report"] = cached_pdf
                    st.session_state["cached_pdf_dataset"] = active_name
            
            st.download_button(
                label="📥 Download Executive PDF Report",
                data=cached_pdf,
                file_name=f"insightiq_executive_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )


    with tab_pptx:
        render_section_header("Executive PowerPoint Pitch Deck", subtitle="16:9 widescreen presentation deck with executive KPI grids and predictive summaries.")
        render_alert(
            "Generates a corporate 16:9 widescreen presentation deck complete with "
            "executive KPI grids, strategic business insights, predictive risk modeling summaries, and methodology notices.",
            level="info"
        )

        pptx_col1, pptx_col2 = st.columns([2, 1.2])
        with pptx_col1:
            st.markdown(
                f"""
                <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 10px; padding: 1.25rem; font-size: 0.9rem; line-height: 1.6; color: {tokens['text_secondary']}; box-shadow: {tokens['card_shadow']};">
                    <div><strong style="color: {tokens['text_primary']};">Output Format:</strong> Microsoft PowerPoint (.pptx) Widescreen 16:9</div>
                    <div><strong style="color: {tokens['text_primary']};">Included Sections:</strong> Executive Overview, KPI Dashboard, Strategic Priorities, Governance</div>
                    <div><strong style="color: {tokens['text_primary']};">Target Dataset:</strong> <code>{active_name}</code></div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with pptx_col2:
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            cached_pptx = st.session_state.get("cached_pptx_deck")
            cached_pptx_ds = st.session_state.get("cached_pptx_dataset")
            if cached_pptx is None or cached_pptx_ds != active_name:
                with st.spinner("Generating widescreen PowerPoint deck..."):
                    cached_pptx = PresentationGenerator.generate_deck(
                        kpis=kpis,
                        insights=insights,
                        dataset_name=active_name
                    )
                    st.session_state["cached_pptx_deck"] = cached_pptx
                    st.session_state["cached_pptx_dataset"] = active_name

            st.download_button(
                label="📥 Download PowerPoint Deck (.pptx)",
                data=cached_pptx,
                file_name=f"insightiq_executive_deck_{datetime.now().strftime('%Y%m%d')}.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
            )


    with tab_exports:
        render_section_header("Unified CSV Analytical Exports", subtitle="Download structured tabular extracts for downstream spreadsheets and audits.")

        e_col1, e_col2 = st.columns(2)

        with e_col1:
            st.markdown(f"<div style='font-size: 0.9rem; font-weight: 700; color: {tokens['text_primary']}; margin-bottom: 0.25rem;'>1. Active Working Dataset</div>", unsafe_allow_html=True)
            st.caption(f"Cleansed active tabular records ({len(df):,} rows).")
            active_csv_bytes = export_dataframe_to_csv_bytes(df)
            st.download_button(
                label="⬇️ Download Active Dataset (CSV)",
                data=active_csv_bytes,
                file_name="insightiq_active_dataset.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_active_csv_btn",
            )

            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 0.9rem; font-weight: 700; color: {tokens['text_primary']}; margin-bottom: 0.25rem;'>2. Executive KPI Summary</div>", unsafe_allow_html=True)
            st.caption("Calculated business metrics and high-level totals.")
            kpi_records = [
                {"Metric": "Total Revenue", "Value": kpis.get("total_revenue", 0)},
                {"Metric": "Total Orders", "Value": kpis.get("total_orders", 0)},
                {"Metric": "Average Order Value", "Value": kpis.get("average_order_value", 0)},
                {"Metric": "Total Profit", "Value": kpis.get("total_profit", 0)},
                {"Metric": "Profit Margin %", "Value": kpis.get("profit_margin_pct", 0)},
                {"Metric": "Unique Customers", "Value": kpis.get("unique_customers", 0)},
                {"Metric": "Repeat Customer %", "Value": kpis.get("repeat_customer_pct", 0)},
                {"Metric": "Revenue Growth %", "Value": kpis.get("revenue_growth_pct", 0)},
            ]
            kpi_csv_bytes = export_dataframe_to_csv_bytes(pd.DataFrame(kpi_records))
            st.download_button(
                label="⬇️ Download KPI Summary (CSV)",
                data=kpi_csv_bytes,
                file_name="insightiq_kpi_summary.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_kpi_csv_btn",
            )

        with e_col2:
            st.markdown(f"<div style='font-size: 0.9rem; font-weight: 700; color: {tokens['text_primary']}; margin-bottom: 0.25rem;'>3. Business Insights & Recommendations</div>", unsafe_allow_html=True)
            st.caption(f"{len(insights)} computed analytical findings.")
            ins_records = [{
                "Category": i.get("category"),
                "Title": i.get("title"),
                "Severity": i.get("severity"),
                "Finding": i.get("finding"),
                "Metric": i.get("supporting_metric"),
                "Top_Action": i.get("recommended_actions", [""])[0],
            } for i in insights]
            ins_csv_bytes = export_dataframe_to_csv_bytes(pd.DataFrame(ins_records))
            st.download_button(
                label="⬇️ Download Insights Summary (CSV)",
                data=ins_csv_bytes,
                file_name="insightiq_insights_export.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_ins_csv_btn",
            )

    render_methodology_disclaimer()
