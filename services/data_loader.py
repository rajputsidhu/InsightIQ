"""
Data Loading & Ingestion Service for InsightIQ.
Safely handles file reading, encoding detection, size limits, and schema profiling.
"""

import io
import os
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_DATA_DIR = os.path.join(BASE_DIR, "sample_data")
MAX_FILE_SIZE_MB = 50


def get_demo_dataset(name: str = "ecommerce") -> pd.DataFrame:
    """Load one of the bundled demo datasets."""
    files = {
        "ecommerce": "sample_ecommerce_orders.csv",
        "churn": "sample_telecom_churn.csv",
        "saas": "sample_saas_metrics.csv",
    }
    filename = files.get(name.lower(), "sample_ecommerce_orders.csv")
    filepath = os.path.join(SAMPLE_DATA_DIR, filename)

    if not os.path.exists(filepath):
        # Auto-generate if missing
        from sample_data.generate_demo_data import (
            generate_ecommerce_data,
            generate_churn_data,
            generate_saas_metrics,
        )
        if name == "churn":
            df = generate_churn_data()
        elif name == "saas":
            df = generate_saas_metrics()
        else:
            df = generate_ecommerce_data()
        df.to_csv(filepath, index=False)
        return df

    return pd.read_csv(filepath)


def load_dataset_from_bytes(file_bytes: bytes, filename: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Safely load a dataset from raw bytes, supporting CSV and Excel files.
    Returns (DataFrame, error_message).
    """
    file_size_mb = len(file_bytes) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        return None, f"File size ({file_size_mb:.1f} MB) exceeds maximum allowed limit of {MAX_FILE_SIZE_MB} MB."

    if len(file_bytes) == 0:
        return None, "The uploaded file is empty."

    filename_lower = filename.lower()
    
    if filename_lower.endswith(".csv") or filename_lower.endswith(".txt"):
        encodings = ["utf-8", "latin1", "iso-8859-1", "cp1252"]
        separators = [",", ";", "\t", "|"]
        
        last_error = None
        for enc in encodings:
            for sep in separators:
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes), encoding=enc, sep=sep, engine="python")
                    if df is not None and df.shape[1] > 1:
                        # Clean column whitespace
                        df.columns = [str(c).strip() for c in df.columns]
                        return df, None
                except Exception as e:
                    last_error = e
                    continue

        # Single column fallback check
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")
            df.columns = [str(c).strip() for c in df.columns]
            return df, None
        except Exception as e:
            return None, f"Failed to parse CSV file: {str(e or last_error)}"

    elif filename_lower.endswith((".xlsx", ".xls")):
        try:
            df = pd.read_excel(io.BytesIO(file_bytes))
            df.columns = [str(c).strip() for c in df.columns]
            return df, None
        except Exception as e:
            return None, f"Failed to parse Excel file: {str(e)}"
    else:
        return None, "Unsupported file format. Please upload a CSV (.csv) or Excel (.xlsx, .xls) file."


def profile_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate high-level profiling metadata for a DataFrame."""
    if df is None or df.empty:
        return {
            "row_count": 0,
            "col_count": 0,
            "memory_mb": 0.0,
            "duplicate_count": 0,
            "missing_total": 0,
            "columns": [],
            "date_columns": [],
            "numeric_columns": [],
            "categorical_columns": [],
        }

    row_count = len(df)
    col_count = len(df.columns)
    memory_mb = round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
    duplicate_count = int(df.duplicated().sum())
    missing_total = int(df.isnull().sum().sum())
    missing_pct = round((missing_total / (row_count * col_count)) * 100, 2) if (row_count * col_count) > 0 else 0.0

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Detect potential date columns
    date_cols = []
    for col in df.columns:
        if np.issubdtype(df[col].dtype, np.datetime64):
            date_cols.append(col)
        elif df[col].dtype == object or str(df[col].dtype) == "string":
            sample = df[col].dropna().astype(str).head(20)
            if not sample.empty:
                # Test if sample can be parsed as dates
                try:
                    parsed = pd.to_datetime(sample, errors="coerce")
                    if parsed.notnull().mean() > 0.8:
                        date_cols.append(col)
                except Exception:
                    pass

    categorical_cols = [c for c in df.columns if c not in numeric_cols and c not in date_cols]

    col_details = []
    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        null_pct = round((null_count / row_count) * 100, 2) if row_count > 0 else 0.0
        n_unique = int(df[col].nunique())
        dtype_str = str(df[col].dtype)
        
        col_type = "Numeric" if col in numeric_cols else ("Datetime" if col in date_cols else "Categorical")
        
        col_details.append({
            "name": col,
            "type": col_type,
            "dtype": dtype_str,
            "null_count": null_count,
            "null_pct": null_pct,
            "unique_count": n_unique,
            "sample": df[col].dropna().head(3).tolist(),
        })

    return {
        "row_count": row_count,
        "col_count": col_count,
        "memory_mb": memory_mb,
        "duplicate_count": duplicate_count,
        "missing_total": missing_total,
        "missing_pct": missing_pct,
        "numeric_columns": numeric_cols,
        "date_columns": date_cols,
        "categorical_columns": categorical_cols,
        "column_details": col_details,
    }
