"""
Unit tests for Customer Churn Modeling Pipeline.
"""

import pandas as pd
import numpy as np
import pytest
from services.churn_model import ChurnPredictionPipeline


def test_churn_pipeline_end_to_end():
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        "cust_id": [f"C{i}" for i in range(n)],
        "tenure": np.random.randint(1, 60, size=n),
        "monthly_charges": np.random.uniform(20, 100, size=n),
        "contract": np.random.choice(["Month-to-month", "One year", "Two year"], size=n),
        "churn": np.random.choice([0, 1], size=n, p=[0.7, 0.3]),
    })

    pipeline = ChurnPredictionPipeline()
    ok_prep, msg_prep = pipeline.prepare_data(df, target_col="churn", id_col="cust_id")
    assert ok_prep is True
    assert "cust_id" not in pipeline.feature_cols
    assert "churn" not in pipeline.feature_cols

    ok_train, msg_train = pipeline.train_and_evaluate(df)
    assert ok_train is True
    assert len(pipeline.models) >= 3
    assert pipeline.best_model_name is not None

    comp_table = pipeline.get_comparison_table()
    assert len(comp_table) >= 3
    assert "F1 Score" in comp_table.columns
    assert "ROC-AUC" in comp_table.columns

    # Test scoring
    risk_df = pipeline.score_customers(df)
    assert len(risk_df) == n
    assert "Churn_Probability" in risk_df.columns
    assert "Risk_Tier" in risk_df.columns
    assert risk_df["Risk_Tier"].isin(["High Risk", "Medium Risk", "Low Risk"]).all()
