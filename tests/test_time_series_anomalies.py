"""
Unit tests for Time-Series Anomaly Detector (Workstream 3).
"""

import pytest
import pandas as pd
import numpy as np
from services.time_series_anomalies import TimeSeriesAnomalyDetector


@pytest.fixture
def series_with_spike():
    dates = pd.date_range(start="2023-01-01", periods=15, freq="MS")
    vals = np.repeat(100.0, 15)
    # Inject noticeable anomaly at index 7
    vals[7] = 500.0
    return pd.Series(vals, index=dates)


def test_detect_anomalies(series_with_spike):
    res = TimeSeriesAnomalyDetector.detect_anomalies(series_with_spike, threshold_sigma=2.5)

    assert res["anomaly_count"] >= 1
    anom = res["anomalies"][0]
    assert anom["actual_value"] == 500.0
    assert anom["relative_deviation_pct"] > 0
    assert "methodology_note" in res
    assert "method" in anom
