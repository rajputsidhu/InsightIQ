"""
Explainability Service for InsightIQ Churn Prediction.
Provides SHAP global feature attributions, individual waterfall/force explanations,
and plain-language interpretation cards with strict non-causal statistical grounding.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False


class ChurnExplainabilityService:
    """
    Computes global and local feature importance and SHAP attributions
    for trained churn models.
    """

    def __init__(self, pipeline):
        """
        Initialize with a fitted ChurnPredictionPipeline instance.
        """
        self.pipeline = pipeline
        self.explainer = None
        self.shap_values = None
        self.explainer_model_name = None
        self.background_sample = None
        self._init_explainer()

    def _init_explainer(self):
        """Initialize appropriate SHAP explainer for the best model."""
        if not HAS_SHAP or not self.pipeline or not self.pipeline.models:
            return

        best_name = self.pipeline.best_model_name
        if not best_name or best_name not in self.pipeline.models:
            return

        model = self.pipeline.models[best_name]
        self.explainer_model_name = best_name

        # Prepare bounded background sample from test set
        X_test_proc = getattr(self.pipeline, "X_test_proc", None)
        if X_test_proc is None or len(X_test_proc) == 0:
            return

        # Cap background dataset at 100 samples for high responsiveness and stability
        bg_size = min(100, len(X_test_proc))
        np.random.seed(42)
        sample_indices = np.random.choice(len(X_test_proc), size=bg_size, replace=False)
        self.background_sample = X_test_proc[sample_indices]

        try:
            if "Random Forest" in best_name or "XGBoost" in best_name or "Gradient Boosting" in best_name:
                self.explainer = shap.TreeExplainer(model, data=self.background_sample)
            elif "Logistic Regression" in best_name:
                self.explainer = shap.LinearExplainer(model, data=self.background_sample)
            else:
                self.explainer = shap.Explainer(model.predict_proba, self.background_sample)
        except Exception:
            # Fallback to model-agnostic sampling explainer
            try:
                predict_fn = getattr(model, "predict_proba", model.predict)
                self.explainer = shap.KernelExplainer(predict_fn, self.background_sample[:30])
            except Exception:
                self.explainer = None

    def get_global_importance(self) -> pd.DataFrame:
        """
        Return structured global feature importance dataframe.
        Blends SHAP mean absolute values if available, otherwise fitted model feature importances/coefficients.
        """
        feature_names = self.pipeline.feature_names_out or [f"Feature_{i}" for i in range(len(self.pipeline.feature_cols))]
        best_name = self.pipeline.best_model_name
        model = self.pipeline.models.get(best_name) if self.pipeline and best_name else None

        if model is None:
            return pd.DataFrame(columns=["Feature", "Importance", "Method"])

        # 1. Try SHAP global importance
        if HAS_SHAP and self.explainer is not None and getattr(self.pipeline, "X_test_proc", None) is not None:
            try:
                eval_sample = self.pipeline.X_test_proc[:150]
                shap_vals = self.explainer(eval_sample)
                
                # Extract values for positive class (churn = 1)
                if hasattr(shap_vals, "values"):
                    vals = shap_vals.values
                    if vals.ndim == 3:  # (samples, features, classes)
                        vals = vals[:, :, 1]
                else:
                    vals = shap_vals
                    if isinstance(vals, list) and len(vals) == 2:
                        vals = vals[1]

                mean_abs = np.mean(np.abs(vals), axis=0)
                if len(mean_abs) == len(feature_names):
                    df_imp = pd.DataFrame({
                        "Feature": feature_names,
                        "Importance": mean_abs,
                        "Method": "SHAP Mean |Attribution|"
                    }).sort_values("Importance", ascending=False).reset_index(drop=True)
                    return df_imp
            except Exception:
                pass

        # 2. Model-based fallback
        importances = []
        method = "Model Importances"
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            method = "Gini Impurity Importance"
        elif hasattr(model, "coef_"):
            coef = model.coef_
            importances = np.abs(coef[0] if coef.ndim > 1 else coef)
            method = "Absolute Logistic Coefficients"
        else:
            importances = np.ones(len(feature_names)) / max(1, len(feature_names))
            method = "Uniform Baseline"

        df_imp = pd.DataFrame({
            "Feature": feature_names[:len(importances)],
            "Importance": importances,
            "Method": method
        }).sort_values("Importance", ascending=False).reset_index(drop=True)
        return df_imp

    def explain_individual_customer(
        self,
        customer_row: pd.Series,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Generate feature-level attributions and plain-language explanation
        for a single customer record.
        """
        if self.pipeline is None or self.pipeline.preprocessor is None:
            return {"error": "Pipeline preprocessor not initialized."}

        features = self.pipeline.feature_cols
        # Extract features present in the series
        cust_df = pd.DataFrame([customer_row])[features]

        # Transform single customer using fitted preprocessor
        try:
            cust_proc = self.pipeline.preprocessor.transform(cust_df)
        except Exception as e:
            return {"error": f"Failed to preprocess customer features: {str(e)}"}

        best_name = self.pipeline.best_model_name
        model = self.pipeline.models.get(best_name)
        if model is None:
            return {"error": "Fitted model not found."}

        # Predict probability
        if hasattr(model, "predict_proba"):
            prob = float(model.predict_proba(cust_proc)[0, 1])
        else:
            prob = float(model.predict(cust_proc)[0])

        risk_tier = "High Risk" if prob >= 0.65 else ("Medium Risk" if prob >= 0.35 else "Low Risk")

        feature_names = self.pipeline.feature_names_out or [f"Feature_{i}" for i in range(cust_proc.shape[1])]
        contributions: List[Dict[str, Any]] = []
        explanation_method = "Statistical Proxy"
        base_value = 0.5

        # Attempt SHAP local attribution
        if HAS_SHAP and self.explainer is not None:
            try:
                shap_obj = self.explainer(cust_proc)
                vals = shap_obj.values[0]
                if vals.ndim == 2:  # (features, classes)
                    vals = vals[:, 1]
                
                base_val = getattr(shap_obj, "base_values", [0.5])[0]
                if isinstance(base_val, (list, np.ndarray)):
                    base_val = base_val[1] if len(base_val) > 1 else base_val[0]
                base_value = float(base_val)

                for name, attr_val in zip(feature_names, vals):
                    contributions.append({
                        "feature": name,
                        "attribution": float(attr_val),
                        "direction": "Increases Churn Risk" if attr_val > 0 else "Decreases Churn Risk",
                        "abs_attribution": abs(float(attr_val))
                    })
                explanation_method = "SHAP Tree/Linear Attribution"
            except Exception:
                contributions = []

        # Fallback if SHAP was unavailable or failed
        if not contributions:
            if hasattr(model, "coef_"):
                coef = model.coef_[0] if model.coef_.ndim > 1 else model.coef_
                vals = cust_proc[0] * coef
                for name, attr_val in zip(feature_names, vals):
                    contributions.append({
                        "feature": name,
                        "attribution": float(attr_val),
                        "direction": "Increases Churn Risk" if attr_val > 0 else "Decreases Churn Risk",
                        "abs_attribution": abs(float(attr_val))
                    })
                explanation_method = "Linear Contribution (Weight × Value)"
            else:
                # Use global feature importances signed by distance from median
                global_imp = self.get_global_importance().set_index("Feature")["Importance"].to_dict()
                for name in feature_names:
                    imp = global_imp.get(name, 0.01)
                    contributions.append({
                        "feature": name,
                        "attribution": float(imp),
                        "direction": "Associated with Risk",
                        "abs_attribution": abs(float(imp))
                    })
                explanation_method = "Global Feature Importance Weighted"

        # Sort top contributors
        contributions.sort(key=lambda x: x["abs_attribution"], reverse=True)
        top_factors = contributions[:top_k]

        # Plain-language narrative synthesis without claiming causality
        top_increasing = [f for f in top_factors if f["attribution"] > 0]
        top_decreasing = [f for f in top_factors if f["attribution"] < 0]

        factors_summary = []
        if top_increasing:
            inc_names = [f["feature"].replace("num__", "").replace("cat__", "").replace("_", " ") for f in top_increasing[:2]]
            factors_summary.append(f"Model associates higher churn probability primarily with factors including {', '.join(inc_names)}.")
        if top_decreasing:
            dec_names = [f["feature"].replace("num__", "").replace("cat__", "").replace("_", " ") for f in top_decreasing[:2]]
            factors_summary.append(f"Protective factors reducing predicted risk include {', '.join(dec_names)}.")

        narrative = " ".join(factors_summary) if factors_summary else "Feature attributions distributed across multiple behavioral indicators."
        methodology_note = (
            "Statistical Disclaimer: Identified attributions reflect mathematical model weights and correlations. "
            "They do not establish direct empirical causality or guarantee that altering these variables will prevent churn."
        )

        return {
            "customer_id": customer_row.get(self.pipeline.id_col, "Selected Account") if self.pipeline.id_col else "Selected Account",
            "model_name": best_name,
            "churn_probability": round(prob, 4),
            "risk_tier": risk_tier,
            "base_value": round(base_value, 4),
            "explanation_method": explanation_method,
            "top_factors": top_factors,
            "all_contributions": contributions,
            "narrative_explanation": narrative,
            "methodology_note": methodology_note,
        }
