"""
AST-Based Safe SQL Validation Layer for InsightIQ.
Treats all user or LLM-generated SQL as untrusted input.
Enforces strict read-only queries, AST parsing via SQLGlot, table allowlisting,
forbidden function prevention, single-statement enforcement, and row limits.
"""

import re
from typing import Tuple, Optional, Set, List, Dict, Any

try:
    import sqlglot
    from sqlglot import exp
    HAS_SQLGLOT = True
except ImportError:
    HAS_SQLGLOT = False


class SQLValidator:
    """
    Validates SQL queries against strict security and structural safety policies.
    """

    FORBIDDEN_KEYWORDS = [
        r"\bDROP\b", r"\bTRUNCATE\b", r"\bDELETE\b", r"\bALTER\b",
        r"\bGRANT\b", r"\bREVOKE\b", r"\bINSERT\b", r"\bUPDATE\b",
        r"\bCREATE\b", r"\bATTACH\b", r"\bDETACH\b", r"\bCOPY\b",
        r"\bINSTALL\b", r"\bLOAD\b", r"\bEXPORT\b", r"\bIMPORT\b",
        r"\bPRAGMA\b", r"\bEXEC\b", r"\bEXECUTE\b", r"\bCALL\b"
    ]

    DISALLOWED_FUNCTIONS = {
        "read_csv", "read_csv_auto", "read_parquet", "read_json",
        "parquet_scan", "scan_parquet", "glob", "install", "load",
        "httpfs", "duckdb_settings", "system"
    }

    ALLOWED_TABLES = {"active_dataset", "active_table", "dataset"}

    @classmethod
    def validate(
        cls,
        sql_query: str,
        allowed_tables: Optional[Set[str]] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate SQL query string.
        Returns (is_valid, sanitized_sql, error_message).
        """
        if not sql_query or not sql_query.strip():
            return False, None, "SQL query cannot be empty."

        query = sql_query.strip()

        # 1. Strip comments
        clean_sql = re.sub(r"--.*", "", query)
        clean_sql = re.sub(r"/\*.*?\*/", "", clean_sql, flags=re.DOTALL).strip()

        # 2. Prevent multi-statement semicolon chaining
        # Remove trailing semicolon
        trimmed_semi = clean_sql.rstrip(";").strip()
        if ";" in trimmed_semi:
            return False, None, "Multiple SQL statements are strictly prohibited."

        # 3. Regex keyword screening
        for kw in cls.FORBIDDEN_KEYWORDS:
            if re.search(kw, trimmed_semi, re.IGNORECASE):
                kw_name = kw.replace(r"\b", "")
                return False, None, f"Prohibited SQL keyword detected: {kw_name}."

        # 4. AST parsing via SQLGlot if available
        if HAS_SQLGLOT:
            try:
                parsed_statements = sqlglot.parse(trimmed_semi, read="duckdb")
                if len(parsed_statements) > 1:
                    return False, None, "Multiple statements parsed; only single SELECT queries permitted."

                if not parsed_statements or parsed_statements[0] is None:
                    return False, None, "Failed to parse SQL statement."

                ast = parsed_statements[0]

                # Root node must be a SELECT or CTE Expression
                if not isinstance(ast, (exp.Select, exp.Union)):
                    return False, None, f"Query must be a SELECT or CTE statement (got {type(ast).__name__})."

                # Check for forbidden expressions
                for forbidden_type in (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter, exp.Command):
                    if list(ast.find_all(forbidden_type)):
                        return False, None, f"Operation type '{forbidden_type.__name__}' is strictly forbidden."

                # Check for disallowed functions
                for func in ast.find_all(exp.Anonymous):
                    fn_name = func.name.lower()
                    if fn_name in cls.DISALLOWED_FUNCTIONS:
                        return False, None, f"Disallowed function call detected: '{fn_name}'."

                for func in ast.find_all(exp.Func):
                    fn_name = func.key.lower() if hasattr(func, "key") else ""
                    if fn_name in cls.DISALLOWED_FUNCTIONS:
                        return False, None, f"Disallowed function call detected: '{fn_name}'."

                # Verify tables referenced
                valid_tables = allowed_tables or cls.ALLOWED_TABLES
                for table in ast.find_all(exp.Table):
                    t_name = table.name.lower()
                    # If query defines CTEs, allow CTE names as tables
                    cte_names = [cte.alias.lower() for cte in ast.find_all(exp.CTE) if cte.alias]
                    if t_name not in valid_tables and t_name not in cte_names:
                        return False, None, f"Access to table '{t_name}' is not permitted. Only active workspace datasets can be queried."

            except sqlglot.errors.ParseError as e:
                return False, None, f"SQL Syntax/Parse Error: {str(e)}"
            except Exception as e:
                return False, None, f"SQL Validation Error: {str(e)}"
        else:
            # Fallback simple grammar check
            upper_sql = trimmed_semi.upper()
            if not (upper_sql.startswith("SELECT") or upper_sql.startswith("WITH")):
                return False, None, "Query must start with SELECT or WITH."

        return True, trimmed_semi, None

    @classmethod
    def enforce_row_limit(cls, sql_query: str, max_rows: int = 500) -> str:
        """Ensure query includes a sensible row limit."""
        clean_q = sql_query.rstrip(";").strip()
        if not re.search(r"\bLIMIT\s+\d+", clean_q, re.IGNORECASE):
            return f"{clean_q} LIMIT {max_rows}"
        return clean_q
