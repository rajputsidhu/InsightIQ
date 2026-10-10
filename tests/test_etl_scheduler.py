"""
Unit tests for Scheduled ETL Ingestion Architecture (Workstream 5).
"""

import pytest
from services.etl_scheduler import ETLSchedulerService


def test_etl_scheduler_sync():
    svc = ETLSchedulerService()
    initial_count = len(svc.get_history())

    res = svc.trigger_pipeline_sync("Demo E-Commerce Orders", trigger_mode="Test Run")

    assert res["status"] == "SUCCESS"
    assert res["rows_ingested"] > 0
    assert res["health_score"] > 80.0
    assert len(svc.get_history()) == initial_count + 1


def test_etl_scheduler_history():
    svc = ETLSchedulerService()
    history = svc.get_history()
    assert len(history) >= 2
    assert "run_id" in history[0]
    assert "status" in history[0]
