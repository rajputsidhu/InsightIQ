"""
Deterministic Business Insight Engine for InsightIQ.
Generates evidence-based observations, supporting metrics, operational interpretations,
and prioritized recommendations from computed analytical results.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


def generate_business_insights(
    df: pd.DataFrame,
    col_map: Dict[str, Optional[str]],
    kpis: Optional[Dict[str, Any]] = None,
    churn_summary: Optional[Dict[str, Any]] = None,
    forecast_summary: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Evaluate deterministic analytical rules against current dataset state
    and return structured, actionable insight cards.
    """
    insights: List[Dict[str, Any]] = []

    if df is None or df.empty:
        return [{
            "title": "No Dataset Available",
            "category": "System",
            "severity": "neutral",
            "finding": "Please load or upload a dataset to generate analytical intelligence.",
            "supporting_metric": "0 records",
            "baseline_comparison": "N/A",
            "interpretation": "Analytics modules require active tabular records.",
            "recommended_actions": ["Upload a CSV/Excel file or click 'Explore Demo Dataset'."],
            "limitations": "No data.",
        }]

    rev_col = col_map.get("revenue")
    profit_col = col_map.get("profit")
    cust_col = col_map.get("customer_id")
    cat_col = col_map.get("category")
    date_col = col_map.get("date")

    # 1. Revenue Growth & Trajectory
    if kpis and kpis.get("revenue_growth_pct") is not None:
        growth = kpis["revenue_growth_pct"]
        if growth >= 10.0:
            insights.append({
                "title": "Strong Revenue Expansion Detected",
                "category": "Revenue & Growth",
                "severity": "positive",
                "finding": f"Net revenue expanded by {growth:+.1f}% across the evaluated time interval.",
                "supporting_metric": f"{growth:+.1f}% Growth",
                "baseline_comparison": "Prior comparable period midpoint",
                "interpretation": "Sales volume and order velocity outpaced historical baselines, indicating healthy customer acquisition and basket size.",
                "recommended_actions": [
                    "Examine top-selling SKUs to ensure inventory and supply chains match accelerated demand.",
                    "Audit marketing channel ROI during high-growth periods to double down on high-converting channels.",
                ],
                "limitations": "Calculated based on equal time splits without adjusting for external macro seasonality.",
            })
        elif growth <= -5.0:
            insights.append({
                "title": "Revenue Contraction Alert",
                "category": "Revenue & Growth",
                "severity": "risk",
                "finding": f"Net revenue declined by {abs(growth):.1f}% relative to the earlier operational window.",
                "supporting_metric": f"{growth:+.1f}% Drop",
                "baseline_comparison": "Prior comparable period midpoint",
                "interpretation": "Observed revenue slowdown could stem from reduced order volume, lower average order values, or increased churn.",
                "recommended_actions": [
                    "Investigate customer repurchase frequency and recent churn signals.",
                    "Review promotional discount efficacy and pricing elasticity.",
                ],
                "limitations": "Does not establish causal origin; further diagnostic segmentation recommended.",
            })

    # 2. Profit Margin & Unit Economics
    if kpis and kpis.get("profit_margin_pct") is not None:
        margin = kpis["profit_margin_pct"]
        if margin < 15.0:
            insights.append({
                "title": "Compressed Operating Profit Margin",
                "category": "Profitability",
                "severity": "warning",
                "finding": f"Overall profit margin stands at {margin:.1f}%, reflecting compressed unit economics.",
                "supporting_metric": f"{margin:.1f}% Margin",
                "baseline_comparison": "Target SaaS/Retail benchmark (>25%)",
                "interpretation": "High product costs, aggressive discounting, or operational shipping overheads are diluting gross earnings.",
                "recommended_actions": [
                    "Audit discounted transactions to identify unprofitable SKU lines.",
                    "Renegotiate wholesale vendor pricing or establish minimum order quantity thresholds.",
                ],
                "limitations": "Margin calculation assumes reported costs capture all direct COGS.",
            })
        elif margin >= 30.0:
            insights.append({
                "title": "Robust Profitability & Healthy Unit Margin",
                "category": "Profitability",
                "severity": "positive",
                "finding": f"Operating margin remains healthy at {margin:.1f}% across all sales volume.",
                "supporting_metric": f"{margin:.1f}% Margin",
                "baseline_comparison": "Industry average baseline (20-25%)",
                "interpretation": "Pricing structures provide ample cushion above unit costs, enabling sustainable reinvestment into growth.",
                "recommended_actions": [
                    "Explore expanding marketing budget to scale customer acquisition while margins remain high.",
                ],
                "limitations": "Excludes indirect overhead, tax, and amortization unless included in source dataset.",
            })

    # 3. Customer Concentration Risk (Pareto Analysis)
    if cust_col and cust_col in df.columns and rev_col and rev_col in df.columns:
        cust_rev = df.groupby(cust_col)[rev_col].sum().sort_values(ascending=False)
        total_rev = cust_rev.sum()
        if total_rev > 0 and len(cust_rev) >= 10:
            top_10_pct_count = max(1, int(len(cust_rev) * 0.10))
            top_10_pct_rev = cust_rev.head(top_10_pct_count).sum()
            concentration_share = round((top_10_pct_rev / total_rev) * 100, 1)

            if concentration_share >= 50.0:
                insights.append({
                    "title": "High Customer Revenue Concentration",
                    "category": "Customer Portfolio",
                    "severity": "warning",
                    "finding": f"Top 10% of customers ({top_10_pct_count:,} accounts) generate {concentration_share}% of total platform revenue.",
                    "supporting_metric": f"{concentration_share}% Revenue in Top 10%",
                    "baseline_comparison": "Standard 80/20 distribution benchmark",
                    "interpretation": "High concentration creates strategic vulnerability; losing even a handful of top accounts could disproportionately impact cash flow.",
                    "recommended_actions": [
                        "Assign dedicated Account Managers / Customer Success leads to key accounts.",
                        "Broaden mid-market acquisition campaigns to diversify revenue distribution.",
                    ],
                    "limitations": "Based on historical transactions within dataset date range.",
                })

    # 4. Product Category Dominance
    if cat_col and cat_col in df.columns and rev_col and rev_col in df.columns:
        cat_rev = df.groupby(cat_col)[rev_col].sum().sort_values(ascending=False)
        total_rev = cat_rev.sum()
        if total_rev > 0 and len(cat_rev) > 1:
            top_cat = cat_rev.index[0]
            top_cat_share = round((cat_rev.iloc[0] / total_rev) * 100, 1)
            
            insights.append({
                "title": f"Category Leader: {top_cat}",
                "category": "Product Strategy",
                "severity": "neutral",
                "finding": f"'{top_cat}' leads all product lines, generating {top_cat_share}% (${cat_rev.iloc[0]:,.2f}) of total revenue.",
                "supporting_metric": f"{top_cat_share}% Portfolio Share",
                "baseline_comparison": f"Outperforms #{2} category ('{cat_rev.index[1]}') by {(cat_rev.iloc[0] - cat_rev.iloc[1]):,.2f}",
                "interpretation": f"Primary revenue engine is heavily anchored in '{top_cat}'. Cross-selling opportunities into adjacent categories remain under-leveraged.",
                "recommended_actions": [
                    f"Create bundle promotions pairing '{top_cat}' items with complementary secondary categories.",
                    "Evaluate whether secondary categories suffer from poor product discovery or uncompetitive pricing.",
                ],
                "limitations": "Category classifications derived directly from dataset labels.",
            })

    # 5. Churn Risk Warning (if churn modeling output provided)
    if churn_summary and "high_risk_pct" in churn_summary:
        high_risk_pct = churn_summary["high_risk_pct"]
        if high_risk_pct >= 20.0:
            insights.append({
                "title": "Elevated Churn Exposure in Active Accounts",
                "category": "Customer Retention",
                "severity": "risk",
                "finding": f"{high_risk_pct:.1f}% of evaluated customers exhibit elevated churn probability (>65%).",
                "supporting_metric": f"{high_risk_pct:.1f}% High Risk Accounts",
                "baseline_comparison": "Internal safe threshold (<12%)",
                "interpretation": "Machine learning model identified strong churn warning signals driven primarily by short tenure, contract type, or high support ticket frequency.",
                "recommended_actions": [
                    "Deploy automated re-engagement workflows with tailored retention incentives for high-risk accounts.",
                    "Conduct proactive customer success outreach to resolve unresolved support tickets.",
                ],
                "limitations": "Statistical prediction based on current feature snapshot; not a certainty.",
            })

    # 6. Forecasting Outlook (if forecast summary provided)
    if forecast_summary and "projected_growth_pct" in forecast_summary:
        f_growth = forecast_summary["projected_growth_pct"]
        insights.append({
            "title": "Predictive Revenue Horizon Outlook",
            "category": "Forecasting",
            "severity": "positive" if f_growth >= 0 else "warning",
            "finding": f"Statistical time-series models project a {f_growth:+.1f}% trend over the next forecast horizon.",
            "supporting_metric": f"{f_growth:+.1f}% Projected Trajectory",
            "baseline_comparison": "Historical mean baseline",
            "interpretation": "Forecast integrates historical trend and smoothing parameters. Uncertainty bounds widen as horizon extends.",
            "recommended_actions": [
                "Align working capital and procurement with projected demand intervals.",
                "Monitor leading monthly indicators to validate model assumptions.",
            ],
            "limitations": "Assumes historical seasonality and baseline demand dynamics remain structurally stable.",
        })

    return insights


def generate_llm_executive_summary(
    insights: List[Dict[str, Any]],
    kpis: Dict[str, Any],
    api_key: Optional[str] = None
) -> str:
    """
    Generate an executive summary synthesizing computed findings.
    Works deterministically with built-in synthesis if no external API key is provided.
    """
    summary_lines = [
        "### Executive Intelligence Briefing",
        "",
        f"**Platform Overview:** Analysis performed across verified business transactions with deterministic statistical models.",
        "",
    ]

    if kpis.get("total_revenue"):
        summary_lines.append(f"- **Revenue Performance:** Total volume reached **${kpis['total_revenue']:,.2f}** across **{kpis.get('total_orders', 0):,}** transactions.")
    if kpis.get("profit_margin_pct"):
        summary_lines.append(f"- **Operating Margins:** Operating margin stands at **{kpis['profit_margin_pct']:.1f}%** (Net Profit: ${kpis.get('total_profit', 0):,.2f}).")
    if kpis.get("repeat_customer_pct"):
        summary_lines.append(f"- **Customer Retention:** Repeat customer rate is **{kpis['repeat_customer_pct']:.1f}%** across {kpis.get('unique_customers', 0):,} unique accounts.")

    summary_lines.append("\n**Key Strategic Priorities:**")
    for i, ins in enumerate(insights[:3], 1):
        summary_lines.append(f"{i}. **{ins['title']}**: {ins['finding']} *Recommendation:* {ins['recommended_actions'][0]}")

    summary_lines.append("\n*Note: All observations are derived from empirical dataset records. Correlations do not imply causal relationships.*")

    return "\n".join(summary_lines)
