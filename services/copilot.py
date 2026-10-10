"""
Conversational Analytics Copilot Engine for InsightIQ.
Coordinates natural-language understanding, safe AST SQL validation,
sandboxed query execution, automatic visualization, and evidence-grounded responses.
"""

import time
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List

from services.sql_validator import SQLValidator
from services.llm_provider import get_llm_provider
from services.chart_recommender import recommend_and_build_chart
from database.connection import db_manager


class AnalyticsCopilotService:
    """
    Orchestrates the safe Ask InsightIQ copilot workflow.
    """

    def __init__(self):
        self.provider = get_llm_provider()

    def get_schema_summary(self, df: pd.DataFrame, table_name: str = "active_dataset") -> Dict[str, Any]:
        """Produce compact schema descriptor for query planning."""
        if df is None or df.empty:
            return {"table_name": table_name, "columns": [], "row_count": 0}

        clean_cols = [str(c).strip().replace(" ", "_").replace("-", "_").replace(".", "_") for c in df.columns]
        types = {c: str(df[orig].dtype) for c, orig in zip(clean_cols, df.columns)}

        return {
            "table_name": table_name,
            "columns": clean_cols,
            "dtypes": types,
            "row_count": len(df),
        }

    def ask(
        self,
        question: str,
        df: pd.DataFrame,
        max_rows: int = 200
    ) -> Dict[str, Any]:
        """
        Execute end-to-end copilot query pipeline.
        """
        if not question or not question.strip():
            return {
                "success": False,
                "error": "Please provide a valid business question.",
                "response_text": "Please enter a question to analyze your data.",
            }

        if df is None or df.empty:
            return {
                "success": False,
                "error": "No active dataset loaded in workspace.",
                "response_text": "Please load a dataset first from the sidebar.",
            }

        start_time = time.perf_counter()

        # Step 1: Ensure DataFrame is registered with DuckDB
        db_manager.register_dataframe("active_dataset", df)

        # Step 2: Schema discovery
        schema_info = self.get_schema_summary(df)

        # Step 3: SQL generation via provider
        plan = self.provider.generate_sql_and_explanation(question, schema_info)
        raw_sql = plan.get("sql", "")

        if not raw_sql:
            return {
                "success": False,
                "error": "Unable to map question to an analytical SQL query.",
                "response_text": "The engine could not determine an appropriate analytical query for this question.",
            }

        # Step 4: AST-based SQL Validation & Security Enforcement
        is_safe, sanitized_sql, val_err = SQLValidator.validate(raw_sql)
        if not is_safe:
            return {
                "success": False,
                "error": f"Security Validation Blocked Query: {val_err}",
                "blocked_sql": raw_sql,
                "response_text": f"Query was rejected by security guardrails: {val_err}",
            }

        query_to_run = SQLValidator.enforce_row_limit(sanitized_sql, max_rows=max_rows)

        # Step 5: Sandboxed execution in DuckDB
        try:
            exec_start = time.perf_counter()
            result_df = db_manager.duckdb_conn.execute(query_to_run).df()
            exec_time_ms = round((time.perf_counter() - exec_start) * 1000, 2)
        except Exception as e:
            return {
                "success": False,
                "error": f"Database Execution Error: {str(e)}",
                "sql": query_to_run,
                "response_text": f"Error running analytical query: {str(e)}",
            }

        # Step 6: Result validation
        total_pipeline_ms = round((time.perf_counter() - start_time) * 1000, 2)
        is_empty = result_df.empty

        # Step 7: Automatic Chart Recommendation
        fig, chart_type = recommend_and_build_chart(result_df, title=f"Analysis: {question[:40]}")

        # Step 8: Evidence-grounded synthesis
        explanation = self._synthesize_evidence_response(question, result_df, plan.get("intent", "Analysis"))

        return {
            "success": True,
            "question": question,
            "sql": query_to_run,
            "result_df": result_df,
            "chart_fig": fig,
            "chart_type": chart_type,
            "response_text": explanation,
            "row_count": len(result_df),
            "execution_time_ms": exec_time_ms,
            "total_time_ms": total_pipeline_ms,
            "provider_name": plan.get("provider", "Deterministic Analytics Engine"),
        }

    def _synthesize_evidence_response(
        self,
        question: str,
        df: pd.DataFrame,
        intent: str
    ) -> str:
        """Synthesize natural-language summary grounded strictly in returned data."""
        if df.empty:
            return "Query executed successfully, but returned zero matching records."

        n_rows = len(df)
        cols = list(df.columns)

        # Single row scalar / aggregate
        if n_rows == 1:
            metrics_summary = []
            for col in cols:
                val = df[col].iloc[0]
                if isinstance(val, (int, float, np.number)):
                    val_str = f"${val:,.2f}" if "rev" in col.lower() or "profit" in col.lower() or "value" in col.lower() else f"{val:,.2f}"
                else:
                    val_str = str(val)
                metrics_summary.append(f"**{col.replace('_', ' ')}**: {val_str}")
            return f"Computed metrics for your inquiry: {', '.join(metrics_summary)}."

        # Multi-row result: highlight leader
        first_col, second_col = cols[0], cols[1] if len(cols) > 1 else cols[0]
        top_item = df[first_col].iloc[0]
        top_val = df[second_col].iloc[0] if len(cols) > 1 else ""

        if isinstance(top_val, (int, float, np.number)):
            top_val_str = f"${top_val:,.2f}" if "rev" in second_col.lower() or "profit" in second_col.lower() else f"{top_val:,.2f}"
            leader_note = f" Top entry is **{top_item}** with **{top_val_str}** in {second_col.replace('_', ' ')}."
        else:
            leader_note = f" Top entry is **{top_item}**."

        return f"Returned **{n_rows:,} records** for *'{intent}'*.{leader_note}"
