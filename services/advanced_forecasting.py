"""
Advanced Time-Series Forecasting & Seasonality Engine for InsightIQ.
Implements STL seasonal-trend decomposition, Seasonal Naive, Holt-Winters
multiplicative/additive models, and chronologically backtested evaluations.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

try:
    from statsmodels.tsa.seasonal import STL, seasonal_decompose
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from statsmodels.tsa.arima.model import ARIMA
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

from services.forecasting import calculate_ts_metrics


class AdvancedForecastingService:
    """
    Extends forecasting capabilities with STL decomposition and seasonal model benchmarking.
    """

    @classmethod
    def perform_stl_decomposition(
        cls,
        ts: pd.Series,
        period: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Decomposes series into Observed, Trend, Seasonal, and Residual components.
        """
        if not HAS_STATSMODELS or len(ts) < 8:
            return {
                "success": False,
                "error": "Decomposition requires at least 8 observations and statsmodels library."
            }

        n = len(ts)
        # Determine seasonal period if not provided
        if period is None:
            period = 12 if n >= 24 else (4 if n >= 8 else 2)

        # Check if length >= 2 * period
        if n < 2 * period:
            period = max(2, n // 2)

        try:
            # Try STL first
            stl = STL(ts, period=period, robust=True)
            res = stl.fit()
            decomp_df = pd.DataFrame({
                "Date": ts.index,
                "Observed": ts.values,
                "Trend": res.trend,
                "Seasonal": res.seasonal,
                "Residual": res.resid
            })
            method = "Robust STL (LOESS)"
        except Exception:
            try:
                # Fallback to classical seasonal decomposition
                res = seasonal_decompose(ts, model="additive", period=period, extrapolate_trend="freq")
                decomp_df = pd.DataFrame({
                    "Date": ts.index,
                    "Observed": ts.values,
                    "Trend": res.trend,
                    "Seasonal": res.seasonal,
                    "Residual": res.resid
                })
                method = "Classical Additive Decomposition"
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Decomposition failed for current series length ({n} points): {str(e)}"
                }

        # Calculate seasonal strength: 1 - Var(Residual) / Var(Seasonal + Residual)
        var_resid = np.var(decomp_df["Residual"].dropna())
        var_sr = np.var((decomp_df["Seasonal"] + decomp_df["Residual"]).dropna())
        seasonal_strength = max(0.0, min(1.0, 1.0 - (var_resid / max(1e-6, var_sr))))

        return {
            "success": True,
            "decomposition_df": decomp_df,
            "period": period,
            "method": method,
            "seasonal_strength": round(float(seasonal_strength), 3),
            "interpretation": (
                f"Series decomposed into Trend and Seasonality with period={period}. "
                f"Seasonal pattern strength is estimated at {seasonal_strength*100:.1f}%."
            )
        }

    @classmethod
    def evaluate_extended_models(
        cls,
        ts: pd.Series,
        horizon: int = 6,
        test_periods: int = 3,
        seasonal_period: int = 12
    ) -> Dict[str, Any]:
        """
        Evaluate seasonal models on chronological holdout and forecast future periods.
        """
        n = len(ts)
        if n <= test_periods + 2:
            test_periods = max(1, n // 3)

        train_ts = ts.iloc[:-test_periods]
        test_ts = ts.iloc[-test_periods:]

        evaluations = {}
        forecasts = {}

        # 1. Seasonal Naive Model (if train length >= seasonal_period)
        if len(train_ts) >= seasonal_period:
            s_val = train_ts.iloc[-seasonal_period:].values
            repeats = int(np.ceil(len(test_ts) / seasonal_period))
            s_naive_test = np.tile(s_val, repeats)[:len(test_ts)]
            evaluations["Seasonal Naive"] = calculate_ts_metrics(test_ts.values, s_naive_test)

            future_repeats = int(np.ceil(horizon / seasonal_period))
            forecasts["Seasonal Naive"] = np.tile(ts.iloc[-seasonal_period:].values, future_repeats)[:horizon]

        # 2. Holt-Winters Seasonal Exponential Smoothing
        if HAS_STATSMODELS and len(train_ts) >= 2 * seasonal_period:
            try:
                hw_model = ExponentialSmoothing(
                    train_ts.values,
                    trend="add",
                    seasonal="add",
                    seasonal_periods=seasonal_period,
                    initialization_method="estimated"
                ).fit()
                hw_test_pred = hw_model.forecast(len(test_ts))
                evaluations["Holt-Winters Seasonal"] = calculate_ts_metrics(test_ts.values, hw_test_pred)

                # Full fit for future forecast
                hw_full = ExponentialSmoothing(
                    ts.values,
                    trend="add",
                    seasonal="add",
                    seasonal_periods=seasonal_period,
                    initialization_method="estimated"
                ).fit()
                forecasts["Holt-Winters Seasonal"] = hw_full.forecast(horizon)
            except Exception:
                pass

        # 3. Autoregressive ARIMA(1, 1, 1) where series allows
        if HAS_STATSMODELS and len(train_ts) >= 10:
            try:
                arima_model = ARIMA(train_ts.values, order=(1, 1, 0)).fit()
                arima_test_pred = arima_model.forecast(len(test_ts))
                evaluations["ARIMA(1,1,0)"] = calculate_ts_metrics(test_ts.values, arima_test_pred)

                arima_full = ARIMA(ts.values, order=(1, 1, 0)).fit()
                forecasts["ARIMA(1,1,0)"] = arima_full.forecast(horizon)
            except Exception:
                pass

        return {
            "evaluations": evaluations,
            "forecasts": forecasts,
            "test_periods": test_periods
        }
