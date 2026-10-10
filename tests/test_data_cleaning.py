"""
Unit tests for Data Cleaning & Transformation Service.
"""

import pandas as pd
import numpy as np
import pytest
from services.data_cleaning import DataCleaningService


def test_deduplication():
    df = pd.DataFrame({
        "id": [1, 1, 2, 3],
        "name": ["A", "A", "B", "C"],
    })
    cleaner = DataCleaningService(df)
    removed, _ = cleaner.remove_duplicates()
    assert removed == 1
    assert len(cleaner.clean_df) == 3
    assert len(cleaner.audit_trail) == 1
    assert len(cleaner.raw_df) == 4  # Raw remains unmutated


def test_numeric_imputation():
    df = pd.DataFrame({
        "vals": [10.0, 20.0, np.nan, 40.0],
    })
    cleaner = DataCleaningService(df)
    imputed, _ = cleaner.fill_numeric_missing("vals", strategy="median")
    assert imputed == 1
    assert cleaner.clean_df["vals"].isnull().sum() == 0
    assert cleaner.clean_df["vals"].iloc[2] == 20.0  # Median of 10, 20, 40 is 20


def test_categorical_imputation():
    df = pd.DataFrame({
        "cat": ["A", "B", None, "A"],
    })
    cleaner = DataCleaningService(df)
    imputed, _ = cleaner.fill_categorical_missing("cat", strategy="constant", custom_val="Unknown")
    assert imputed == 1
    assert cleaner.clean_df["cat"].iloc[2] == "Unknown"


def test_outlier_capping():
    df = pd.DataFrame({
        "vals": [10, 12, 11, 13, 10, 11, 12, 100],  # 100 is high outlier
    })
    cleaner = DataCleaningService(df)
    capped, _ = cleaner.cap_outliers_iqr("vals", factor=1.5)
    assert capped == 1
    assert cleaner.clean_df["vals"].max() < 100
