"""
Data Quality & Validation Service for InsightIQ.
Performs data integrity checks, statistical anomaly detection, outlier scanning, and health scoring.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


def compute_data_quality_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run full suite of data quality checks and return comprehensive diagnostics.
    """
    if df is None or df.empty:
        return {
            "overall_score": 0,
            "grade": "F",
            "total_rows": 0,
            "total_cols": 0,
            "duplicate_rows": 0,
            "duplicate_pct": 0.0,
            "missing_cells": 0,
            "missing_pct": 0.0,
            "columns_with_missing": 0,
            "outlier_summary": {},
            "column_metrics": [],
            "issues": ["Dataset is empty or not loaded."],
            "recommendations": ["Upload a valid non-empty dataset."],
        }

    total_rows = len(df)
    total_cols = len(df.columns)
    total_cells = total_rows * total_cols

    # 1. Duplicates
    dup_rows = int(df.duplicated().sum())
    dup_pct = round((dup_rows / total_rows) * 100, 2) if total_rows > 0 else 0.0

    # 2. Missingness
    missing_by_col = df.isnull().sum()
    missing_cells = int(missing_by_col.sum())
    missing_pct = round((missing_cells / total_cells) * 100, 2) if total_cells > 0 else 0.0
    cols_with_missing = int((missing_by_col > 0).sum())

    # 3. Numeric Outliers & Inconsistencies
    outlier_summary = {}
    issues = []
    recommendations = []
    column_metrics = []

    if dup_rows > 0:
        issues.append(f"Detected {dup_rows:,} duplicate rows ({dup_pct}% of total records).")
        recommendations.append("Apply deduplication to avoid double-counting transactions or metrics.")

    if missing_pct > 15:
        issues.append(f"High overall missingness: {missing_pct}% of all data points are null.")
        recommendations.append("Review data extraction pipelines or perform imputation on key analytical columns.")
    elif missing_pct > 0:
        issues.append(f"Found {missing_cells:,} missing values across {cols_with_missing} columns.")
        recommendations.append("Impute missing numeric values with median/mean or fill categories with 'Unknown'.")

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    for col in df.columns:
        col_nulls = int(missing_by_col[col])
        col_null_pct = round((col_nulls / total_rows) * 100, 2) if total_rows > 0 else 0.0
        n_unique = int(df[col].nunique())
        dtype_str = str(df[col].dtype)

        # Check for constant column
        is_constant = (n_unique <= 1 and total_rows > 1)
        if is_constant:
            issues.append(f"Column '{col}' has zero variance (constant value throughout).")
            recommendations.append(f"Consider dropping constant column '{col}' before statistical modeling.")

        outliers_iqr = 0
        min_val = None
        max_val = None
        mean_val = None
        std_val = None

        if col in numeric_cols:
            valid_series = df[col].dropna()
            if len(valid_series) > 4:
                q25 = valid_series.quantile(0.25)
                q75 = valid_series.quantile(0.75)
                iqr = q75 - q25
                lower_bound = q25 - 1.5 * iqr
                upper_bound = q75 + 1.5 * iqr

                outliers = valid_series[(valid_series < lower_bound) | (valid_series > upper_bound)]
                outliers_iqr = int(len(outliers))

                min_val = round(float(valid_series.min()), 2)
                max_val = round(float(valid_series.max()), 2)
                mean_val = round(float(valid_series.mean()), 2)
                std_val = round(float(valid_series.std()), 2)

                if outliers_iqr > 0:
                    outlier_summary[col] = {
                        "count": outliers_iqr,
                        "pct": round((outliers_iqr / total_rows) * 100, 2),
                        "lower_bound": round(float(lower_bound), 2),
                        "upper_bound": round(float(upper_bound), 2),
                    }
                    if (outliers_iqr / total_rows) > 0.05:
                        issues.append(f"Column '{col}' contains {outliers_iqr} statistical outliers (>5% of rows).")

        column_metrics.append({
            "column": col,
            "dtype": dtype_str,
            "null_count": col_nulls,
            "null_pct": col_null_pct,
            "unique_count": n_unique,
            "outliers_iqr": outliers_iqr,
            "min": min_val,
            "max": max_val,
            "mean": mean_val,
            "std": std_val,
            "is_constant": is_constant,
        })

    # Overall Quality Score Calculation (0 - 100)
    # Deductions based on missingness, duplicates, constant columns, severe outliers
    score = 100.0
    score -= min(35.0, missing_pct * 1.5)
    score -= min(25.0, dup_pct * 2.0)
    
    constant_col_count = sum(1 for c in column_metrics if c["is_constant"])
    score -= min(15.0, constant_col_count * 5.0)

    score = max(5.0, min(100.0, round(score, 1)))

    if score >= 90:
        grade = "A (Excellent)"
    elif score >= 80:
        grade = "B (Good)"
    elif score >= 70:
        grade = "C (Fair)"
    elif score >= 55:
        grade = "D (Needs Attention)"
    else:
        grade = "F (Poor Quality)"

    if not issues:
        issues.append("No critical data anomalies detected.")
    if not recommendations:
        recommendations.append("Dataset is clean and ready for analytics & modeling workflows.")

    return {
        "overall_score": score,
        "grade": grade,
        "total_rows": total_rows,
        "total_cols": total_cols,
        "duplicate_rows": dup_rows,
        "duplicate_pct": dup_pct,
        "missing_cells": missing_cells,
        "missing_pct": missing_pct,
        "columns_with_missing": cols_with_missing,
        "outlier_summary": outlier_summary,
        "column_metrics": column_metrics,
        "issues": issues,
        "recommendations": recommendations,
    }
