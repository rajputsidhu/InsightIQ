"""
Unit tests for Time-Series Revenue Forecasting Engine.
"""

import pandas as pd
import numpy as np
import pytest
from services.forecasting import prepare_time_series, run_forecasting_pipeline, calculate_ts_metrics


def test_calculate_ts_metrics():
    y_true = np.array([100.0, 110.0, 120.0])
    y_pred = np.array([105.0, 108.0, 125.0])
    metrics = calculate_ts_metrics(y_true, y_pred)
    assert metrics["mae"] == 4.0
    assert metrics["rmse"] > 0
    assert metrics["wape_pct"] > 0
    assert metrics["mape_pct"] > 0


def test_prepare_time_series():
    dates = pd.date_range("2023-01-01", periods=12, freq="MS")
    df = pd.DataFrame({
        "order_date": dates.strftime("%Y-%m-%d"),
        "revenue": [1000.0 * (1 + i * 0.05) for i in range(12)],
    })
    ts, err = prepare_time_series(df, date_col="order_date", target_col="revenue", freq="MS")
    assert err is None
    assert len(ts) == 12


def test_run_forecasting_pipeline():
    dates = pd.date_range("2022-01-01", periods=24, freq="MS")
    ts = pd.Series([5000.0 * (1.02 ** i) + np.sin(i) * 100 for i in range(24)], index=dates)

    results = run_forecasting_pipeline(ts, horizon=6, test_periods=4)
    assert results["best_model"] is not None
    assert len(results["forecast_df"]) == 6
    assert "Forecast" in results["forecast_df"].columns
    assert "Lower_95" in results["forecast_df"].columns
    assert "Upper_95" in results["forecast_df"].columns
    assert len(results["evaluation_table"]) >= 2
