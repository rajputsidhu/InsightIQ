"""
Unit tests for Data Validation and Quality Auditing Service.
"""

import pandas as pd
import numpy as np
import pytest
from services.data_validation import compute_data_quality_report


def test_empty_dataset_quality_report():
    df = pd.DataFrame()
    report = compute_data_quality_report(df)
    assert report["overall_score"] == 0
    assert report["grade"] == "F"
    assert report["total_rows"] == 0


def test_clean_dataset_quality_score():
    df = pd.DataFrame({
        "order_id": [1, 2, 3, 4, 5],
        "customer_id": ["A", "B", "C", "D", "E"],
        "amount": [10.0, 20.0, 30.0, 40.0, 50.0],
    })
    report = compute_data_quality_report(df)
    assert report["overall_score"] >= 90
    assert report["grade"].startswith("A")
    assert report["duplicate_rows"] == 0
    assert report["missing_cells"] == 0


def test_dataset_with_missing_and_duplicates():
    df = pd.DataFrame({
        "a": [1, 2, 2, np.nan, 5],
        "b": ["x", "y", "y", "z", "w"],
    })
    report = compute_data_quality_report(df)
    assert report["duplicate_rows"] == 1
    assert report["missing_cells"] == 1
    assert report["overall_score"] < 100


def test_outlier_detection_iqr():
    # Construct series with clear outliers
    normal_data = [10.0, 11.0, 10.5, 12.0, 9.8, 10.2, 11.5, 10.8, 12.2, 10.0]
    outliers = [100.0, -50.0]
    df = pd.DataFrame({"val": normal_data + outliers})
    report = compute_data_quality_report(df)
    assert "val" in report["outlier_summary"]
    assert report["outlier_summary"]["val"]["count"] >= 1
