"""
Time-Series Revenue & Metric Forecasting Page for InsightIQ.
Integrates sequential holdout backtesting, baseline models (Naive, Moving Average, Holt linear),
advanced models (Seasonal Naive, Holt-Winters, ARIMA), STL decomposition, and robust anomaly detection.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from components.header import render_header
from components.ui_components import render_page_title, render_section_header, render_empty_state
from components.kpi_cards import render_kpi_card
from components.charts import plot_time_series_forecast, apply_theme
from components.alerts import render_alert, render_methodology_disclaimer
from components.design_system import get_theme_tokens
from services.business_metrics import infer_business_columns
from services.forecasting import prepare_time_series, run_forecasting_pipeline
from services.advanced_forecasting import AdvancedForecastingService
from services.time_series_anomalies import TimeSeriesAnomalyDetector
from services.data_loader import get_demo_dataset
from services.report_generator import export_dataframe_to_csv_bytes


def render_revenue_forecasting_page():
    """Render the time-series forecasting, decomposition, and anomaly workspace."""
    render_header("Revenue Forecasting", "Analytics")

    df: pd.DataFrame = st.session_state.get("active_df")

    if df is None or df.empty:
        render_empty_state(
            title="No Active Dataset Available",
            description="Load a time-series or MRR dataset from the sidebar (e.g. 'Demo SaaS Metrics') to run revenue projections.",
            icon="📈"
        )
        return

    tokens = get_theme_tokens()
    col_map = st.session_state.get("col_map") or infer_business_columns(df)
    cols = list(df.columns)

    date_candidates = [c for c in cols if any(k in c.lower() for k in ["date", "period", "month", "time", "year"])]
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if not date_candidates or not num_cols:
        render_alert(
            "Forecasting requires at least one Date column and one Numeric Target metric. "
            "You can load 'Demo SaaS Metrics' or 'Demo E-Commerce Orders' from the sidebar.",
            level="warning",
            title="Required Columns Missing"
        )
        if st.button("📈 Load Demo SaaS Time-Series Dataset", type="primary"):
            saas_df = get_demo_dataset("saas")
            from components.sidebar import _set_active_dataset
            _set_active_dataset("Demo SaaS Metrics", saas_df)
            st.rerun()
        return

    render_page_title(
        "Predictive Revenue & Metric Forecasting",
        "Generate multi-period revenue projections, backtested confidence bounds, seasonal STL decompositions, and anomaly flags."
    )

    # Configuration Controls
    with st.expander("⚙️ Forecasting Configuration & Scenario Assumptions", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            sel_date_col = st.selectbox(
                "Date / Time Column",
                options=date_candidates + [c for c in cols if c not in date_candidates],
                index=0,
                key="fc_date_col",
            )
        with f_col2:
            sel_target_col = st.selectbox(
                "Target Metric",
                options=num_cols,
                index=0,
                key="fc_target_col",
            )
        with f_col3:
            sel_freq = st.selectbox(
                "Aggregation Frequency",
                options=["Monthly (MS)", "Weekly (W)", "Daily (D)"],
                index=0,
                key="fc_freq",
            )
            freq_code = "MS" if "Monthly" in sel_freq else ("W" if "Weekly" in sel_freq else "D")

        with f_col4:
            horizon = st.slider("Forecast Horizon (Periods)", min_value=2, max_value=18, value=6, key="fc_horizon")

        scenario_mult = st.slider(
            "Scenario Demand Adjustment Multiplier",
            min_value=0.70,
            max_value=1.30,
            value=1.00,
            step=0.05,
            format="%.2fx",
            help="Simulate conservative (0.85x) or aggressive (1.15x) macroeconomic demand conditions.",
            key="fc_scenario_mult",
        )

        run_fc_btn = st.button("🚀 Update Predictive Forecast", type="primary", key="btn_run_fc")

    # Run Time Series Preparation
    ts_series, ts_err = prepare_time_series(df, sel_date_col, sel_target_col, freq=freq_code)
    if ts_err:
        st.error(ts_err)
        return

    with st.spinner("Executing time-series backtesting and uncertainty modeling..."):
        fc_results = run_forecasting_pipeline(ts_series, horizon=horizon, scenario_multiplier=scenario_mult)
        adv_models = AdvancedForecastingService.evaluate_extended_models(ts_series, horizon=horizon, seasonal_period=12 if freq_code == "MS" else 4)
        stl_result = AdvancedForecastingService.perform_stl_decomposition(ts_series)
        anomaly_result = TimeSeriesAnomalyDetector.detect_anomalies(ts_series, threshold_sigma=2.5)

    st.session_state["forecast_results"] = fc_results

    best_model = fc_results["best_model"]
    summary = fc_results["summary"]
    forecast_df = fc_results["forecast_df"]
    historical_df = fc_results["historical_df"]

    # Top KPI Metrics Grid
    render_section_header("Forecast Trajectory & Volatility", subtitle=f"Projections computed across {summary['total_historical_periods']} historical periods.", badge="Backtested")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card("Best Time-Series Model", best_model, "Selected via Backtesting RMSE", accent="blue")
    with k2:
        render_kpi_card("Historical Mean", f"${summary['historical_mean']:,.2f}", f"{summary['total_historical_periods']} Periods Observed", accent="teal")
    with k3:
        render_kpi_card("Projected Cumulative", f"${summary['projected_total']:,.2f}", f"Next {horizon} Periods", accent="green")
    with k4:
        anom_cnt = anomaly_result.get("anomaly_count", 0)
        render_kpi_card("Detected Anomalies", f"{anom_cnt}", f"{anomaly_result.get('anomaly_rate_pct', 0)}% of Series", accent="amber" if anom_cnt > 0 else "teal")

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # Tabs for Workspace
    tab_chart, tab_eval, tab_stl, tab_anom, tab_tbl = st.tabs([
        "📈 Predictive Trajectory & Bounds",
        "📊 Model Benchmarking & Validation",
        "🌊 STL Seasonality Decomposition",
        "🚨 Anomaly Detection Scanner",
        "📋 Forecast Table & CSV Export",
    ])

    with tab_chart:
        render_section_header("Predictive Trajectory with Uncertainty Bounds", subtitle="Historical observations paired with 80% and 95% expanding prediction intervals.")
        fig_fc = plot_time_series_forecast(historical_df, forecast_df, metric_name=sel_target_col)
        st.plotly_chart(fig_fc, use_container_width=True)
        st.caption("Empirical prediction intervals calibrated from sequential holdout residuals.")

    with tab_eval:
        render_section_header("Backtesting Validation Metrics", subtitle="Sequential holdout test evaluation preventing forward lookahead bias.")
        render_alert(
            "Backtesting strictly splits time series sequentially to prevent future data leakage. "
            "Evaluated with Scale-Sensitive (MAE, RMSE) and Scale-Free metrics (Safe MAPE, WAPE).",
            level="info",
            title="Validation Methodology"
        )
        all_evals = list(fc_results.get("evaluation_table", []))
        if adv_models.get("evaluations"):
            for m_name, m_metrics in adv_models["evaluations"].items():
                all_evals.append({
                    "Model": m_name,
                    "MAE": m_metrics["mae"],
                    "RMSE": m_metrics["rmse"],
                    "MAPE %": f"{m_metrics['mape_pct']}%",
                    "WAPE %": f"{m_metrics['wape_pct']}%",
                })
        st.dataframe(pd.DataFrame(all_evals), use_container_width=True, hide_index=True)

    with tab_stl:
        render_section_header("Seasonal-Trend Decomposition (STL)", subtitle="Separates observed data into trend, cyclical seasonality, and irregular noise.")
        if stl_result.get("success"):
            st.caption(f"{stl_result['interpretation']} (Method: {stl_result['method']})")
            d_df = stl_result["decomposition_df"]

            fig_stl = go.Figure()
            fig_stl.add_trace(go.Scatter(x=d_df["Date"], y=d_df["Observed"], name="Observed", line=dict(color=tokens["brand_primary"])))
            fig_stl.add_trace(go.Scatter(x=d_df["Date"], y=d_df["Trend"], name="Underlying Trend", line=dict(color=tokens["teal"], width=2.5)))
            fig_stl.add_trace(go.Scatter(x=d_df["Date"], y=d_df["Seasonal"], name="Seasonal Pattern", line=dict(color=tokens["warning"], dash="dot")))
            fig_stl.add_trace(go.Scatter(x=d_df["Date"], y=d_df["Residual"], name="Residual Noise", line=dict(color=tokens["text_muted"])))
            fig_stl.update_layout(
                height=400,
                title="Decomposed Series Components",
                margin=dict(l=10, r=10, t=35, b=10)
            )
            fig_stl = apply_theme(fig_stl, height=400)
            st.plotly_chart(fig_stl, use_container_width=True)
        else:
            st.info(stl_result.get("error", "STL decomposition not supported for current dataset."))

    with tab_anom:
        render_section_header("Time-Series Anomaly Scanner", subtitle="Automated outlier identification based on Median Absolute Deviation (MAD).")
        anomalies = anomaly_result.get("anomalies", [])
        if not anomalies:
            st.success("✅ No statistical anomalies detected above threshold (±2.5 MAD z-scores).")
        else:
            st.markdown(f"Flagged **{len(anomalies)} statistical anomalies**:")
            df_anom = pd.DataFrame(anomalies)
            st.dataframe(
                df_anom[["date", "actual_value", "baseline_value", "relative_deviation_pct", "severity", "direction", "explanation"]],
                use_container_width=True,
                hide_index=True
            )

        st.caption(f"ℹ️ *{anomaly_result.get('methodology_note')}*")

    with tab_tbl:
        render_section_header("Detailed Period Projections", subtitle="Future horizon points and prediction intervals.")
        disp_fc = forecast_df.copy()
        if not hasattr(st, "column_config") or isinstance(getattr(st, "column_config", None), type):
            for c in ["Forecast", "Lower_80", "Upper_80", "Lower_95", "Upper_95"]:
                if c in disp_fc.columns and pd.api.types.is_numeric_dtype(disp_fc[c]):
                    disp_fc[c] = disp_fc[c].apply(lambda v: f"${v:,.2f}")
        st.dataframe(
            disp_fc,
            column_config={
                "Forecast": st.column_config.NumberColumn("Point Forecast", format="$%.2f"),
                "Lower_80": st.column_config.NumberColumn("80% Lower Bound", format="$%.2f"),
                "Upper_80": st.column_config.NumberColumn("80% Upper Bound", format="$%.2f"),
                "Lower_95": st.column_config.NumberColumn("95% Lower Bound", format="$%.2f"),
                "Upper_95": st.column_config.NumberColumn("95% Upper Bound", format="$%.2f"),
            },
            use_container_width=True,
            hide_index=True,
        )

        csv_bytes = export_dataframe_to_csv_bytes(forecast_df)
        st.download_button(
            label="⬇️ Export Forecast & Confidence Intervals (CSV)",
            data=csv_bytes,
            file_name="insightiq_revenue_forecast.csv",
            mime="text/csv",
        )

    render_methodology_disclaimer()
