"""
Data Quality Gate Controller.
Enforces quality score thresholds, creates pipeline summaries, and controls downstream processing.
"""

import uuid
from datetime import datetime
from typing import Tuple, Dict, Any, Optional
import pandas as pd

from datapulse.config import settings
from datapulse.storage.base import BaseStorage
from datapulse.storage.factory import get_storage_client
from datapulse.quality.validator import DataQualityValidator
from datapulse.quality.quarantine import QuarantineManager
from datapulse.schemas.models import PipelineRunSummary
from datapulse.utils.logger import get_logger

logger = get_logger("datapulse.quality.gate")


class DataQualityGate:
    """
    Quality gatekeeper that evaluates incoming datasets, quarantines corrupted records,
    calculates holistic quality scores, and determines whether downstream processing can proceed.
    """

    def __init__(
        self,
        storage: Optional[BaseStorage] = None,
        quality_threshold: Optional[float] = None,
    ):
        self.storage = storage or get_storage_client()
        self.threshold = quality_threshold or settings.QUALITY_THRESHOLD_PERCENT
        self.quarantine_mgr = QuarantineManager(self.storage)

    def evaluate_pipeline_batch(
        self,
        raw_customers_path: Optional[str] = None,
        raw_products_path: Optional[str] = None,
        raw_orders_path: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Tuple[bool, PipelineRunSummary, Dict[str, pd.DataFrame]]:
        """
        Executes end-to-end quality validation on incoming raw CSV datasets.
        Returns:
            - passed: bool (True if overall quality score >= threshold)
            - summary: PipelineRunSummary
            - valid_datasets: Dict[str, pd.DataFrame] containing clean DataFrames
        """
        batch_id = run_id or f"run-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        start_time = datetime.utcnow()

        c_path = raw_customers_path or f"{settings.RAW_DATA_PATH}/customers.csv"
        p_path = raw_products_path or f"{settings.RAW_DATA_PATH}/products.csv"
        o_path = raw_orders_path or f"{settings.RAW_DATA_PATH}/orders.csv"

        logger.info(f"Initiating Data Quality Gate evaluation for batch [{batch_id}]...")

        # 1. Ingest raw frames
        df_customers_raw = self.storage.read_csv(c_path)
        df_products_raw = self.storage.read_csv(p_path)
        df_orders_raw = self.storage.read_csv(o_path)

        total_ingested = len(df_customers_raw) + len(df_products_raw) + len(df_orders_raw)

        validator = DataQualityValidator()

        # 2. Validate Customers
        valid_customers, q_customers, q_c_map = validator.validate_customers(df_customers_raw)
        self.quarantine_mgr.save_quarantine_batch(batch_id, "customers", q_customers, q_c_map)

        # 3. Validate Products
        valid_products, q_products, q_p_map = validator.validate_products(df_products_raw)
        self.quarantine_mgr.save_quarantine_batch(batch_id, "products", q_products, q_p_map)

        # 4. Validate Orders (using valid customer and product key sets)
        valid_cust_keys = set(valid_customers["customer_id"].astype(str))
        valid_prod_keys = set(valid_products["product_id"].astype(str))

        valid_orders, q_orders, q_o_map = validator.validate_orders(
            df_orders_raw,
            valid_customer_ids=valid_cust_keys,
            valid_product_ids=valid_prod_keys,
        )
        self.quarantine_mgr.save_quarantine_batch(batch_id, "orders", q_orders, q_o_map)

        # 5. Aggregate Results & Scoring
        total_valid = len(valid_customers) + len(valid_products) + len(valid_orders)
        total_quarantined = len(q_customers) + len(q_products) + len(q_orders)

        overall_score = round((total_valid / total_ingested * 100), 2) if total_ingested > 0 else 100.0
        gate_passed = overall_score >= self.threshold

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        summary = PipelineRunSummary(
            run_id=batch_id,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            status="SUCCESS" if gate_passed else "FAILED_QUALITY_GATE",
            total_records_ingested=total_ingested,
            total_records_valid=total_valid,
            total_records_quarantined=total_quarantined,
            overall_quality_score=overall_score,
            quality_threshold=self.threshold,
            metrics=validator.metrics,
        )

        # Save summary report to storage
        summary_path = f"{settings.QUARANTINE_DATA_PATH}/quality_report_{batch_id}.json"
        self.storage.write_json(summary.model_dump(mode="json"), summary_path)

        if gate_passed:
            logger.info(
                f"[QUALITY GATE PASSED] Score: {overall_score:.2f}% (Threshold: {self.threshold}%) | "
                f"Valid: {total_valid:,} | Quarantined: {total_quarantined:,}"
            )
        else:
            logger.error(
                f"[QUALITY GATE BLOCKED] Score: {overall_score:.2f}% < Threshold: {self.threshold}% | "
                f"Quarantined: {total_quarantined:,} records."
            )

        valid_datasets = {
            "customers": valid_customers,
            "products": valid_products,
            "orders": valid_orders,
        }

        return gate_passed, summary, valid_datasets
