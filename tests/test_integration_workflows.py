"""
Comprehensive Integration Tests for InsightIQ End-to-End Workflows (Workstream 6).
Verifies complete data pipelines across ingestion, cleaning, ML modeling,
explainability, forecasting, conversational copilot, and executive reporting.
"""

import pytest
import pandas as pd
import numpy as np

from services.data_loader import get_demo_dataset
from services.data_validation import compute_data_quality_report
from services.data_cleaning import DataCleaningService
from services.business_metrics import infer_business_columns, calculate_executive_kpis
from services.churn_model import ChurnPredictionPipeline
from services.explainability import ChurnExplainabilityService
from services.counterfactuals import CounterfactualAnalysisService
from services.forecasting import prepare_time_series, run_forecasting_pipeline
from services.advanced_forecasting import AdvancedForecastingService
from services.time_series_anomalies import TimeSeriesAnomalyDetector
from services.copilot import AnalyticsCopilotService
from services.presentation_generator import PresentationGenerator
from services.report_generator import generate_pdf_report


def test_full_ecommerce_analytics_pipeline():
    """
    Workflow 1: Ingestion -> Quality Audit -> Cleaning -> Executive KPIs -> Copilot -> PowerPoint Export
    """
    # 1. Load dataset
    df = get_demo_dataset("ecommerce")
    assert df is not None and not df.empty

    # 2. Quality Audit
    dq_report = compute_data_quality_report(df)
    assert dq_report["overall_score"] > 80.0

    # 3. Data Cleaning
    cleaner = DataCleaningService(df)
    cleaner.remove_duplicates()
    clean_df = cleaner.clean_df
    assert len(clean_df) <= len(df)

    # 4. Executive KPIs
    col_map = infer_business_columns(clean_df)
    kpis = calculate_executive_kpis(clean_df, col_map)
    assert kpis["total_revenue"] > 0
    assert kpis["total_orders"] > 0

    # 5. Natural Language Copilot
    copilot = AnalyticsCopilotService()
    copilot_res = copilot.ask("Top 5 products by revenue", clean_df)
    assert copilot_res["success"] is True
    assert not copilot_res["result_df"].empty

    # 6. Executive Presentation Deck Export (.pptx)
    deck_bytes = PresentationGenerator.generate_deck(
        kpis=kpis,
        insights=[],
        dataset_name="Demo E-Commerce Orders"
    )
    assert len(deck_bytes) > 5000


def test_full_churn_prediction_explainability_pipeline():
    """
    Workflow 2: Customer Data -> Churn Modeling -> Risk Scoring -> SHAP Attribution -> Counterfactuals
    """
    df = get_demo_dataset("churn")
    assert df is not None and not df.empty

    pipeline = ChurnPredictionPipeline()
    ok_prep, msg_prep = pipeline.prepare_data(df, target_col="churn", id_col="customer_id")
    assert ok_prep, msg_prep

    ok_train, msg_train = pipeline.train_and_evaluate(df)
    assert ok_train, msg_train

    risk_df = pipeline.score_customers(df)
    assert len(risk_df) == len(df)
    assert "Risk_Tier" in risk_df.columns

    # SHAP Explainability
    explain_svc = ChurnExplainabilityService(pipeline)
    first_customer = df.iloc[0]
    explanation = explain_svc.explain_individual_customer(first_customer, top_k=4)
    assert "error" not in explanation
    assert len(explanation["top_factors"]) <= 4

    # Prescriptive Counterfactual
    cf_svc = CounterfactualAnalysisService(pipeline)
    cf_res = cf_svc.predict_scenario(first_customer, {"contract_type": "Two year"})
    assert "error" not in cf_res
    assert "simulated_probability" in cf_res


def test_full_revenue_forecasting_anomaly_pipeline():
    """
    Workflow 3: Time-Series Data -> Sequential Holdout Backtest -> STL -> Anomalies -> PDF Export
    """
    df = get_demo_dataset("saas")
    assert df is not None and not df.empty

    ts, err = prepare_time_series(df, date_col="date", target_col="mrr", freq="MS")
    assert err is None
    assert len(ts) >= 12

    # Forecast pipeline with sequential backtesting
    fc_res = run_forecasting_pipeline(ts, horizon=6)
    assert fc_res["best_model"] is not None
    assert len(fc_res["forecast_df"]) == 6

    # STL decomposition
    stl_res = AdvancedForecastingService.perform_stl_decomposition(ts)
    assert stl_res["success"] is True

    # Anomaly scanning
    anom_res = TimeSeriesAnomalyDetector.detect_anomalies(ts, threshold_sigma=2.5)
    assert "anomalies" in anom_res

    # PDF Briefing Export
    col_map = infer_business_columns(df)
    kpis = calculate_executive_kpis(df, col_map)
    pdf_bytes = generate_pdf_report(
        kpis=kpis,
        insights=[],
        data_quality={"grade": "A", "overall_score": 95.0, "missing_cells": 0, "duplicate_rows": 0, "issues": []},
        dataset_name="Demo SaaS MRR"
    )
    assert len(pdf_bytes.getvalue()) > 1000
