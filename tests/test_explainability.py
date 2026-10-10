"""
Unit tests for Churn Explainability Service (Workstream 1).
"""

import pytest
import pandas as pd
import numpy as np
from services.churn_model import ChurnPredictionPipeline
from services.explainability import ChurnExplainabilityService


@pytest.fixture
def trained_churn_pipeline():
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        "CustomerID": [f"CUST_{i:03d}" for i in range(n)],
        "tenure": np.random.randint(1, 72, size=n),
        "MonthlyCharges": np.random.uniform(20, 120, size=n),
        "Contract": np.random.choice(["Month-to-month", "One year", "Two year"], size=n),
        "TechSupport": np.random.choice(["Yes", "No"], size=n),
        "Churn": np.random.choice(["Yes", "No"], size=n, p=[0.3, 0.7]),
    })

    pipeline = ChurnPredictionPipeline()
    ok, _ = pipeline.prepare_data(df, target_col="Churn", id_col="CustomerID")
    assert ok
    ok_train, _ = pipeline.train_and_evaluate(df)
    assert ok_train
    return pipeline, df


def test_global_importance(trained_churn_pipeline):
    pipeline, df = trained_churn_pipeline
    svc = ChurnExplainabilityService(pipeline)
    imp_df = svc.get_global_importance()

    assert not imp_df.empty
    assert "Feature" in imp_df.columns
    assert "Importance" in imp_df.columns
    assert "Method" in imp_df.columns
    assert (imp_df["Importance"] >= 0).all()


def test_individual_customer_explanation(trained_churn_pipeline):
    pipeline, df = trained_churn_pipeline
    svc = ChurnExplainabilityService(pipeline)
    first_customer = df.iloc[0]

    explanation = svc.explain_individual_customer(first_customer, top_k=3)

    assert "error" not in explanation
    assert "churn_probability" in explanation
    assert 0.0 <= explanation["churn_probability"] <= 1.0
    assert explanation["risk_tier"] in ["High Risk", "Medium Risk", "Low Risk"]
    assert len(explanation["top_factors"]) <= 3
    assert "narrative_explanation" in explanation
    assert "methodology_note" in explanation
