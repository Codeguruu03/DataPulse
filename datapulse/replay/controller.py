"""
Pipeline Replay & Remediation Controller.
Enables restarting and replaying pipeline stages from validation or quarantine checkpoints.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd

from datapulse.config import settings
from datapulse.storage.base import BaseStorage
from datapulse.storage.factory import get_storage_client
from datapulse.quality.gate import DataQualityGate
from datapulse.transforms.pipeline import LakehouseTransformPipeline
from datapulse.warehouse.loader import WarehouseLoader
from datapulse.utils.logger import get_logger

logger = get_logger("datapulse.replay.controller")


class PipelineReplayController:
    """Controls selective re-execution of data pipeline stages."""

    def __init__(self, storage: Optional[BaseStorage] = None):
        self.storage = storage or get_storage_client()

    def replay_from_validation(
        self,
        replay_run_id: str,
        threshold: float = 95.0,
    ) -> Dict[str, Any]:
        """
        Replays pipeline stages starting from Quality Gate Validation using existing raw files.
        """
        logger.info(f"Initiating pipeline replay for run [{replay_run_id}] from checkpoint [VALIDATION]...")
        
        gate = DataQualityGate(storage=self.storage, quality_threshold=threshold)
        passed, summary, valid_datasets = gate.evaluate_pipeline_batch(run_id=replay_run_id)

        if not passed:
            logger.error(f"Replay run [{replay_run_id}] failed quality gate ({summary.overall_quality_score:.2f}% < {threshold}%).")
            return {
                "replay_run_id": replay_run_id,
                "status": "BLOCKED_BY_QUALITY_GATE",
                "quality_score": summary.overall_quality_score,
            }

        # Transform to Lakehouse
        pipeline = LakehouseTransformPipeline(storage=self.storage)
        manifest = pipeline.process_and_publish_lake(valid_datasets, run_id=replay_run_id)

        # Load Warehouse
        loader = WarehouseLoader(storage=self.storage)
        load_stats = loader.load_lakehouse_to_warehouse(run_id=replay_run_id)

        logger.info(f"Pipeline replay for run [{replay_run_id}] completed successfully.")
        return {
            "replay_run_id": replay_run_id,
            "status": "SUCCESS",
            "checkpoint": "VALIDATION",
            "quality_score": summary.overall_quality_score,
            "orders_replayed": manifest["records_processed"]["orders"],
            "load_stats": load_stats,
        }
