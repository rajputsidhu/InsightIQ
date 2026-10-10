"""
Database Connection Manager for InsightIQ.
Provides high-performance analytical execution via DuckDB (local analytical database)
and seamless PostgreSQL connectivity when configured via environment variables.
"""

import os
import duckdb
from typing import Tuple, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


class DatabaseManager:
    def __init__(self):
        self.duckdb_conn = duckdb.connect(database=":memory:")
        self.pg_engine: Optional[Engine] = None
        self.pg_connected = False
        self._init_postgres()

    def _init_postgres(self):
        """Attempt PostgreSQL connection from environment variables if present."""
        pg_host = os.environ.get("POSTGRES_HOST")
        pg_port = os.environ.get("POSTGRES_PORT", "5432")
        pg_db = os.environ.get("POSTGRES_DB")
        pg_user = os.environ.get("POSTGRES_USER")
        pg_pass = os.environ.get("POSTGRES_PASSWORD")

        if pg_host and pg_db and pg_user:
            try:
                conn_str = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
                self.pg_engine = create_engine(conn_str, pool_pre_ping=True, connect_args={"connect_timeout": 3})
                with self.pg_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                self.pg_connected = True
            except Exception:
                self.pg_connected = False
                self.pg_engine = None
        else:
            self.pg_connected = False
            self.pg_engine = None

    def get_status(self) -> dict:
        """Return clear database connection diagnostics."""
        return {
            "mode": "PostgreSQL (Enterprise Storage)" if self.pg_connected else "DuckDB (In-Memory High-Speed Engine)",
            "is_postgres": self.pg_connected,
            "engine_name": "PostgreSQL 15+" if self.pg_connected else f"DuckDB v{duckdb.__version__}",
            "is_live": True,
            "description": (
                "Connected to remote PostgreSQL cluster."
                if self.pg_connected
                else "Operating in high-speed local analytical demonstration mode via DuckDB. Full analytical SQL syntax supported."
            )
        }

    def register_dataframe(self, table_name: str, df: Any):
        """Register a pandas DataFrame as a queryable SQL table in DuckDB."""
        if df is not None and not df.empty:
            # Replace spaces and hyphens in column names with underscores for clean SQL execution
            clean_df = df.copy()
            clean_df.columns = [str(c).strip().replace(" ", "_").replace("-", "_").replace(".", "_") for c in clean_df.columns]
            self.duckdb_conn.register(table_name, clean_df)


# Global singleton instance
db_manager = DatabaseManager()
