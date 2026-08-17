"""
Data Quality and Quarantine API Endpoints.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from datapulse.warehouse.db import get_db_session
from datapulse.storage.factory import get_storage_client
from datapulse.config import settings

router = APIRouter(prefix="/quality", tags=["Data Quality"])


@router.get("/metrics")
def get_quality_metrics(db: Session = Depends(get_db_session)) -> List[Dict[str, Any]]:
    """Retrieves all data quality checks and pass rates from audit table."""
    try:
        rows = db.execute(
            text("SELECT run_id, check_name, dataset, status, records_checked, records_passed, records_failed, pass_rate, evaluated_at FROM data_quality_audit ORDER BY evaluated_at DESC LIMIT 50;")
        ).mappings().all()
        return [dict(r) for r in rows]
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return []


@router.get("/trends")
def get_quality_trends(db: Session = Depends(get_db_session)) -> List[Dict[str, Any]]:
    """Retrieves historical pipeline quality trends from analytical mart."""
    try:
        rows = db.execute(
            text("SELECT run_id, audit_date, checks_executed, total_records_checked, total_records_passed, total_records_failed, avg_check_pass_rate FROM v_mart_quality_trends LIMIT 20;")
        ).mappings().all()
        return [dict(r) for r in rows]
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return []


@router.get("/quarantine")
def get_quarantine_records(
    dataset: str = Query(default="orders", description="Dataset name (orders, customers, products)"),
    limit: int = Query(default=50, ge=1, le=500),
) -> Dict[str, Any]:
    """Reads quarantined invalid records from the quarantine data zone."""
    storage = get_storage_client()
    target_csv = f"{settings.QUARANTINE_DATA_PATH}/quarantine_{dataset}.csv"

    if not storage.exists(target_csv):
        return {"dataset": dataset, "total_quarantined": 0, "records": []}

    try:
        df = storage.read_csv(target_csv)
        total = len(df)
        records = df.head(limit).to_dict(orient="records")
        return {
            "dataset": dataset,
            "total_quarantined": total,
            "showing": len(records),
            "records": records,
        }
    except Exception as e:
        return {"dataset": dataset, "error": str(e), "records": []}
