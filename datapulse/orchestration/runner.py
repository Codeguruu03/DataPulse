"""
Standalone Pipeline Orchestrator for DataPulse.
Executes the identical multi-stage DAG task sequence locally with telemetry, failure handling, and circuit breaking.
"""

import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from datapulse.config import settings
from datapulse.generator.generator import DataPulseGenerator
from datapulse.quality.gate import DataQualityGate
from datapulse.transforms.pipeline import LakehouseTransformPipeline
from datapulse.warehouse.loader import WarehouseLoader
from datapulse.utils.logger import get_logger

logger = get_logger("datapulse.orchestration.runner")


class PipelineRunner:
    """Orchestrates end-to-end DataPulse runs with automated data quality gates and circuit breaking."""

    def __init__(
        self,
        quality_threshold: Optional[float] = None,
        auto_generate: bool = True,
        anomaly_rate: float = 0.05,
    ):
        self.threshold = quality_threshold or settings.QUALITY_THRESHOLD_PERCENT
        self.auto_generate = auto_generate
        self.anomaly_rate = anomaly_rate

    def run(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes complete pipeline:
        1. Ingest / Generate Raw Datasets
        2. Evaluate Quality Gate & Quarantine Bad Data
        3. Threshold Circuit-Breaker Check
        4. Lakehouse Parquet Transformation & Partitioning
        5. Star Schema Warehouse Loading
        """
        batch_id = run_id or f"pipe-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"
        start_time = time.time()

        logger.info(f"============================================================")
        logger.info(f"Starting DataPulse Orchestration Run [{batch_id}]")
        logger.info(f"Quality Threshold: {self.threshold}% | Anomaly Rate: {self.anomaly_rate * 100}%")
        logger.info(f"============================================================")

        run_result = {
            "run_id": batch_id,
            "start_time": datetime.utcnow().isoformat(),
            "status": "RUNNING",
            "stages": {},
        }

        # Stage 1: Ingestion / Generation
        logger.info(">>> [Stage 1/5] Ingestion & Raw Staging...")
        t0 = time.time()
        if self.auto_generate:
            gen = DataPulseGenerator(anomaly_rate=self.anomaly_rate)
            c, p, o = gen.generate_all_and_save()
            run_result["stages"]["ingestion"] = {
                "status": "SUCCESS",
                "duration_sec": round(time.time() - t0, 2),
                "paths": {"customers": str(c), "products": str(p), "orders": str(o)},
            }
        else:
            run_result["stages"]["ingestion"] = {
                "status": "SKIPPED_EXISTING",
                "duration_sec": round(time.time() - t0, 2),
            }

        # Stage 2: Quality Gate Evaluation
        logger.info(">>> [Stage 2/5] Data Quality Gate Evaluation...")
        t1 = time.time()
        gate = DataQualityGate(quality_threshold=self.threshold)
        passed, gate_summary, valid_datasets = gate.evaluate_pipeline_batch(run_id=batch_id)

        run_result["stages"]["quality_gate"] = {
            "status": "PASSED" if passed else "FAILED",
            "duration_sec": round(time.time() - t1, 2),
            "quality_score": gate_summary.overall_quality_score,
            "threshold": self.threshold,
            "total_ingested": gate_summary.total_records_ingested,
            "total_valid": gate_summary.total_records_valid,
            "total_quarantined": gate_summary.total_records_quarantined,
        }

        # Stage 3: Circuit Breaker Decision
        logger.info(">>> [Stage 3/5] Threshold Circuit Breaker Check...")
        if not passed:
            logger.error(
                f"[CIRCUIT BREAKER TRIGGERED] Quality score ({gate_summary.overall_quality_score:.2f}%) "
                f"fell below required threshold ({self.threshold}%). Downstream pipeline halted."
            )
            run_result["status"] = "BLOCKED_BY_QUALITY_GATE"
            run_result["end_time"] = datetime.utcnow().isoformat()
            run_result["total_duration_sec"] = round(time.time() - start_time, 2)
            return run_result

        run_result["stages"]["circuit_breaker"] = {"status": "PASSED", "verdict": "ALLOW_DOWNSTREAM"}

        # Stage 4: Lakehouse Parquet Transformation
        logger.info(">>> [Stage 4/5] Lakehouse Parquet Transformation & Partitioning...")
        t2 = time.time()
        transform_pipeline = LakehouseTransformPipeline()
        manifest = transform_pipeline.process_and_publish_lake(valid_datasets, run_id=batch_id)

        run_result["stages"]["transformation"] = {
            "status": "SUCCESS",
            "duration_sec": round(time.time() - t2, 2),
            "partitions_created": manifest["partitions_created"],
            "orders_processed": manifest["records_processed"]["orders"],
        }

        # Stage 5: Warehouse Ingestion
        logger.info(">>> [Stage 5/5] Star Schema Warehouse Ingestion...")
        t3 = time.time()
        loader = WarehouseLoader()
        load_stats = loader.load_lakehouse_to_warehouse(run_id=batch_id)

        run_result["stages"]["warehouse_load"] = {
            "status": "SUCCESS",
            "duration_sec": round(time.time() - t3, 2),
            "load_stats": load_stats,
        }

        run_result["status"] = "SUCCESS"
        run_result["end_time"] = datetime.utcnow().isoformat()
        run_result["total_duration_sec"] = round(time.time() - start_time, 2)

        logger.info(f"============================================================")
        logger.info(f"Pipeline Run [{batch_id}] FINISHED in {run_result['total_duration_sec']}s with status SUCCESS")
        logger.info(f"============================================================")

        return run_result
