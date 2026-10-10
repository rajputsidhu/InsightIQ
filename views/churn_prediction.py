"""
Customer Churn Prediction & Risk Modeling Page for InsightIQ.
Integrates supervised model benchmarking, global feature attribution, individual customer
SHAP explanations, and prescriptive counterfactual analysis with strict non-causal disclosures.
"""

import streamlit as st
import pandas as pd
import numpy as np
from components.header import render_header
from components.ui_components import render_page_title, render_section_header, render_empty_state
from components.kpi_cards import render_kpi_card
from components.charts import (
    plot_roc_curves,
    plot_pr_curves,
    plot_confusion_matrix_heatmap,
    plot_feature_importance_bar,
    apply_theme,
)
from components.tables import render_risk_table
from components.alerts import render_alert, render_methodology_disclaimer
from components.explanation_cards import (
    render_individual_explanation_card,
    render_counterfactual_comparison_card,
)
from components.design_system import get_theme_tokens
from services.churn_model import ChurnPredictionPipeline
from services.explainability import ChurnExplainabilityService
from services.counterfactuals import CounterfactualAnalysisService
from services.data_loader import get_demo_dataset
from services.report_generator import export_dataframe_to_csv_bytes


def render_churn_prediction_page():
    """Render supervised churn modeling and customer risk evaluation."""
    render_header("Churn Prediction", "Analytics")

    df: pd.DataFrame = st.session_state.get("active_df")

    if df is None or df.empty:
        render_empty_state(
            title="No Active Dataset Available",
            description="Load a customer retention dataset or switch to the Telecom Churn demo to train churn models.",
            icon="🎯"
        )
        return

    tokens = get_theme_tokens()

    # Check if active dataset contains a churn-like column
    cols = list(df.columns)
    churn_candidates = [c for c in cols if "churn" in c.lower() or "attrit" in c.lower() or "cancelled" in c.lower()]

    if not churn_candidates:
        render_alert(
            "The active dataset does not appear to contain a customer churn label column. "
            "You can load the 'Demo Telecom Churn' dataset from the sidebar to explore supervised retention modeling.",
            level="warning",
            title="No Churn Target Detected"
        )
        if st.button("👥 Load Demo Telecom Churn Dataset", type="primary"):
            churn_df = get_demo_dataset("churn")
            from components.sidebar import _set_active_dataset
            _set_active_dataset("Demo Telecom Churn", churn_df)
            st.rerun()
        return

    render_page_title(
        "Predictive Churn Intelligence & Explainable AI",
        "Benchmark classification models, inspect ROC/PR frontiers, review customer risk scores, and simulate commercial counterfactuals."
    )

    # Configuration Controls
    with st.expander("⚙️ Model Pipeline Configuration & Feature Controls", expanded=True):
        cfg_col1, cfg_col2, cfg_col3 = st.columns(3)
        with cfg_col1:
            target_col = st.selectbox(
                "Target Churn Column",
                options=churn_candidates + [c for c in cols if c not in churn_candidates],
                index=0,
                key="churn_target_col",
            )
        with cfg_col2:
            id_candidates = [c for c in cols if "id" in c.lower() or "cust" in c.lower()]
            id_col = st.selectbox(
                "Customer Identifier (Excluded from Training)",
                options=["None"] + id_candidates + [c for c in cols if c not in id_candidates],
                index=1 if id_candidates else 0,
                key="churn_id_col",
            )
            id_col_val = None if id_col == "None" else id_col

        with cfg_col3:
            drop_candidates = [c for c in cols if "reason" in c.lower() or "date" in c.lower()]
            drop_cols = st.multiselect(
                "Exclude Potential Target Leakage",
                options=[c for c in cols if c != target_col and c != id_col_val],
                default=[c for c in drop_candidates if c != target_col and c != id_col_val],
                key="churn_drop_cols",
            )

        train_btn = st.button("🚀 Train & Benchmark Models", type="primary", key="btn_train_churn")

    # Pipeline state management
    if "churn_pipeline" not in st.session_state or train_btn:
        with st.spinner("Preparing features and benchmarking models with stratified validation..."):
            pipeline = ChurnPredictionPipeline()
            ok_prep, msg_prep = pipeline.prepare_data(df, target_col=target_col, id_col=id_col_val, drop_cols=drop_cols)
            if not ok_prep:
                st.error(msg_prep)
                return

            ok_train, msg_train = pipeline.train_and_evaluate(df)
            if not ok_train:
                st.error(msg_train)
                return

            st.session_state["churn_pipeline"] = pipeline
            st.session_state["churn_ready"] = True
            st.session_state.pop("explain_svc", None)
            st.session_state.pop("cf_svc", None)
            st.success(msg_train)

    pipeline: ChurnPredictionPipeline = st.session_state.get("churn_pipeline")

    if not pipeline or not pipeline.evaluation_results:
        st.info("Click 'Train & Benchmark Models' to run the evaluation pipeline.")
        return

    best_res = pipeline.evaluation_results.get(pipeline.best_model_name, {})

    # Initialize Explainability & Counterfactual Services
    if "explain_svc" not in st.session_state:
        st.session_state["explain_svc"] = ChurnExplainabilityService(pipeline)
    if "cf_svc" not in st.session_state:
        st.session_state["cf_svc"] = CounterfactualAnalysisService(pipeline)

    explain_svc: ChurnExplainabilityService = st.session_state["explain_svc"]
    cf_svc: CounterfactualAnalysisService = st.session_state["cf_svc"]

    # Top Metric Cards Grid
    render_section_header("Model Evaluation Benchmarks", subtitle="Stratified test-split metrics across leading classification algorithms.", badge="Model Leader")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card("Best Model", pipeline.best_model_name, "Selected on Holdout F1", accent="blue")
    with k2:
        render_kpi_card("F1-Score", f"{best_res.get('f1_score', 0):.3f}", "Harmonic Precision/Recall", accent="teal")
    with k3:
        render_kpi_card("ROC-AUC", f"{best_res.get('roc_auc', 0):.3f}", "Discrimination Ability", accent="green")
    with k4:
        render_kpi_card("PR-AUC", f"{best_res.get('pr_auc', 0):.3f}", "Precision-Recall Integral", accent="purple")

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # Scored Dataset
    risk_df = pipeline.score_customers(df)

    # Tabs for Model Leaderboard, Diagnostic Curves, Risk Table, Individual Explainability, Counterfactuals, What-If
    tab_lead, tab_diag, tab_risk, tab_indiv, tab_cf, tab_sim = st.tabs([
        "🏆 Model Comparison",
        "📈 ROC & Confusion Matrix",
        "👥 Customer Risk Table",
        "🔍 Account Investigation (SHAP)",
        "🧪 Counterfactual Analysis",
        "🔮 What-If Simulator",
    ])

    with tab_lead:
        render_section_header("Holdout Test Set Performance Comparison", subtitle="Cross-model metrics table ranked by discrimination capacity.")
        comp_df = pipeline.get_comparison_table()
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

        render_section_header("Global Feature Importance & Attribution", subtitle="Relative contribution of predictive signals across the active model.")
        imp_df = explain_svc.get_global_importance().head(12)
        if not imp_df.empty:
            fig_imp = plot_feature_importance_bar(imp_df.rename(columns={"Importance": "importance", "Feature": "feature"}))
            st.plotly_chart(fig_imp, use_container_width=True)
            st.caption(f"Method: {imp_df['Method'].iloc[0]}. *Note: Statistical association does not imply direct empirical causality.*")
        else:
            st.info("Feature importance not available for the selected model.")

    with tab_diag:
        render_section_header("Diagnostic Classification Frontiers", subtitle="ROC discrimination and Precision-Recall tradeoffs on unseen validation data.")
        curve_c1, curve_c2 = st.columns(2)
        with curve_c1:
            fig_roc = plot_roc_curves(pipeline.evaluation_results)
            st.plotly_chart(fig_roc, use_container_width=True)

        with curve_c2:
            fig_pr = plot_pr_curves(pipeline.evaluation_results)
            st.plotly_chart(fig_pr, use_container_width=True)

        if "confusion_matrix" in best_res:
            render_section_header(f"Confusion Matrix — {pipeline.best_model_name}", subtitle="True vs. predicted class counts at default 0.5 decision threshold.")
            fig_cm = plot_confusion_matrix_heatmap(best_res["confusion_matrix"])
            st.plotly_chart(fig_cm, use_container_width=True)

    with tab_risk:
        render_section_header("Individual Customer Churn Risk Scores", subtitle="Account-level probabilistic risk scores with calibrated risk bands.")
        high_cnt = int((risk_df["Risk_Tier"] == "High Risk").sum())
        med_cnt = int((risk_df["Risk_Tier"] == "Medium Risk").sum())
        low_cnt = int((risk_df["Risk_Tier"] == "Low Risk").sum())
        total_scored = len(risk_df)

        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            st.metric("High Risk Accounts", f"{high_cnt:,}", f"{high_cnt/total_scored*100:.1f}% of cohort")
        with rc2:
            st.metric("Medium Risk Accounts", f"{med_cnt:,}", f"{med_cnt/total_scored*100:.1f}% of cohort")
        with rc3:
            st.metric("Low Risk Accounts", f"{low_cnt:,}", f"{low_cnt/total_scored*100:.1f}% of cohort")

        render_risk_table(risk_df, page_size=15, key_prefix="churn_risk_tbl")

        csv_bytes = export_dataframe_to_csv_bytes(risk_df)
        st.download_button(
            label="⬇️ Export Churn Risk Scores (CSV)",
            data=csv_bytes,
            file_name="insightiq_churn_risk_scores.csv",
            mime="text/csv",
        )

    with tab_indiv:
        render_section_header("Individual Customer Risk Attribution (SHAP)", subtitle="Local feature attribution explaining why a specific account received its risk score.")

        cust_id_col = pipeline.id_col if (pipeline.id_col and pipeline.id_col in risk_df.columns) else "CustomerID"
        if cust_id_col in risk_df.columns:
            customer_options = risk_df[cust_id_col].astype(str).tolist()
        else:
            customer_options = [f"Record #{i}" for i in range(len(risk_df))]

        sel_cust_col1, sel_cust_col2 = st.columns([2, 1])
        with sel_cust_col1:
            sel_customer_val = st.selectbox(
                "Select Customer Account",
                options=customer_options[:500],
                index=0,
                key="indiv_expl_selector"
            )

        with sel_cust_col2:
            top_k_factors = st.slider("Number of Factors to Show", min_value=3, max_value=10, value=5, key="shap_topk")

        # Retrieve selected row
        if cust_id_col in risk_df.columns:
            sel_row = df[df[cust_id_col].astype(str) == sel_customer_val].iloc[0]
        else:
            idx = customer_options.index(sel_customer_val)
            sel_row = df.iloc[idx]

        with st.spinner("Computing local feature attributions..."):
            explanation = explain_svc.explain_individual_customer(sel_row, top_k=top_k_factors)

        render_individual_explanation_card(explanation)

    with tab_cf:
        render_section_header("Prescriptive Counterfactual Analysis", subtitle="Simulate commercial parameter adjustments (pricing, contracts, support) to assess score delta.")

        actionable_features = cf_svc.get_actionable_features(df)
        if not actionable_features:
            st.info("No actionable commercial attributes detected for counterfactual simulation.")
        else:
            cf_c1, cf_c2 = st.columns([1, 1])
            with cf_c1:
                st.markdown(f"<div style='font-weight: 600; color: {tokens['text_primary']}; margin-bottom: 0.5rem;'>1. Baseline Customer Configuration</div>", unsafe_allow_html=True)
                st.markdown(f"**Target Account:** `{sel_customer_val}`")
                current_risk_val = risk_df.loc[df[cust_id_col].astype(str) == sel_customer_val, 'Risk_Tier'].values[0] if cust_id_col in risk_df.columns else 'Assessed'
                st.markdown(f"**Current Risk:** `{current_risk_val}`")

            with cf_c2:
                st.markdown(f"<div style='font-weight: 600; color: {tokens['text_primary']}; margin-bottom: 0.5rem;'>2. Automated Actionable Interventions</div>", unsafe_allow_html=True)
                minimal_paths = cf_svc.find_minimal_counterfactuals(sel_row, target_max_prob=0.35, dataset_sample=df)
                if minimal_paths:
                    for i, path in enumerate(minimal_paths[:3], 1):
                        ch_str = ", ".join([f"{col}: '{c['from']}' ➔ '{c['to']}'" for col, c in path["changes"].items()])
                        st.markdown(f"- **Option {i}:** {ch_str} (Predicted: **{path['simulated_prob']*100:.1f}%**, -{path['drop_pct']:.1f}%)")
                else:
                    st.caption("No single-feature intervention met the <35% low-risk threshold.")

            render_section_header("Interactive Counterfactual Builder", subtitle="Adjust individual attributes to simulate expected risk migration.")
            cf_modifications = {}
            mod_cols = st.columns(min(3, len(actionable_features[:6])))

            for idx, feat in enumerate(actionable_features[:6]):
                with mod_cols[idx % len(mod_cols)]:
                    curr_val = sel_row.get(feat)
                    if pd.api.types.is_numeric_dtype(df[feat]):
                        min_v = float(df[feat].min())
                        max_v = float(df[feat].max())
                        step_v = (max_v - min_v) / 20.0 or 1.0
                        new_val = st.slider(f"{feat}", min_value=min_v, max_value=max_v, value=float(curr_val) if pd.notnull(curr_val) else min_v, step=step_v, key=f"cf_sl_{feat}")
                    else:
                        opts = list(df[feat].dropna().unique())
                        def_idx = opts.index(curr_val) if curr_val in opts else 0
                        new_val = st.selectbox(f"{feat}", options=opts, index=def_idx, key=f"cf_sb_{feat}")
                    
                    if str(new_val) != str(curr_val):
                        cf_modifications[feat] = new_val

            if cf_modifications:
                sim_res = cf_svc.predict_scenario(sel_row, cf_modifications)
                render_counterfactual_comparison_card(sim_res)
            else:
                st.info("Adjust one or more parameters above to evaluate a hypothetical scenario.")

    with tab_sim:
        render_section_header("Interactive Customer Risk Simulator", subtitle="Adjust characteristics in real time to observe predicted churn probability.")

        sim_inputs = {}
        features = pipeline.feature_cols[:8]
        sim_cols = st.columns(2)

        for idx, feat in enumerate(features):
            with sim_cols[idx % 2]:
                if np.issubdtype(df[feat].dtype, np.number):
                    min_v = float(df[feat].min())
                    max_v = float(df[feat].max())
                    default_v = float(df[feat].median())
                    sim_inputs[feat] = st.slider(f"{feat}", min_value=min_v, max_value=max_v, value=default_v, key=f"sim_feat_{feat}")
                else:
                    unique_vals = list(df[feat].dropna().unique())
                    sim_inputs[feat] = st.selectbox(f"{feat}", options=unique_vals, key=f"sim_feat_{feat}")

        for feat in pipeline.feature_cols:
            if feat not in sim_inputs:
                if np.issubdtype(df[feat].dtype, np.number):
                    sim_inputs[feat] = float(df[feat].median())
                else:
                    mode_v = df[feat].mode()
                    sim_inputs[feat] = mode_v[0] if not mode_v.empty else "Unknown"

        sim_df = pd.DataFrame([sim_inputs])
        sim_proc = pipeline.preprocessor.transform(sim_df)
        best_model = pipeline.models[pipeline.best_model_name]

        if hasattr(best_model, "predict_proba"):
            sim_prob = float(best_model.predict_proba(sim_proc)[0, 1])
        else:
            sim_prob = float(best_model.predict(sim_proc)[0])

        sim_tier = "High Risk" if sim_prob >= 0.65 else ("Medium Risk" if sim_prob >= 0.35 else "Low Risk")
        tier_color = tokens["danger"] if sim_prob >= 0.65 else (tokens["warning"] if sim_prob >= 0.35 else tokens["success"])

        st.markdown(
            f"""
            <div style="background: {tokens['surface']}; border: 1px solid {tokens['border']}; border-radius: 12px; padding: 1.5rem; margin-top: 1.25rem; text-align: center; box-shadow: {tokens['card_shadow']};">
                <div style="font-size: 0.775rem; color: {tokens['text_muted']}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">SIMULATED CHURN PROBABILITY</div>
                <div style="font-size: 2.5rem; font-weight: 800; color: {tier_color}; line-height: 1.2; margin: 0.25rem 0; font-variant-numeric: tabular-nums;">
                    {sim_prob * 100:.1f}%
                </div>
                <div style="font-size: 0.95rem; font-weight: 600; color: {tokens['text_primary']};">Status: <span style="color: {tier_color};">{sim_tier}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_methodology_disclaimer()
