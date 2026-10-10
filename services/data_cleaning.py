"""
Data Cleaning & Transformation Service for InsightIQ.
Provides audit-trailed data cleansing without mutating the raw source dataset.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional


class DataCleaningService:
    def __init__(self, raw_df: pd.DataFrame):
        self.raw_df = raw_df.copy()
        self.clean_df = raw_df.copy()
        self.audit_trail: List[Dict[str, Any]] = []

    def remove_duplicates(self, subset_cols: Optional[List[str]] = None) -> Tuple[int, "DataCleaningService"]:
        """Remove duplicate records and record in audit trail."""
        before_count = len(self.clean_df)
        self.clean_df = self.clean_df.drop_duplicates(subset=subset_cols).reset_index(drop=True)
        after_count = len(self.clean_df)
        removed = before_count - after_count

        self.audit_trail.append({
            "operation": "Deduplication",
            "columns": subset_cols or "All columns",
            "affected_records": removed,
            "details": f"Removed {removed} duplicate rows ({before_count} -> {after_count})",
        })
        return removed, self

    def fill_numeric_missing(self, col: str, strategy: str = "median", custom_val: Optional[float] = None) -> Tuple[int, "DataCleaningService"]:
        """Impute missing values in a numeric column."""
        if col not in self.clean_df.columns:
            return 0, self

        null_count = int(self.clean_df[col].isnull().sum())
        if null_count == 0:
            return 0, self

        fill_val = None
        if strategy == "median":
            fill_val = self.clean_df[col].median()
        elif strategy == "mean":
            fill_val = self.clean_df[col].mean()
        elif strategy == "zero":
            fill_val = 0.0
        elif strategy == "custom" and custom_val is not None:
            fill_val = custom_val
        else:
            fill_val = self.clean_df[col].median()

        self.clean_df[col] = self.clean_df[col].fillna(fill_val)

        fill_val_str = f"{fill_val:.2f}" if isinstance(fill_val, (int, float, np.floating)) else str(fill_val)
        self.audit_trail.append({
            "operation": "Numeric Imputation",
            "columns": col,
            "affected_records": null_count,
            "details": f"Imputed {null_count} missing values in '{col}' using {strategy} (value: {fill_val_str})",
        })
        return null_count, self

    def fill_categorical_missing(self, col: str, strategy: str = "constant", custom_val: str = "Unknown") -> Tuple[int, "DataCleaningService"]:
        """Impute missing values in a categorical column."""
        if col not in self.clean_df.columns:
            return 0, self

        null_count = int(self.clean_df[col].isnull().sum())
        if null_count == 0:
            return 0, self

        if strategy == "mode":
            mode_series = self.clean_df[col].mode()
            fill_val = mode_series[0] if not mode_series.empty else custom_val
        elif strategy == "ffill":
            self.clean_df[col] = self.clean_df[col].ffill().bfill()
            fill_val = "Forward/Backward Fill"
        else:
            fill_val = custom_val
            self.clean_df[col] = self.clean_df[col].fillna(fill_val)

        if strategy != "ffill":
            self.clean_df[col] = self.clean_df[col].fillna(fill_val)

        self.audit_trail.append({
            "operation": "Categorical Imputation",
            "columns": col,
            "affected_records": null_count,
            "details": f"Imputed {null_count} missing values in '{col}' with strategy '{strategy}' (value: '{fill_val}')",
        })
        return null_count, self

    def convert_column_type(self, col: str, target_type: str) -> Tuple[bool, "DataCleaningService"]:
        """Cast column to specified data type safely."""
        if col not in self.clean_df.columns:
            return False, self

        orig_dtype = str(self.clean_df[col].dtype)
        try:
            if target_type == "datetime":
                self.clean_df[col] = pd.to_datetime(self.clean_df[col], errors="coerce")
            elif target_type == "numeric":
                if self.clean_df[col].dtype == object or str(self.clean_df[col].dtype) == "string":
                    # Remove common currency symbols and commas
                    cleaned_series = self.clean_df[col].astype(str).str.replace(r"[\$,€,£,]", "", regex=True).str.strip()
                    self.clean_df[col] = pd.to_numeric(cleaned_series, errors="coerce")
                else:
                    self.clean_df[col] = pd.to_numeric(self.clean_df[col], errors="coerce")
            elif target_type == "string":
                self.clean_df[col] = self.clean_df[col].astype(str)
            elif target_type == "category":
                self.clean_df[col] = self.clean_df[col].astype("category")

            self.audit_trail.append({
                "operation": "Type Conversion",
                "columns": col,
                "affected_records": len(self.clean_df),
                "details": f"Converted column '{col}' from {orig_dtype} to {target_type}",
            })
            return True, self
        except Exception as e:
            self.audit_trail.append({
                "operation": "Type Conversion Failed",
                "columns": col,
                "affected_records": 0,
                "details": f"Failed conversion on '{col}': {str(e)}",
            })
            return False, self

    def cap_outliers_iqr(self, col: str, factor: float = 1.5) -> Tuple[int, "DataCleaningService"]:
        """Cap extreme statistical outliers to IQR threshold boundaries (Winsorization)."""
        if col not in self.clean_df.columns or not np.issubdtype(self.clean_df[col].dtype, np.number):
            return 0, self

        series = self.clean_df[col].dropna()
        if len(series) < 5:
            return 0, self

        q25 = series.quantile(0.25)
        q75 = series.quantile(0.75)
        iqr = q75 - q25
        lower = q25 - factor * iqr
        upper = q75 + factor * iqr

        outliers_count = int(((self.clean_df[col] < lower) | (self.clean_df[col] > upper)).sum())
        if outliers_count > 0:
            self.clean_df[col] = self.clean_df[col].clip(lower=lower, upper=upper)
            self.audit_trail.append({
                "operation": "Outlier Capping (Winsorization)",
                "columns": col,
                "affected_records": outliers_count,
                "details": f"Capped {outliers_count} outliers in '{col}' to range [{lower:.2f}, {upper:.2f}]",
            })

        return outliers_count, self

    def drop_column(self, col: str) -> Tuple[bool, "DataCleaningService"]:
        """Drop a selected column."""
        if col in self.clean_df.columns:
            self.clean_df = self.clean_df.drop(columns=[col])
            self.audit_trail.append({
                "operation": "Drop Column",
                "columns": col,
                "affected_records": len(self.clean_df),
                "details": f"Dropped column '{col}' from active workspace",
            })
            return True, self
        return False, self

    def get_summary(self) -> Dict[str, Any]:
        """Return cleaning summary comparison between raw and clean data."""
        return {
            "initial_rows": len(self.raw_df),
            "final_rows": len(self.clean_df),
            "initial_cols": len(self.raw_df.columns),
            "final_cols": len(self.clean_df.columns),
            "initial_missing": int(self.raw_df.isnull().sum().sum()),
            "final_missing": int(self.clean_df.isnull().sum().sum()),
            "operations_count": len(self.audit_trail),
            "audit_trail": self.audit_trail,
        }
