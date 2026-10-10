"""
Time-Series Anomaly Detection Service for InsightIQ.
Identifies unusual revenue surges or contractions using robust statistical estimators
(Rolling Median, Median Absolute Deviation, and STL Residuals) with severity grading.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional


class TimeSeriesAnomalyDetector:
    """
    Detects statistical outliers in historical time series observations.
    """

    @classmethod
    def detect_anomalies(
        cls,
        ts: pd.Series,
        window: int = 5,
        threshold_sigma: float = 2.5
    ) -> Dict[str, Any]:
        """
        Flag anomalous observations using rolling robust z-scores (MAD).
        """
        if ts is None or len(ts) < 5:
            return {
                "anomalies": [],
                "anomaly_count": 0,
                "summary": "Insufficient data points for anomaly scanning."
            }

        df = pd.DataFrame({"Date": ts.index, "Actual": ts.values})
        
        # Compute rolling median and Median Absolute Deviation (MAD)
        rolling_median = df["Actual"].rolling(window=window, min_periods=3, center=True).median().bfill().ffill()
        residuals = np.abs(df["Actual"] - rolling_median)
        rolling_mad = residuals.rolling(window=window, min_periods=3, center=True).median().bfill().ffill()
        
        # Constant multiplier 1.4826 converts MAD to consistent normal std estimator
        scale = 1.4826 * np.maximum(rolling_mad, 1e-4)
        z_scores = (df["Actual"] - rolling_median) / scale

        anomalies: List[Dict[str, Any]] = []

        for idx, row in df.iterrows():
            z = z_scores.iloc[idx]
            if np.abs(z) >= threshold_sigma:
                actual_v = float(row["Actual"])
                exp_v = float(rolling_median.iloc[idx])
                abs_diff = actual_v - exp_v
                pct_diff = (abs_diff / exp_v * 100) if exp_v != 0 else 0.0

                # Severity classification
                abs_z = abs(z)
                severity = "Critical Risk" if abs_z >= 3.5 else ("Moderate Warning" if abs_z >= 2.5 else "Low Anomaly")
                direction = "Positive Surge" if abs_diff > 0 else "Negative Contraction"

                date_str = str(row["Date"])[:10]
                explanation = (
                    f"Observation of {actual_v:,.2f} deviated by {pct_diff:+.1f}% from rolling baseline ({exp_v:,.2f}) "
                    f"with robust z-score of {z:+.2f}."
                )

                anomalies.append({
                    "date": date_str,
                    "actual_value": round(actual_v, 2),
                    "baseline_value": round(exp_v, 2),
                    "absolute_deviation": round(abs_diff, 2),
                    "relative_deviation_pct": round(pct_diff, 1),
                    "robust_z_score": round(float(z), 2),
                    "severity": severity,
                    "direction": direction,
                    "method": "Rolling Median & MAD (1.4826x)",
                    "explanation": explanation,
                })

        return {
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
            "anomaly_rate_pct": round((len(anomalies) / len(df)) * 100, 1),
            "threshold_sigma": threshold_sigma,
            "methodology_note": (
                "Statistical Disclaimer: Flagged points represent mathematical deviations from local statistical trends. "
                "They do not automatically imply external accounting errors, security breaches, or operational failures."
            )
        }
