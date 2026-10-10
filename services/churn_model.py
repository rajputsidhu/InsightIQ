"""
End-to-End Customer Churn Prediction Engine for InsightIQ.
Implements robust leakage prevention, stratified evaluation, model benchmarking,
feature importance interpretation, and individual customer risk scoring.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    brier_score_loss,
    roc_curve,
    precision_recall_curve,
)

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False


class ChurnPredictionPipeline:
    def __init__(self):
        self.target_col: Optional[str] = None
        self.id_col: Optional[str] = None
        self.feature_cols: List[str] = []
        self.preprocessor = None
        self.models: Dict[str, Any] = {}
        self.evaluation_results: Dict[str, Dict[str, Any]] = {}
        self.best_model_name: Optional[str] = None
        self.X_test = None
        self.y_test = None
        self.feature_names_out: List[str] = []

    def prepare_data(
        self,
        df: pd.DataFrame,
        target_col: str,
        id_col: Optional[str] = None,
        drop_cols: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """
        Validate, separate features from IDs/targets, and construct preprocessing pipeline.
        """
        if df is None or df.empty:
            return False, "Dataset is empty."

        if target_col not in df.columns:
            return False, f"Target column '{target_col}' not found in dataset."

        self.target_col = target_col
        self.id_col = id_col

        working_df = df.copy()

        # Convert target to binary 0/1
        target_series = working_df[target_col].dropna()
        unique_targets = target_series.unique()
        
        if len(unique_targets) != 2:
            return False, f"Target '{target_col}' must have exactly 2 distinct classes (found {len(unique_targets)})."

        # Map to 0 and 1
        pos_val = 1
        if "yes" in [str(u).lower() for u in unique_targets]:
            mapping = {u: (1 if str(u).lower() in ["yes", "1", "true", "churn"] else 0) for u in unique_targets}
        else:
            sorted_unique = sorted(list(unique_targets))
            mapping = {sorted_unique[0]: 0, sorted_unique[1]: 1}

        working_df["_target_binary"] = working_df[target_col].map(mapping)
        working_df = working_df.dropna(subset=["_target_binary"])

        # Determine features to drop to prevent leakage
        cols_to_exclude = [target_col, "_target_binary"]
        if id_col and id_col in working_df.columns:
            cols_to_exclude.append(id_col)
        if drop_cols:
            cols_to_exclude.extend(drop_cols)

        # Drop columns with 'reason', 'status' that obviously leak post-churn knowledge
        for c in working_df.columns:
            if c not in cols_to_exclude:
                c_low = c.lower()
                if "churn_reason" in c_low or "cancellation_reason" in c_low or "churn_date" in c_low:
                    cols_to_exclude.append(c)

        features = [c for c in working_df.columns if c not in cols_to_exclude]
        if not features:
            return False, "No valid predictive features remaining after target/ID separation."

        self.feature_cols = features
        X = working_df[features]
        y = working_df["_target_binary"].astype(int)

        # Identify numeric vs categorical
        num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = [c for c in X.columns if c not in num_cols]

        numeric_transformer = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])

        categorical_transformer = Pipeline(steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ])

        self.preprocessor = ColumnTransformer(
            transformers=[
                ("num", numeric_transformer, num_cols),
                ("cat", categorical_transformer, cat_cols),
            ]
        )

        return True, f"Configured {len(features)} predictive features ({len(num_cols)} numeric, {len(cat_cols)} categorical)."

    def train_and_evaluate(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Train multiple models with stratified split and evaluate on holdout test set.
        """
        if self.preprocessor is None or self.target_col is None:
            return False, "Pipeline not prepared. Call prepare_data first."

        working_df = df.dropna(subset=[self.target_col]).copy()
        
        # Map target
        unique_targets = working_df[self.target_col].unique()
        if "yes" in [str(u).lower() for u in unique_targets]:
            mapping = {u: (1 if str(u).lower() in ["yes", "1", "true", "churn"] else 0) for u in unique_targets}
        else:
            sorted_unique = sorted(list(unique_targets))
            mapping = {sorted_unique[0]: 0, sorted_unique[1]: 1}
            
        y = working_df[self.target_col].map(mapping).astype(int)
        X = working_df[self.feature_cols]

        # Check class balance
        pos_rate = y.mean()
        if pos_rate == 0 or pos_rate == 1:
            return False, "Target has only a single class. Cannot train classification models."

        # Stratified 80/20 train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42, stratify=y
        )

        # Fit preprocessor
        X_train_proc = self.preprocessor.fit_transform(X_train)
        X_test_proc = self.preprocessor.transform(X_test)
        
        self.X_test = X_test
        self.y_test = y_test
        self.X_test_proc = X_test_proc

        # Extract transformed feature names
        feature_names = []
        for name, trans, cols in self.preprocessor.transformers_:
            if name == "num":
                feature_names.extend(cols)
            elif name == "cat":
                try:
                    cat_encoder = trans.named_steps["onehot"]
                    cat_names = cat_encoder.get_feature_names_out(cols).tolist()
                    feature_names.extend(cat_names)
                except Exception:
                    feature_names.extend(cols)
        self.feature_names_out = feature_names

        # Candidate models
        candidate_models = {
            "Baseline (Majority Class)": DummyClassifier(strategy="most_frequent"),
            "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
            "Random Forest": RandomForestClassifier(n_estimators=120, max_depth=8, min_samples_leaf=4, class_weight="balanced", random_state=42),
        }

        if HAS_XGBOOST:
            # Scale pos weight for imbalance
            scale_pos = (len(y_train) - sum(y_train)) / max(1, sum(y_train))
            candidate_models["XGBoost"] = xgb.XGBClassifier(
                n_estimators=100, max_depth=4, learning_rate=0.08, scale_pos_weight=scale_pos, eval_metric="logloss", random_state=42
            )
        else:
            candidate_models["Gradient Boosting"] = GradientBoostingClassifier(
                n_estimators=100, max_depth=4, learning_rate=0.08, random_state=42
            )

        self.models = {}
        self.evaluation_results = {}
        best_f1 = -1.0

        for model_name, model_obj in candidate_models.items():
            model_obj.fit(X_train_proc, y_train)
            self.models[model_name] = model_obj

            y_pred = model_obj.predict(X_test_proc)
            
            # Predict probabilities
            if hasattr(model_obj, "predict_proba"):
                y_prob = model_obj.predict_proba(X_test_proc)[:, 1]
            else:
                y_prob = y_pred.astype(float)

            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, zero_division=0)
            rec = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
            try:
                roc_auc = roc_auc_score(y_test, y_prob)
            except Exception:
                roc_auc = 0.5

            try:
                pr_auc = average_precision_score(y_test, y_prob)
            except Exception:
                pr_auc = pos_rate

            brier = brier_score_loss(y_test, y_prob)
            cm = confusion_matrix(y_test, y_pred)

            fpr, tpr, _ = roc_curve(y_test, y_prob)
            p_curve, r_curve, _ = precision_recall_curve(y_test, y_prob)

            self.evaluation_results[model_name] = {
                "accuracy": round(float(acc), 3),
                "precision": round(float(prec), 3),
                "recall": round(float(rec), 3),
                "f1_score": round(float(f1), 3),
                "roc_auc": round(float(roc_auc), 3),
                "pr_auc": round(float(pr_auc), 3),
                "brier_score": round(float(brier), 3),
                "confusion_matrix": cm.tolist(),
                "fpr": fpr.tolist(),
                "tpr": tpr.tolist(),
                "precision_curve": p_curve.tolist(),
                "recall_curve": r_curve.tolist(),
            }

            # Select best model based on F1-score (excluding baseline)
            if model_name != "Baseline (Majority Class)" and f1 > best_f1:
                best_f1 = f1
                self.best_model_name = model_name

        if not self.best_model_name:
            self.best_model_name = "Logistic Regression"

        return True, f"Successfully trained {len(self.models)} models. Best model: {self.best_model_name} (F1: {best_f1:.3f})."

    def get_comparison_table(self) -> pd.DataFrame:
        """Return formatted comparison table across all evaluated models."""
        rows = []
        for name, metrics in self.evaluation_results.items():
            rows.append({
                "Model": name,
                "Accuracy": f"{metrics['accuracy']:.3f}",
                "Precision": f"{metrics['precision']:.3f}",
                "Recall": f"{metrics['recall']:.3f}",
                "F1 Score": f"{metrics['f1_score']:.3f}",
                "ROC-AUC": f"{metrics['roc_auc']:.3f}",
                "PR-AUC": f"{metrics['pr_auc']:.3f}",
                "Brier Score": f"{metrics['brier_score']:.3f}",
                "Is Best": "★ Selected" if name == self.best_model_name else "",
            })
        return pd.DataFrame(rows)

    def get_feature_importance(self, top_n: int = 10) -> pd.DataFrame:
        """Extract top feature importance scores from the best model."""
        if not self.best_model_name or self.best_model_name not in self.models:
            return pd.DataFrame()

        model = self.models[self.best_model_name]
        importances = None

        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        elif hasattr(model, "coef_"):
            importances = np.abs(model.coef_[0])

        if importances is None or len(importances) != len(self.feature_names_out):
            return pd.DataFrame()

        df_imp = pd.DataFrame({
            "Feature": self.feature_names_out,
            "Importance": importances,
        }).sort_values(by="Importance", ascending=False).head(top_n).reset_index(drop=True)

        # Normalize to percentage
        total_imp = df_imp["Importance"].sum()
        if total_imp > 0:
            df_imp["Relative_Weight_Pct"] = (df_imp["Importance"] / total_imp * 100).round(1)

        return df_imp

    def score_customers(self, df: pd.DataFrame, high_risk_thresh: float = 0.65, med_risk_thresh: float = 0.35) -> pd.DataFrame:
        """Generate customer-level risk probabilities and tier classifications."""
        if not self.best_model_name or self.best_model_name not in self.models:
            return pd.DataFrame()

        model = self.models[self.best_model_name]
        X = df[self.feature_cols]
        X_proc = self.preprocessor.transform(X)

        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X_proc)[:, 1]
        else:
            probs = model.predict(X_proc).astype(float)

        risk_df = pd.DataFrame()
        if self.id_col and self.id_col in df.columns:
            risk_df["Customer_ID"] = df[self.id_col]
        else:
            risk_df["Customer_ID"] = [f"CUST-{1000 + i}" for i in range(len(df))]

        risk_df["Churn_Probability"] = probs.round(3)
        risk_df["Churn_Risk_Pct"] = (probs * 100).round(1)

        def assign_tier(p):
            if p >= high_risk_thresh:
                return "High Risk"
            elif p >= med_risk_thresh:
                return "Medium Risk"
            else:
                return "Low Risk"

        risk_df["Risk_Tier"] = risk_df["Churn_Probability"].apply(assign_tier)

        # Include selected relevant context columns
        for col in self.feature_cols[:4]:
            risk_df[col] = df[col].values

        risk_df = risk_df.sort_values(by="Churn_Probability", ascending=False).reset_index(drop=True)
        return risk_df
