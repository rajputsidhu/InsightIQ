"""
Unified Database Connector Architecture for InsightIQ.
Provides standardized interface for querying, schema inspection, and previewing
across SQLite, DuckDB, PostgreSQL, and cloud warehouse stubs.
"""

import os
import sqlite3
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod


class BaseDataConnector(ABC):
    """Abstract base class for all InsightIQ data sources."""

    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """Verify network/file accessibility and authentication."""
        pass

    @abstractmethod
    def list_tables(self) -> List[str]:
        """Enumerate queryable tables in the catalog."""
        pass

    @abstractmethod
    def get_schema(self, table_name: str) -> Dict[str, str]:
        """Return mapping of column name to data type."""
        pass

    @abstractmethod
    def preview_data(self, table_name: str, limit: int = 20) -> pd.DataFrame:
        """Fetch read-only preview sample."""
        pass

    @abstractmethod
    def close(self):
        """Release underlying connections and resources."""
        pass


class SQLiteConnector(BaseDataConnector):
    """Local relational database connector (SQLite)."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None

    def _get_connection(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return self._conn

    def test_connection(self) -> Tuple[bool, str]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            return True, f"Successfully connected to SQLite database at '{self.db_path}'."
        except Exception as e:
            return False, f"SQLite connection failed: {str(e)}"

    def list_tables(self) -> List[str]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            return [row[0] for row in cursor.fetchall()]
        except Exception:
            return []

    def get_schema(self, table_name: str) -> Dict[str, str]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name});")
            rows = cursor.fetchall()
            return {row[1]: row[2] for row in rows}
        except Exception:
            return {}

    def preview_data(self, table_name: str, limit: int = 20) -> pd.DataFrame:
        try:
            conn = self._get_connection()
            return pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {limit};", conn)
        except Exception:
            return pd.DataFrame()

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None


class DuckDBConnector(BaseDataConnector):
    """In-memory or persistent columnar DuckDB connector."""

    def __init__(self, database: str = ":memory:"):
        import duckdb
        self.database = database
        self.conn = duckdb.connect(database=database)

    def test_connection(self) -> Tuple[bool, str]:
        try:
            self.conn.execute("SELECT 1;").fetchone()
            return True, f"DuckDB connection active ({self.database})."
        except Exception as e:
            return False, f"DuckDB error: {str(e)}"

    def list_tables(self) -> List[str]:
        try:
            res = self.conn.execute("SHOW TABLES;").fetchall()
            return [r[0] for r in res]
        except Exception:
            return []

    def get_schema(self, table_name: str) -> Dict[str, str]:
        try:
            df = self.conn.execute(f"DESCRIBE {table_name};").df()
            return dict(zip(df["column_name"], df["column_type"]))
        except Exception:
            return {}

    def preview_data(self, table_name: str, limit: int = 20) -> pd.DataFrame:
        try:
            return self.conn.execute(f"SELECT * FROM {table_name} LIMIT {limit};").df()
        except Exception:
            return pd.DataFrame()

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass


class CloudConnectorStub(BaseDataConnector):
    """
    Standardized adapter for cloud warehouses (Snowflake, BigQuery, Redshift).
    Provides clear setup diagnostics when drivers/credentials are pending.
    """

    def __init__(self, provider_name: str, config: Dict[str, Any]):
        self.provider_name = provider_name
        self.config = config

    def test_connection(self) -> Tuple[bool, str]:
        required_keys = {
            "Snowflake": ["account", "warehouse", "database", "schema", "user"],
            "BigQuery": ["project_id", "dataset"],
            "Redshift": ["host", "port", "database", "user"]
        }.get(self.provider_name, ["host", "database"])

        missing = [k for k in required_keys if not self.config.get(k)]
        if missing:
            return False, f"{self.provider_name} configuration missing required parameters: {', '.join(missing)}."

        return False, f"{self.provider_name} driver not configured in current environment. Please install optional connector driver."

    def list_tables(self) -> List[str]:
        return []

    def get_schema(self, table_name: str) -> Dict[str, str]:
        return {}

    def preview_data(self, table_name: str, limit: int = 20) -> pd.DataFrame:
        return pd.DataFrame()

    def close(self):
        pass
