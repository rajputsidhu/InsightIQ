"""
Business Metrics & KPI Computation Engine for InsightIQ.
Calculates executive metrics, revenue trends, product margins, and customer retention metrics.
Strictly relies on actual available data and never fabricates missing figures.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple


def infer_business_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """
    Intelligently infer business column roles from DataFrame schema.
    Returns mapping of standardized semantic roles to actual column names.
    """
    if df is None or df.empty:
        return {}

    cols = list(df.columns)
    col_lower = {c: str(c).lower().replace(" ", "_").replace("-", "_") for c in cols}

    mapping = {
        "revenue": None,
        "profit": None,
        "date": None,
        "customer_id": None,
        "order_id": None,
        "product": None,
        "category": None,
        "quantity": None,
        "region": None,
        "cost": None,
    }

    # Revenue candidates
    rev_candidates = ["net_revenue", "gross_revenue", "revenue", "sales", "total_amount", "amount", "total_price", "mrr", "charges"]
    for cand in rev_candidates:
        for c, norm in col_lower.items():
            if cand == norm or (cand in norm and pd.api.types.is_numeric_dtype(df[c])):
                mapping["revenue"] = c
                break
        if mapping["revenue"]:
            break

    # Profit candidates
    profit_candidates = ["profit", "net_profit", "margin_amount", "earnings"]
    for cand in profit_candidates:
        for c, norm in col_lower.items():
            if cand in norm and pd.api.types.is_numeric_dtype(df[c]):
                mapping["profit"] = c
                break
        if mapping["profit"]:
            break

    # Date candidates
    date_candidates = ["order_date", "transaction_date", "invoice_date", "date", "created_at", "timestamp", "period"]
    for cand in date_candidates:
        for c, norm in col_lower.items():
            if cand in norm:
                mapping["date"] = c
                break
        if mapping["date"]:
            break

    # Customer ID candidates
    cust_candidates = ["customer_id", "client_id", "user_id", "account_id", "cust_id", "buyer_id"]
    for cand in cust_candidates:
        for c, norm in col_lower.items():
            if cand in norm:
                mapping["customer_id"] = c
                break
        if mapping["customer_id"]:
            break

    # Order ID candidates
    order_candidates = ["order_id", "transaction_id", "invoice_id", "id", "order_number"]
    for cand in order_candidates:
        for c, norm in col_lower.items():
            if cand in norm:
                mapping["order_id"] = c
                break
        if mapping["order_id"]:
            break

    # Product candidates
    prod_candidates = ["product_name", "product", "item_name", "item", "sku", "service"]
    for cand in prod_candidates:
        for c, norm in col_lower.items():
            if cand in norm:
                mapping["product"] = c
                break
        if mapping["product"]:
            break

    # Category candidates
    cat_candidates = ["category", "product_category", "department", "segment", "type", "industry"]
    for cand in cat_candidates:
        for c, norm in col_lower.items():
            if cand in norm:
                mapping["category"] = c
                break
        if mapping["category"]:
            break

    # Quantity candidates
    qty_candidates = ["quantity", "qty", "units", "items_count"]
    for cand in qty_candidates:
        for c, norm in col_lower.items():
            if cand in norm and pd.api.types.is_numeric_dtype(df[c]):
                mapping["quantity"] = c
                break
        if mapping["quantity"]:
            break

    # Region candidates
    region_candidates = ["region", "country", "state", "territory", "city", "market"]
    for cand in region_candidates:
        for c, norm in col_lower.items():
            if cand in norm:
                mapping["region"] = c
                break
        if mapping["region"]:
            break

    return mapping


def calculate_executive_kpis(df: pd.DataFrame, col_map: Optional[Dict[str, Optional[str]]] = None) -> Dict[str, Any]:
    """
    Compute executive summary KPIs from the dataset based on available columns.
    """
    if df is None or df.empty:
        return {"available": False, "reason": "No data loaded."}

    if col_map is None:
        col_map = infer_business_columns(df)

    res: Dict[str, Any] = {
        "available": True,
        "total_revenue": None,
        "total_orders": None,
        "unique_customers": None,
        "average_order_value": None,
        "total_profit": None,
        "profit_margin_pct": None,
        "repeat_customer_pct": None,
        "revenue_growth_pct": None,
        "date_range": None,
        "unsupported_metrics": [],
    }

    # Total Orders
    if col_map.get("order_id") and col_map["order_id"] in df.columns:
        res["total_orders"] = int(df[col_map["order_id"]].nunique())
    else:
        res["total_orders"] = len(df)

    # Unique Customers
    if col_map.get("customer_id") and col_map["customer_id"] in df.columns:
        res["unique_customers"] = int(df[col_map["customer_id"]].nunique())
        
        # Repeat customer rate
        orders_per_cust = df.groupby(col_map["customer_id"]).size()
        repeat_count = int((orders_per_cust > 1).sum())
        total_unique = len(orders_per_cust)
        res["repeat_customer_pct"] = round((repeat_count / total_unique) * 100, 1) if total_unique > 0 else 0.0
    else:
        res["unsupported_metrics"].append("Unique Customers & Repeat Rate (requires Customer ID column)")

    # Revenue
    rev_col = col_map.get("revenue")
    if rev_col and rev_col in df.columns:
        total_rev = float(df[rev_col].dropna().sum())
        res["total_revenue"] = round(total_rev, 2)

        # Average Order Value
        if res["total_orders"] and res["total_orders"] > 0:
            res["average_order_value"] = round(total_rev / res["total_orders"], 2)
    else:
        res["unsupported_metrics"].append("Total Revenue & AOV (requires Numeric Revenue/Sales column)")

    # Profit & Margin
    profit_col = col_map.get("profit")
    if profit_col and profit_col in df.columns:
        total_prof = float(df[profit_col].dropna().sum())
        res["total_profit"] = round(total_prof, 2)
        if res["total_revenue"] and res["total_revenue"] > 0:
            res["profit_margin_pct"] = round((total_prof / res["total_revenue"]) * 100, 2)
    else:
        res["unsupported_metrics"].append("Total Profit & Profit Margin (requires Profit column)")

    # Time-based growth calculation
    date_col = col_map.get("date")
    if date_col and date_col in df.columns and rev_col and rev_col in df.columns:
        try:
            temp_df = df[[date_col, rev_col]].copy()
            temp_df["dt"] = pd.to_datetime(temp_df[date_col], errors="coerce")
            temp_df = temp_df.dropna(subset=["dt", rev_col])
            
            if len(temp_df) > 10:
                min_dt = temp_df["dt"].min()
                max_dt = temp_df["dt"].max()
                res["date_range"] = f"{min_dt.strftime('%b %d, %Y')} – {max_dt.strftime('%b %d, %Y')}"
                
                # Compare latest 30 days or last half vs previous half
                midpoint = min_dt + (max_dt - min_dt) / 2
                prior_rev = temp_df[temp_df["dt"] < midpoint][rev_col].sum()
                recent_rev = temp_df[temp_df["dt"] >= midpoint][rev_col].sum()

                if prior_rev > 0:
                    growth = ((recent_rev - prior_rev) / prior_rev) * 100
                    res["revenue_growth_pct"] = round(growth, 1)
        except Exception:
            pass

    return res


def compute_category_breakdown(df: pd.DataFrame, col_map: Dict[str, Optional[str]]) -> pd.DataFrame:
    """Aggregate revenue and profit by product category."""
    cat_col = col_map.get("category")
    rev_col = col_map.get("revenue")
    profit_col = col_map.get("profit")

    if not cat_col or cat_col not in df.columns or not rev_col or rev_col not in df.columns:
        return pd.DataFrame()

    agg_dict = {rev_col: "sum"}
    if profit_col and profit_col in df.columns:
        agg_dict[profit_col] = "sum"

    cat_df = df.groupby(cat_col).agg(agg_dict).reset_index()
    cat_df.rename(columns={cat_col: "Category", rev_col: "Revenue"}, inplace=True)
    
    if profit_col and profit_col in df.columns:
        cat_df.rename(columns={profit_col: "Profit"}, inplace=True)
        cat_df["Margin %"] = (cat_df["Profit"] / cat_df["Revenue"] * 100).round(1)

    cat_df = cat_df.sort_values(by="Revenue", ascending=False).reset_index(drop=True)
    return cat_df


def compute_top_products(df: pd.DataFrame, col_map: Dict[str, Optional[str]], top_n: int = 8) -> pd.DataFrame:
    """Aggregate top performing products by revenue, orders, and profit."""
    prod_col = col_map.get("product")
    rev_col = col_map.get("revenue")
    profit_col = col_map.get("profit")
    qty_col = col_map.get("quantity")

    if not prod_col or prod_col not in df.columns or not rev_col or rev_col not in df.columns:
        return pd.DataFrame()

    agg_dict = {rev_col: ["sum", "count"]}
    if qty_col and qty_col in df.columns:
        agg_dict[qty_col] = "sum"
    if profit_col and profit_col in df.columns:
        agg_dict[profit_col] = "sum"

    prod_df = df.groupby(prod_col).agg(agg_dict)
    
    # Flatten column multi-index
    cols = ["Revenue", "Orders"]
    if qty_col and qty_col in df.columns:
        cols.append("Units_Sold")
    if profit_col and profit_col in df.columns:
        cols.append("Profit")
        
    prod_df.columns = cols
    prod_df = prod_df.reset_index().rename(columns={prod_col: "Product"})
    
    if "Profit" in prod_df.columns:
        prod_df["Margin %"] = (prod_df["Profit"] / prod_df["Revenue"] * 100).round(1)

    prod_df = prod_df.sort_values(by="Revenue", ascending=False).head(top_n).reset_index(drop=True)
    return prod_df


def compute_time_series_aggregation(df: pd.DataFrame, col_map: Dict[str, Optional[str]], freq: str = "MS") -> pd.DataFrame:
    """Aggregate revenue and profit over time (Monthly / Weekly / Daily)."""
    date_col = col_map.get("date")
    rev_col = col_map.get("revenue")
    profit_col = col_map.get("profit")

    if not date_col or date_col not in df.columns or not rev_col or rev_col not in df.columns:
        return pd.DataFrame()

    temp_df = df.copy()
    temp_df["dt"] = pd.to_datetime(temp_df[date_col], errors="coerce")
    temp_df[rev_col] = pd.to_numeric(temp_df[rev_col], errors="coerce")
    if profit_col and profit_col in temp_df.columns:
        temp_df[profit_col] = pd.to_numeric(temp_df[profit_col], errors="coerce")

    temp_df = temp_df.dropna(subset=["dt", rev_col])
    if temp_df.empty:
        return pd.DataFrame()

    # Create robust period grouping format
    if freq == "D":
        temp_df["period_str"] = temp_df["dt"].dt.strftime("%Y-%m-%d")
        temp_df["period_dt"] = pd.to_datetime(temp_df["period_str"])
    elif freq == "W":
        temp_df["period_str"] = temp_df["dt"].dt.strftime("%Y-W%U")
        temp_df["period_dt"] = temp_df["dt"].dt.to_period("W").dt.start_time
    else:  # Monthly default
        temp_df["period_str"] = temp_df["dt"].dt.strftime("%Y-%m")
        temp_df["period_dt"] = pd.to_datetime(temp_df["period_str"] + "-01")

    agg_dict = {rev_col: "sum"}
    if profit_col and profit_col in temp_df.columns:
        agg_dict[profit_col] = "sum"

    ts_df = temp_df.groupby(["period_str", "period_dt"], as_index=False).agg(agg_dict)
    ts_df = ts_df.sort_values(by="period_dt").reset_index(drop=True)

    ts_df.rename(columns={"period_dt": "Date", "period_str": "Date_Str", rev_col: "Revenue"}, inplace=True)
    if profit_col and profit_col in ts_df.columns:
        ts_df.rename(columns={profit_col: "Profit"}, inplace=True)

    return ts_df
