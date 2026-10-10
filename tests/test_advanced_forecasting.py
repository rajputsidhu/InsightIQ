"""
Unit tests for Advanced Forecasting Service (Workstream 3).
"""

import pytest
import pandas as pd
import numpy as np
from services.advanced_forecasting import AdvancedForecastingService


@pytest.fixture
def synthetic_monthly_series():
    dates = pd.date_range(start="2022-01-01", periods=24, freq="MS")
    trend = np.linspace(100, 300, 24)
    seasonal = 30 * np.sin(2 * np.pi * np.arange(24) / 12)
    noise = np.random.normal(0, 5, 24)
    values = trend + seasonal + noise
    return pd.Series(values, index=dates)


def test_stl_decomposition(synthetic_monthly_series):
    res = AdvancedForecastingService.perform_stl_decomposition(synthetic_monthly_series, period=12)
    assert res["success"] is True
    assert "decomposition_df" in res
    d_df = res["decomposition_df"]
    assert "Trend" in d_df.columns
    assert "Seasonal" in d_df.columns
    assert "Residual" in d_df.columns
    assert len(d_df) == 24
    assert 0.0 <= res["seasonal_strength"] <= 1.0


def test_evaluate_extended_models(synthetic_monthly_series):
    res = AdvancedForecastingService.evaluate_extended_models(synthetic_monthly_series, horizon=4, test_periods=3, seasonal_period=12)
    assert "evaluations" in res
    assert "forecasts" in res
    assert "Seasonal Naive" in res["evaluations"]
    assert len(res["forecasts"]["Seasonal Naive"]) == 4
