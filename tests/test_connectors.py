"""
Unit tests for Database Connectors (Workstream 5).
"""

import pytest
import sqlite3
import os
import tempfile
import pandas as pd
from database.connectors import SQLiteConnector, DuckDBConnector, CloudConnectorStub


def test_duckdb_connector():
    conn = DuckDBConnector()
    ok, msg = conn.test_connection()
    assert ok
    assert "DuckDB" in msg

    # Create dummy table
    conn.conn.execute("CREATE TABLE test_tbl (id INT, val TEXT);")
    conn.conn.execute("INSERT INTO test_tbl VALUES (1, 'InsightIQ');")

    tables = conn.list_tables()
    assert "test_tbl" in tables

    schema = conn.get_schema("test_tbl")
    assert "id" in schema

    preview = conn.preview_data("test_tbl")
    assert len(preview) == 1
    assert preview["val"].iloc[0] == "InsightIQ"
    conn.close()


def test_sqlite_connector():
    # Use temporary file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    try:
        raw_conn = sqlite3.connect(db_path)
        raw_conn.execute("CREATE TABLE employees (emp_id INT, name TEXT);")
        raw_conn.execute("INSERT INTO employees VALUES (101, 'Ada Lovelace');")
        raw_conn.commit()
        raw_conn.close()

        connector = SQLiteConnector(db_path)
        ok, msg = connector.test_connection()
        assert ok
        assert "Successfully" in msg

        tables = connector.list_tables()
        assert "employees" in tables

        preview = connector.preview_data("employees")
        assert len(preview) == 1
        assert preview["name"].iloc[0] == "Ada Lovelace"
        connector.close()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_cloud_connector_stub():
    stub = CloudConnectorStub("Snowflake", {"account": "test_acc"})
    ok, msg = stub.test_connection()
    assert not ok
    assert "missing required parameters" in msg
