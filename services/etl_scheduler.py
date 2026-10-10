"""
Demonstrable Scheduled ETL Ingestion Architecture for InsightIQ.
Tracks ingestion pipelines, executes idempotent data refreshes, audits data quality,
and logs execution telemetry (timestamps, row counts, and health scores).
"""

import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd

from services.data_validation import compute_data_quality_report
from services.data_loader import get_demo_dataset
from database.connection import db_manager


class ETLSchedulerService:
    """
    Demonstrates scheduled and on-demand automated data ingestion with idempotent validation.
    """

    def __init__(self):
        self.pipeline_history: List[Dict[str, Any]] = []
        self._init_default_history()

    def _init_default_history(self):
        """Populate initial realistic run logs for dashboard presentation."""
        self.pipeline_history = [
            {
                "run_id": "RUN-20261009-0801",
                "source": "Demo E-Commerce Orders",
                "status": "SUCCESS",
                "trigger": "Scheduled (Daily 08:00)",
                "start_time": "2026-10-09 08:00:01",
                "end_time": "2026-10-09 08:00:04",
                "duration_ms": 3120,
                "rows_ingested": 1250,
                "health_score": 98.5,
                "message": "Automated daily ingestion completed with 0 duplicate rows."
            },
            {
                "run_id": "RUN-20261008-0801",
                "source": "Demo E-Commerce Orders",
                "status": "SUCCESS",
                "trigger": "Scheduled (Daily 08:00)",
                "start_time": "2026-10-08 08:00:01",
                "end_time": "2026-10-08 08:00:03",
                "duration_ms": 2890,
                "rows_ingested": 1250,
                "health_score": 98.5,
                "message": "Daily sync verified."
            }
        ]

    def trigger_pipeline_sync(
        self,
        source_name: str,
        trigger_mode: str = "Manual On-Demand"
    ) -> Dict[str, Any]:
        """
        Execute an end-to-end ingestion cycle: fetch, validate, score, and register.
        """
        start_time = time.perf_counter()
        run_id = f"RUN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        start_dt_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Ingestion source mapping
        if "ecommerce" in source_name.lower():
            df = get_demo_dataset("ecommerce")
        elif "churn" in source_name.lower():
            df = get_demo_dataset("churn")
        elif "saas" in source_name.lower():
            df = get_demo_dataset("saas")
        else:
            df = get_demo_dataset("ecommerce")

        if df is None or df.empty:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            record = {
                "run_id": run_id,
                "source": source_name,
                "status": "FAILED",
                "trigger": trigger_mode,
                "start_time": start_dt_str,
                "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "duration_ms": duration_ms,
                "rows_ingested": 0,
                "health_score": 0.0,
                "message": "Source dataset returned zero records."
            }
            self.pipeline_history.insert(0, record)
            return record

        # Run automated quality audit
        quality_report = compute_data_quality_report(df)
        score = quality_report.get("overall_score", 100.0)

        # Idempotent registration into DuckDB
        db_manager.register_dataframe("active_dataset", df)

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        end_dt_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        record = {
            "run_id": run_id,
            "source": source_name,
            "status": "SUCCESS",
            "trigger": trigger_mode,
            "start_time": start_dt_str,
            "end_time": end_dt_str,
            "duration_ms": duration_ms,
            "rows_ingested": len(df),
            "health_score": round(score, 1),
            "message": f"Successfully ingested {len(df):,} records (Data Health: {score:.1f}/100)."
        }

        self.pipeline_history.insert(0, record)
        return record

    def get_history(self) -> List[Dict[str, Any]]:
        return self.pipeline_history
