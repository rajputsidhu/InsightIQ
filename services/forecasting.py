"""
Revenue & Metric Time-Series Forecasting Engine for InsightIQ.
Implements time-ordered backtesting, multiple baseline & statistical models,
prediction intervals, and what-if scenario simulations.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta

try:
    from statsmodels.tsa.api import ExponentialSmoothing, SimpleExpSmoothing, Holt
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False


def prepare_time_series(
    df: pd.DataFrame,
    date_col: str,
    target_col: str,
    freq: str = "ME"
) -> Tuple[Optional[pd.Series], Optional[str]]:
    """
    Clean, parse dates, sort chronologically, and resample to specified frequency.
    """
    if df is None or df.empty:
        return None, "Dataset is empty."

    if date_col not in df.columns or target_col not in df.columns:
        return None, f"Required columns '{date_col}' or '{target_col}' not found."

    temp_df = df[[date_col, target_col]].copy()
    temp_df["dt"] = pd.to_datetime(temp_df[date_col], errors="coerce")
    temp_df[target_col] = pd.to_numeric(temp_df[target_col], errors="coerce")
    temp_df = temp_df.dropna(subset=["dt", target_col])

    if len(temp_df) < 5:
        return None, "Insufficient data points for time-series forecasting (minimum 5 required)."

    if freq == "D":
        temp_df["period_dt"] = pd.to_datetime(temp_df["dt"].dt.strftime("%Y-%m-%d"))
    elif freq == "W":
        temp_df["period_dt"] = temp_df["dt"].dt.to_period("W").dt.start_time
    else:
        temp_df["period_dt"] = pd.to_datetime(temp_df["dt"].dt.strftime("%Y-%m") + "-01")

    grouped = temp_df.groupby("period_dt")[target_col].sum().sort_index()
    ts_resampled = grouped.fillna(0.0)

    if len(ts_resampled) < 4:
        return None, f"Aggregated series resulted in only {len(ts_resampled)} periods. Please choose a finer frequency."

    return ts_resampled, None


def calculate_ts_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate MAE, RMSE, MAPE (safe), and WAPE."""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    # WAPE: sum(|y - y_hat|) / sum(y)
    sum_true = float(np.sum(np.abs(y_true)))
    wape = (float(np.sum(np.abs(y_true - y_pred))) / sum_true * 100) if sum_true > 0 else 0.0

    # Safe MAPE: only on non-zero true values
    non_zero_mask = y_true != 0
    if np.any(non_zero_mask):
        mape = float(np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100)
    else:
        mape = 0.0

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape_pct": round(mape, 2),
        "wape_pct": round(wape, 2),
    }


def run_forecasting_pipeline(
    ts: pd.Series,
    horizon: int = 6,
    test_periods: int = 3,
    scenario_multiplier: float = 1.0
) -> Dict[str, Any]:
    """
    Execute time-series models with backtesting validation and generate future forecasts.
    """
    n = len(ts)
    if n <= test_periods + 2:
        test_periods = max(1, n // 3)

    train_ts = ts.iloc[:-test_periods]
    test_ts = ts.iloc[-test_periods:]

    models_eval = {}

    # 1. Naive Model (Last value)
    last_val = float(train_ts.iloc[-1])
    naive_test_pred = np.repeat(last_val, len(test_ts))
    models_eval["Naive Baseline"] = calculate_ts_metrics(test_ts.values, naive_test_pred)

    # 2. Moving Average (3 periods)
    window = min(3, len(train_ts))
    ma_val = float(train_ts.iloc[-window:].mean())
    ma_test_pred = np.repeat(ma_val, len(test_ts))
    models_eval["Moving Average"] = calculate_ts_metrics(test_ts.values, ma_test_pred)

    # 3. Exponential Smoothing (Holt linear trend or SES)
    exp_test_pred = None
    best_fitted_model = None
    if HAS_STATSMODELS and len(train_ts) >= 4:
        try:
            exp_model = Holt(train_ts.values, initialization_method="estimated").fit()
            exp_test_pred = exp_model.forecast(len(test_ts))
            models_eval["Holt Exponential Smoothing"] = calculate_ts_metrics(test_ts.values, exp_test_pred)
            best_fitted_model = "Holt Exponential Smoothing"
        except Exception:
            try:
                ses_model = SimpleExpSmoothing(train_ts.values).fit()
                exp_test_pred = ses_model.forecast(len(test_ts))
                models_eval["Simple Exp Smoothing"] = calculate_ts_metrics(test_ts.values, exp_test_pred)
                best_fitted_model = "Simple Exp Smoothing"
            except Exception:
                pass

    # Pick best model based on lowest RMSE on validation set
    best_model_name = "Naive Baseline"
    best_rmse = float("inf")
    for name, m in models_eval.items():
        if m["rmse"] < best_rmse:
            best_rmse = m["rmse"]
            best_model_name = name

    # Generate Future Forecasts on Full Series
    future_dates = pd.date_range(start=ts.index[-1], periods=horizon + 1, freq=ts.index.freq or "MS")[1:]
    
    full_values = ts.values
    residuals = []

    if best_model_name == "Holt Exponential Smoothing" and HAS_STATSMODELS:
        try:
            full_model = Holt(full_values, initialization_method="estimated").fit()
            future_point_pred = full_model.forecast(horizon)
            residuals = full_values - full_model.fittedvalues
        except Exception:
            future_point_pred = np.repeat(full_values[-1], horizon)
    elif best_model_name == "Moving Average":
        window = min(3, len(full_values))
        base_val = full_values[-window:].mean()
        future_point_pred = np.repeat(base_val, horizon)
        rolling_means = pd.Series(full_values).rolling(window).mean()
        residuals = (pd.Series(full_values) - rolling_means).dropna().values
    elif best_model_name == "Simple Exp Smoothing" and HAS_STATSMODELS:
        try:
            full_model = SimpleExpSmoothing(full_values).fit()
            future_point_pred = full_model.forecast(horizon)
            residuals = full_values - full_model.fittedvalues
        except Exception:
            future_point_pred = np.repeat(full_values[-1], horizon)
            residuals = np.diff(full_values)
    else:
        base_val = full_values[-1]
        future_point_pred = np.repeat(base_val, horizon)
        residuals = np.diff(full_values)

    # Apply Scenario Multiplier if adjusted
    point_forecast = future_point_pred * scenario_multiplier

    # Compute Prediction Intervals (80% and 95%)
    res_std = float(np.std(residuals)) if len(residuals) > 0 else (float(np.mean(full_values)) * 0.1)
    
    # Uncertainty expands with horizon sqrt(h)
    h_steps = np.sqrt(np.arange(1, horizon + 1))
    lower_80 = np.maximum(0, point_forecast - 1.28 * res_std * h_steps)
    upper_80 = point_forecast + 1.28 * res_std * h_steps
    lower_95 = np.maximum(0, point_forecast - 1.96 * res_std * h_steps)
    upper_95 = point_forecast + 1.96 * res_std * h_steps

    forecast_df = pd.DataFrame({
        "Date": future_dates.strftime("%Y-%m-%d"),
        "Forecast": np.round(point_forecast, 2),
        "Lower_80": np.round(lower_80, 2),
        "Upper_80": np.round(upper_80, 2),
        "Lower_95": np.round(lower_95, 2),
        "Upper_95": np.round(upper_95, 2),
    })

    historical_df = pd.DataFrame({
        "Date": ts.index.strftime("%Y-%m-%d"),
        "Actual": np.round(ts.values, 2),
    })

    comparison_rows = []
    for m_name, met in models_eval.items():
        comparison_rows.append({
            "Model": m_name,
            "MAE": f"${met['mae']:,.2f}",
            "RMSE": f"${met['rmse']:,.2f}",
            "MAPE (%)": f"{met['mape_pct']:.1f}%",
            "WAPE (%)": f"{met['wape_pct']:.1f}%",
            "Selected": "★ Best Fit" if m_name == best_model_name else "",
        })

    return {
        "best_model": best_model_name,
        "evaluation_table": pd.DataFrame(comparison_rows),
        "historical_df": historical_df,
        "forecast_df": forecast_df,
        "summary": {
            "total_historical_periods": len(ts),
            "forecast_horizon": horizon,
            "validation_periods": test_periods,
            "projected_total": float(np.round(np.sum(point_forecast), 2)),
            "historical_mean": float(np.round(np.mean(full_values), 2)),
        }
    }
