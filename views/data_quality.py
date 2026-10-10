"""
Data Quality Diagnostics & Interactive Cleaning Workbench for InsightIQ.
Provides data health grading, anomaly audits, deduplication, imputation,
outlier capping, and transformation audit trails.
"""

import streamlit as st
import pandas as pd
import numpy as np
from components.header import render_header
from components.ui_components import render_page_title, render_section_header, render_empty_state
from components.alerts import render_alert
from components.design_system import get_theme_tokens
from services.data_validation import compute_data_quality_report
from services.data_cleaning import DataCleaningService
from services.report_generator import export_dataframe_to_csv_bytes


def render_data_quality_page():
    """Render data quality auditing and interactive cleaning workbench."""
    render_header("Data Quality", "Workspace")

    raw_df: pd.DataFrame = st.session_state.get("raw_df")
    active_df: pd.DataFrame = st.session_state.get("active_df")

    if raw_df is None or raw_df.empty:
        render_empty_state(
            title="No Active Dataset Available",
            description="Load a demo dataset or upload a file from the sidebar to inspect data quality metrics.",
            icon="🛡️"
        )
        return

    tokens = get_theme_tokens()
    render_page_title(
        "Data Quality & Hygiene Workbench",
        "Audit dataset health scores, identify missingness or duplicates, and execute non-destructive cleaning transformations."
    )

    # Initialize cleaning service in session state if missing
    if "cleaning_service" not in st.session_state:
        st.session_state["cleaning_service"] = DataCleaningService(raw_df)

    cleaner: DataCleaningService = st.session_state["cleaning_service"]
    current_df = cleaner.clean_df

    # Run Data Quality Diagnostics on current working DataFrame
    report = compute_data_quality_report(current_df)

    # Top Quality Score & KPI Cards Grid
    score_val = report["overall_score"]
    grade = report["grade"]
    score_color = tokens["success"] if score_val >= 80 else (tokens["warning"] if score_val >= 60 else tokens["danger"])
    outlier_count = sum(o["count"] for o in report.get("outlier_summary", {}).values())

    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.markdown(
            f"""
            <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 12px; padding: 1.15rem; box-shadow: {tokens['card_shadow']};">
                <div style="font-size: 0.75rem; color: {tokens['text_muted']}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;">Data Health Score</div>
                <div style="font-size: 2rem; font-weight: 800; color: {score_color}; line-height: 1.2; margin-top: 2px;">
                    {score_val:.0f}<span style="font-size: 1rem; color: {tokens['text_muted']};">/100</span>
                </div>
                <div style="font-size: 0.8rem; font-weight: 600; color: {tokens['text_secondary']}; margin-top: 4px;">Grade: {grade} Rating</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with sc2:
        _render_stat_card("Completeness", f"{100 - report['missing_pct']:.1f}%", f"{report['missing_cells']:,} missing cells", tokens["success"] if report['missing_pct'] == 0 else tokens["warning"])
    with sc3:
        _render_stat_card("Uniqueness", f"{100 - report['duplicate_pct']:.1f}%", f"{report['duplicate_rows']:,} duplicates", tokens["success"] if report['duplicate_rows'] == 0 else tokens["danger"])
    with sc4:
        _render_stat_card("Outlier Points", f"{outlier_count:,}", f"Across {len(report.get('outlier_summary', {}))} columns", tokens["teal"])

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # Tabs for Quality Diagnostics vs Interactive Cleaning Workbench
    tab_diag, tab_clean, tab_audit = st.tabs([
        "🔍 Health Diagnostics & Issues",
        "🛠️ Interactive Cleaning Workbench",
        "📜 Operations Audit Trail",
    ])

    with tab_diag:
        render_section_header("Detected Quality Issues & Anomalies", subtitle="Automated inspection findings requiring attention.")
        if report["issues"]:
            for issue in report["issues"]:
                st.markdown(
                    f"""
                    <div style="background: {tokens['surface']}; border-left: 3px solid {tokens['warning']}; border-top: 1px solid {tokens['border']}; border-right: 1px solid {tokens['border']}; border-bottom: 1px solid {tokens['border']}; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; font-size: 0.875rem; color: {tokens['text_primary']};">
                        ⚠️ {issue}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.success("No critical quality issues detected.")

        render_section_header("Prescriptive Data Hygiene Recommendations")
        for rec in report["recommendations"]:
            st.markdown(
                f"""
                <div style="background: {tokens['surface_subtle']}; border-left: 3px solid {tokens['brand_primary']}; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; font-size: 0.875rem; color: {tokens['text_secondary']};">
                    💡 {rec}
                </div>
                """,
                unsafe_allow_html=True,
            )

        render_section_header("Column-Level Integrity Breakdown", subtitle="Detailed distribution of null counts, unique cardinality, and IQR outliers.")
        col_metrics_df = pd.DataFrame(report["column_metrics"])
        if not hasattr(st, "column_config") or isinstance(getattr(st, "column_config", None), type):
            col_metrics_df["null_pct"] = col_metrics_df["null_pct"].apply(lambda v: f"{v:.2f}%")
        st.dataframe(
            col_metrics_df,
            column_config={
                "column": "Column",
                "dtype": "Type",
                "null_count": "Missing Count",
                "null_pct": st.column_config.NumberColumn("Missing %", format="%.2f%%"),
                "unique_count": "Unique Values",
                "outliers_iqr": "IQR Outliers",
                "min": "Min",
                "max": "Max",
                "mean": "Mean",
                "is_constant": "Zero Variance?",
            },
            use_container_width=True,
            hide_index=True,
        )

    with tab_clean:
        render_section_header("Execute Cleaning Operations", subtitle="Transformations immediately update the active workspace while preserving raw uploads.")
        render_alert("Cleaning operations update the active working dataset. The raw original dataset is preserved.", level="info")

        op_col1, op_col2 = st.columns(2)

        with op_col1:
            st.markdown(f"<div style='font-size: 0.875rem; font-weight: 700; color: {tokens['text_primary']}; margin-bottom: 0.5rem;'>1. Deduplication</div>", unsafe_allow_html=True)
            if st.button("🗑️ Remove Duplicate Rows", use_container_width=True):
                removed, _ = cleaner.remove_duplicates()
                st.session_state["active_df"] = cleaner.clean_df
                if removed > 0:
                    st.success(f"Removed {removed:,} duplicate records.")
                else:
                    st.info("No duplicate rows found.")
                st.rerun()

            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 0.875rem; font-weight: 700; color: {tokens['text_primary']}; margin-bottom: 0.5rem;'>2. Missing Value Imputation</div>", unsafe_allow_html=True)
            target_null_col = st.selectbox("Select Column to Impute", options=list(current_df.columns), key="dq_impute_col")

            if target_null_col:
                is_num = pd.api.types.is_numeric_dtype(current_df[target_null_col])
                if is_num:
                    strategy = st.selectbox("Numeric Strategy", options=["median", "mean", "zero", "custom"], key="dq_num_strat")
                    custom_v = None
                    if strategy == "custom":
                        custom_v = st.number_input("Custom Replacement Value", value=0.0)
                    if st.button(f"Apply Numeric Imputation to '{target_null_col}'", use_container_width=True):
                        cnt, _ = cleaner.fill_numeric_missing(target_null_col, strategy=strategy, custom_val=custom_v)
                        st.session_state["active_df"] = cleaner.clean_df
                        st.success(f"Imputed {cnt} missing values in '{target_null_col}'.")
                        st.rerun()
                else:
                    cat_strat = st.selectbox("Categorical Strategy", options=["constant", "mode", "ffill"], key="dq_cat_strat")
                    custom_str = "Unknown"
                    if cat_strat == "constant":
                        custom_str = st.text_input("Fill Value", value="Unknown")
                    if st.button(f"Apply Categorical Imputation to '{target_null_col}'", use_container_width=True):
                        cnt, _ = cleaner.fill_categorical_missing(target_null_col, strategy=cat_strat, custom_val=custom_str)
                        st.session_state["active_df"] = cleaner.clean_df
                        st.success(f"Imputed {cnt} missing values in '{target_null_col}'.")
                        st.rerun()

        with op_col2:
            st.markdown(f"<div style='font-size: 0.875rem; font-weight: 700; color: {tokens['text_primary']}; margin-bottom: 0.5rem;'>3. Data Type Standardization</div>", unsafe_allow_html=True)
            type_col = st.selectbox("Select Column to Cast", options=list(current_df.columns), key="cast_col_select")
            target_t = st.selectbox("Target Type", options=["numeric", "datetime", "string", "category"], key="cast_target_select")
            if st.button(f"Convert '{type_col}' to {target_t}", use_container_width=True):
                ok, _ = cleaner.convert_column_type(type_col, target_t)
                st.session_state["active_df"] = cleaner.clean_df
                if ok:
                    st.success(f"Converted '{type_col}' to {target_t}.")
                else:
                    st.error(f"Failed to convert '{type_col}'.")
                st.rerun()

            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 0.875rem; font-weight: 700; color: {tokens['text_primary']}; margin-bottom: 0.5rem;'>4. Outlier Capping (Winsorization)</div>", unsafe_allow_html=True)
            num_cols = current_df.select_dtypes(include=[np.number]).columns.tolist()
            if num_cols:
                outlier_col = st.selectbox("Select Numeric Column to Cap", options=num_cols, key="dq_outlier_col")
                iqr_factor = st.slider("IQR Multiplier Factor", min_value=1.0, max_value=3.0, value=1.5, step=0.25)
                if st.button(f"Cap Outliers in '{outlier_col}' ({iqr_factor}x IQR)", use_container_width=True):
                    capped, _ = cleaner.cap_outliers_iqr(outlier_col, factor=iqr_factor)
                    st.session_state["active_df"] = cleaner.clean_df
                    st.success(f"Capped {capped} extreme outliers in '{outlier_col}'.")
                    st.rerun()
            else:
                st.info("No numeric columns available for outlier treatment.")

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        # Reset to Raw button
        if st.button("↺ Reset Active Dataset to Original Upload", type="secondary"):
            st.session_state["cleaning_service"] = DataCleaningService(raw_df)
            st.session_state["active_df"] = raw_df.copy()
            st.info("Reset active workspace to original raw dataset.")
            st.rerun()

    with tab_audit:
        render_section_header("Data Cleansing Summary & Audit Trail", subtitle="Chronological ledger of data transformations performed on this dataset.")
        summary = cleaner.get_summary()

        sum_c1, sum_c2, sum_c3 = st.columns(3)
        with sum_c1:
            _render_stat_card("Rows Retained", f"{summary['final_rows']:,}", f"From {summary['initial_rows']:,}", tokens["brand_primary"])
        with sum_c2:
            _render_stat_card("Missing Cells", f"{summary['final_missing']:,}", f"From {summary['initial_missing']:,}", tokens["teal"])
        with sum_c3:
            _render_stat_card("Logged Operations", f"{summary['operations_count']}", "Total transforms", tokens["purple"])

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        if summary["audit_trail"]:
            audit_df = pd.DataFrame(summary["audit_trail"])
            st.dataframe(audit_df, use_container_width=True, hide_index=True)
        else:
            st.info("No transformations applied yet.")

        # Download Cleaned Dataset
        render_section_header("Export Cleansed Dataset", subtitle="Download a validated snapshot of the cleaned records.")
        clean_csv_bytes = export_dataframe_to_csv_bytes(cleaner.clean_df)
        st.download_button(
            label="⬇️ Download Cleaned Dataset (CSV)",
            data=clean_csv_bytes,
            file_name="insightiq_cleaned_dataset.csv",
            mime="text/csv",
        )



def _render_stat_card(label: str, value: str, subtext: str, accent: str):
    """Render a clean metric summary card."""
    tokens = get_theme_tokens()
    st.markdown(
        f"""
        <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 12px; padding: 1.15rem; box-shadow: {tokens['card_shadow']};">
            <div style="font-size: 0.75rem; color: {tokens['text_muted']}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;">{label}</div>
            <div style="font-size: 1.6rem; font-weight: 700; color: {tokens['text_primary']}; margin-top: 2px; font-variant-numeric: tabular-nums;">{value}</div>
            <div style="font-size: 0.775rem; color: {tokens['text_secondary']}; margin-top: 2px;">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
