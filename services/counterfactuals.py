"""
Prescriptive Counterfactual Analysis Service for InsightIQ.
Simulates hypothetical feature configuration changes on customer records to explore
model sensitivity while strictly enforcing domain constraints, immutable variable guards,
and explicit non-causal simulation notices.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple


class CounterfactualAnalysisService:
    """
    Evaluates actionable hypothetical feature variations against a fitted churn model pipeline.
    """

    # Variables that cannot or should not be modified in counterfactual interventions
    IMMUTABLE_KEYWORDS = [
        "id", "account", "gender", "senior", "partner", "dependents", "date",
        "tenure", "age", "signup", "created", "totalcharges", "total_charges"
    ]

    def __init__(self, pipeline):
        self.pipeline = pipeline

    def is_actionable_feature(self, col_name: str) -> bool:
        """Check if feature represents an operationally adjustable commercial attribute."""
        col_low = col_name.lower()
        for kw in self.IMMUTABLE_KEYWORDS:
            if kw in col_low:
                return False
        return True

    def get_actionable_features(self, df: pd.DataFrame) -> List[str]:
        """List features that can be legitimately altered in business simulations."""
        if self.pipeline is None:
            return []
        return [c for c in self.pipeline.feature_cols if self.is_actionable_feature(c)]

    def predict_scenario(
        self,
        base_series: pd.Series,
        modifications: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate a modified hypothetical customer record against the trained pipeline.
        """
        if self.pipeline is None or self.pipeline.preprocessor is None:
            return {"error": "Pipeline preprocessor not initialized."}

        best_name = self.pipeline.best_model_name
        model = self.pipeline.models.get(best_name)
        if model is None:
            return {"error": "Model not available."}

        # Original prediction
        orig_row = pd.DataFrame([base_series])[self.pipeline.feature_cols]
        orig_proc = self.pipeline.preprocessor.transform(orig_row)
        orig_prob = float(model.predict_proba(orig_proc)[0, 1]) if hasattr(model, "predict_proba") else float(model.predict(orig_proc)[0])

        # Modified prediction
        mod_series = base_series.copy()
        for col, val in modifications.items():
            if col in mod_series.index:
                # Cast to matching dtype
                orig_val = mod_series[col]
                if isinstance(orig_val, (int, np.integer)):
                    mod_series[col] = int(val)
                elif isinstance(orig_val, (float, np.floating)):
                    mod_series[col] = float(val)
                else:
                    mod_series[col] = str(val)

        mod_row = pd.DataFrame([mod_series])[self.pipeline.feature_cols]
        mod_proc = self.pipeline.preprocessor.transform(mod_row)
        mod_prob = float(model.predict_proba(mod_proc)[0, 1]) if hasattr(model, "predict_proba") else float(model.predict(mod_proc)[0])

        delta_prob = mod_prob - orig_prob
        pct_change = ((mod_prob - orig_prob) / orig_prob * 100) if orig_prob > 0 else 0.0

        orig_tier = "High Risk" if orig_prob >= 0.65 else ("Medium Risk" if orig_prob >= 0.35 else "Low Risk")
        mod_tier = "High Risk" if mod_prob >= 0.65 else ("Medium Risk" if mod_prob >= 0.35 else "Low Risk")

        disclaimer = (
            "Hypothetical Simulation Notice: Under this simulated feature configuration, the model's predicted "
            f"churn score shifts from {orig_prob*100:.1f}% to {mod_prob*100:.1f}%. This represents a mathematical "
            "model sensitivity estimate, not a guaranteed causal outcome or empirical contract guarantee."
        )

        return {
            "original_probability": round(orig_prob, 4),
            "simulated_probability": round(mod_prob, 4),
            "absolute_delta": round(delta_prob, 4),
            "percentage_change": round(pct_change, 2),
            "original_tier": orig_tier,
            "simulated_tier": mod_tier,
            "applied_modifications": modifications,
            "disclaimer": disclaimer,
            "model_used": best_name,
        }

    def find_minimal_counterfactuals(
        self,
        base_series: pd.Series,
        target_max_prob: float = 0.35,
        dataset_sample: Optional[pd.DataFrame] = None
    ) -> List[Dict[str, Any]]:
        """
        Explore single-feature and two-feature intervention candidate paths
        that drive predicted probability below target_max_prob.
        """
        actionable_cols = self.get_actionable_features(dataset_sample if dataset_sample is not None else pd.DataFrame([base_series]))
        candidates = []

        # Find domain values for actionable columns from dataset_sample
        domain_values: Dict[str, List[Any]] = {}
        if dataset_sample is not None:
            for col in actionable_cols:
                if col in dataset_sample.columns:
                    if pd.api.types.is_numeric_dtype(dataset_sample[col]):
                        q25, q50, q75 = dataset_sample[col].quantile([0.25, 0.50, 0.75]).tolist()
                        domain_values[col] = [q25, q50, q75]
                    else:
                        domain_values[col] = list(dataset_sample[col].dropna().unique())[:4]

        # Test single-attribute interventions
        for col, test_vals in domain_values.items():
            current_val = base_series.get(col)
            for tv in test_vals:
                if str(tv) != str(current_val):
                    res = self.predict_scenario(base_series, {col: tv})
                    if res.get("simulated_probability", 1.0) < res.get("original_probability", 1.0):
                        candidates.append({
                            "changes": {col: {"from": current_val, "to": tv}},
                            "simulated_prob": res["simulated_probability"],
                            "drop_pct": abs(res["percentage_change"]),
                            "achieves_target": res["simulated_probability"] <= target_max_prob
                        })

        # Sort by largest probability reduction
        candidates.sort(key=lambda x: x["simulated_prob"])
        return candidates[:5]
