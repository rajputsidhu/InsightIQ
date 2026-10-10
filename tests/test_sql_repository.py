"""
Unit tests for SQL Repository and Safety Guards.
"""

import pandas as pd
import pytest
from database.connection import db_manager
from database.repository import SQLRepository


def test_sql_safety_validation():
    # Prohibited mutations
    assert SQLRepository.validate_query_safety("DROP TABLE active_dataset;")[0] is False
    assert SQLRepository.validate_query_safety("TRUNCATE TABLE active_dataset;")[0] is False
    assert SQLRepository.validate_query_safety("DELETE FROM active_dataset WHERE id = 1;")[0] is False
    assert SQLRepository.validate_query_safety("ALTER TABLE active_dataset ADD COLUMN x INT;")[0] is False
    assert SQLRepository.validate_query_safety("INSERT INTO active_dataset VALUES (1, 2);")[0] is False

    # Valid read-only queries
    assert SQLRepository.validate_query_safety("SELECT * FROM active_dataset LIMIT 10;")[0] is True
    assert SQLRepository.validate_query_safety("WITH cte AS (SELECT 1 AS val) SELECT * FROM cte;")[0] is True


def test_sql_execution_duckdb():
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "category": ["Tech", "Office", "Tech"],
        "amount": [100.0, 50.0, 200.0],
    })
    db_manager.register_dataframe("active_dataset", df)

    res_df, meta, err = SQLRepository.execute_query(
        "SELECT category, SUM(amount) AS total_amount FROM active_dataset GROUP BY category ORDER BY total_amount DESC"
    )

    assert err is None
    assert res_df is not None
    assert len(res_df) == 2
    assert res_df.iloc[0]["category"] == "Tech"
    assert res_df.iloc[0]["total_amount"] == 300.0
    assert meta["execution_time_ms"] >= 0
