"""
Lakehouse Parquet Transformation Pipeline.
Orchestrates cleaning, dimension enrichment, and partitioned Parquet data lake writing.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pandas as pd

from datapulse.config import settings
from datapulse.storage.base import BaseStorage
from datapulse.storage.factory import get_storage_client
from datapulse.transforms.cleaners import DatasetCleaners
from datapulse.transforms.enrichment import DatasetEnricher
from datapulse.utils.logger import get_logger

logger = get_logger("datapulse.transforms.pipeline")


class LakehouseTransformPipeline:
    """Executes transformations and writes partitioned Parquet datasets to the Lakehouse."""

    def __init__(self, storage: Optional[BaseStorage] = None):
        self.storage = storage or get_storage_client()

    def process_and_publish_lake(
        self,
        valid_datasets: Dict[str, pd.DataFrame],
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cleans, enriches, and persists validated datasets to Parquet partitions.
        """
        batch_id = run_id or f"trans-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        logger.info(f"Starting Lakehouse Parquet Transformation Pipeline [{batch_id}]...")

        df_c = valid_datasets.get("customers")
        df_p = valid_datasets.get("products")
        df_o = valid_datasets.get("orders")

        if df_c is None or df_p is None or df_o is None:
            raise ValueError("All three datasets ('customers', 'products', 'orders') are required for transformation.")

        # 1. Clean data
        clean_customers = DatasetCleaners.clean_customers(df_c)
        clean_products = DatasetCleaners.clean_products(df_p)
        clean_orders = DatasetCleaners.clean_orders(df_o)

        # 2. Enrich dimensions
        enriched_customers = DatasetEnricher.enrich_customers(clean_customers, clean_orders)
        enriched_products = DatasetEnricher.enrich_products(clean_products, clean_orders)

        # 3. Target Parquet storage paths (relative to storage root)
        base_processed = "processed"
        customers_parquet_path = f"{base_processed}/dim_customers/customers.parquet"
        products_parquet_path = f"{base_processed}/dim_products/products.parquet"
        orders_parquet_path = f"{base_processed}/fact_orders"


        # 4. Write Parquet with Year/Month partitioning for orders
        logger.info("Writing enriched datasets to Parquet lakehouse...")
        self.storage.write_parquet(enriched_customers, customers_parquet_path)
        self.storage.write_parquet(enriched_products, products_parquet_path)
        
        # Partition orders by year and month
        self.storage.write_parquet(
            clean_orders,
            orders_parquet_path,
            partition_cols=["year", "month"],
        )

        unique_partitions = clean_orders[["year", "month"]].drop_duplicates().to_dict(orient="records")

        summary = {
            "run_id": batch_id,
            "timestamp": datetime.utcnow().isoformat(),
            "records_processed": {
                "customers": len(enriched_customers),
                "products": len(enriched_products),
                "orders": len(clean_orders),
            },
            "partitions_created": len(unique_partitions),
            "partitions": unique_partitions,
            "paths": {
                "customers": customers_parquet_path,
                "products": products_parquet_path,
                "orders": orders_parquet_path,
            },
        }

        # Write transformation audit manifest
        manifest_path = f"{base_processed}/transform_manifest_{batch_id}.json"
        self.storage.write_json(summary, manifest_path)

        logger.info(
            f"Lakehouse transform completed: {len(clean_orders):,} orders written across {len(unique_partitions)} partitions."
        )
        return summary
