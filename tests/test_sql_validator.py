"""
Unit tests for Safe SQL Validator (Workstream 2).
"""

import pytest
from services.sql_validator import SQLValidator


def test_valid_select_query():
    sql = "SELECT category, SUM(revenue) FROM active_dataset GROUP BY category ORDER BY 2 DESC;"
    is_safe, sanitized, err = SQLValidator.validate(sql)
    assert is_safe
    assert err is None
    assert "SELECT" in sanitized


def test_valid_cte_query():
    sql = """
    WITH monthly_sales AS (
        SELECT strftime(order_date, '%Y-%m') AS month, SUM(revenue) AS rev
        FROM active_dataset
        GROUP BY 1
    )
    SELECT month, rev FROM monthly_sales ORDER BY month;
    """
    is_safe, sanitized, err = SQLValidator.validate(sql)
    assert is_safe
    assert err is None


def test_block_drop_and_delete():
    for bad_sql in [
        "DROP TABLE active_dataset;",
        "DELETE FROM active_dataset WHERE id = 1;",
        "TRUNCATE TABLE active_dataset;",
        "ALTER TABLE active_dataset ADD COLUMN secret TEXT;",
        "INSERT INTO active_dataset VALUES (1, 2);",
        "UPDATE active_dataset SET revenue = 0;",
    ]:
        is_safe, _, err = SQLValidator.validate(bad_sql)
        assert not is_safe
        assert err is not None


def test_block_multi_statements():
    bad_sql = "SELECT * FROM active_dataset; DROP TABLE active_dataset;"
    is_safe, _, err = SQLValidator.validate(bad_sql)
    assert not is_safe
    assert "Multiple" in err or "Prohibited" in err


def test_block_unsafe_functions():
    bad_sql = "SELECT * FROM read_csv('secret.csv');"
    is_safe, _, err = SQLValidator.validate(bad_sql)
    assert not is_safe
    assert "Disallowed function" in err or "Access to table" in err


def test_enforce_row_limit():
    sql = "SELECT * FROM active_dataset"
    limited = SQLValidator.enforce_row_limit(sql, max_rows=100)
    assert "LIMIT 100" in limited

    already_limited = "SELECT * FROM active_dataset LIMIT 25"
    limited2 = SQLValidator.enforce_row_limit(already_limited, max_rows=100)
    assert "LIMIT 25" in limited2
