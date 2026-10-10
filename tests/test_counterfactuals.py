"""
Unit tests for Prescriptive Counterfactual Analysis Service (Workstream 1).
"""

import pytest
import pandas as pd
import numpy as np
from services.churn_model import ChurnPredictionPipeline
from services.counterfactuals import CounterfactualAnalysisService


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


def test_immutable_feature_detection(trained_churn_pipeline):
    pipeline, df = trained_churn_pipeline
    cf_svc = CounterfactualAnalysisService(pipeline)

    assert not cf_svc.is_actionable_feature("CustomerID")
    assert not cf_svc.is_actionable_feature("tenure")
    assert not cf_svc.is_actionable_feature("signup_date")
    assert cf_svc.is_actionable_feature("Contract")
    assert cf_svc.is_actionable_feature("TechSupport")


def test_scenario_prediction(trained_churn_pipeline):
    pipeline, df = trained_churn_pipeline
    cf_svc = CounterfactualAnalysisService(pipeline)
    customer = df.iloc[0]

    res = cf_svc.predict_scenario(customer, {"Contract": "Two year"})

    assert "error" not in res
    assert 0.0 <= res["original_probability"] <= 1.0
    assert 0.0 <= res["simulated_probability"] <= 1.0
    assert "disclaimer" in res
    assert "Hypothetical Simulation Notice" in res["disclaimer"]


def test_minimal_counterfactuals(trained_churn_pipeline):
    pipeline, df = trained_churn_pipeline
    cf_svc = CounterfactualAnalysisService(pipeline)
    customer = df.iloc[0]

    paths = cf_svc.find_minimal_counterfactuals(customer, target_max_prob=0.35, dataset_sample=df)
    assert isinstance(paths, list)
    if paths:
        assert "changes" in paths[0]
        assert "simulated_prob" in paths[0]
