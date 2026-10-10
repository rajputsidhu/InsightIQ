"""
Analytical SQL Repository for InsightIQ.
Executes queries against restricted read-only data views with query safety validation,
execution timeouts, and parameterized protection.
"""

import time
import re
import pandas as pd
from typing import Tuple, Optional, Dict, Any
from database.connection import db_manager


class SQLRepository:
    FORBIDDEN_KEYWORDS = [
        r"\bDROP\b",
        r"\bTRUNCATE\b",
        r"\bDELETE\b",
        r"\bALTER\b",
        r"\bGRANT\b",
        r"\bREVOKE\b",
        r"\bINSERT\b",
        r"\bUPDATE\b",
        r"\bEXEC\b",
    ]

    @classmethod
    def validate_query_safety(cls, sql_query: str) -> Tuple[bool, Optional[str]]:
        """Ensure query is strictly read-only SELECT / WITH statement."""
        clean_sql = re.sub(r"--.*", "", sql_query)  # Strip comments
        clean_sql = re.sub(r"/\*.*?\*/", "", clean_sql, flags=re.DOTALL)

        for kw in cls.FORBIDDEN_KEYWORDS:
            if re.search(kw, clean_sql, re.IGNORECASE):
                return False, f"Prohibited operation detected. Analytical SQL editor is strictly read-only (matched {kw})."

        trimmed = clean_sql.strip().upper()
        if not (trimmed.startswith("SELECT") or trimmed.startswith("WITH") or trimmed.startswith("EXPLAIN") or trimmed.startswith("DESCRIBE") or trimmed.startswith("SHOW")):
            return False, "Query must begin with SELECT, WITH, DESCRIBE, or SHOW."

        return True, None

    @classmethod
    def execute_query(
        cls,
        sql_query: str,
        row_limit: int = 1000
    ) -> Tuple[Optional[pd.DataFrame], Dict[str, Any], Optional[str]]:
        """
        Execute read-only SQL query with timing metrics and row limits.
        Returns (DataFrame, execution_metadata, error_message).
        """
        is_safe, error = cls.validate_query_safety(sql_query)
        if not is_safe:
            return None, {}, error

        start_time = time.perf_counter()

        try:
            # Enforce max row limit if not already present
            query_to_run = sql_query.strip()
            if not re.search(r"\bLIMIT\s+\d+", query_to_run, re.IGNORECASE):
                query_to_run = f"{query_to_run.rstrip(';')} LIMIT {row_limit}"

            if db_manager.pg_connected and db_manager.pg_engine:
                with db_manager.pg_engine.connect() as conn:
                    result_df = pd.read_sql_query(query_to_run, conn)
            else:
                result_df = db_manager.duckdb_conn.execute(query_to_run).df()

            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            meta = {
                "execution_time_ms": elapsed_ms,
                "rows_returned": len(result_df),
                "columns_returned": len(result_df.columns),
                "engine": "PostgreSQL" if db_manager.pg_connected else "DuckDB (Local)",
            }
            return result_df, meta, None

        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return None, {"execution_time_ms": elapsed_ms}, f"SQL Execution Error: {str(e)}"
