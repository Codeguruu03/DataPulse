"""
Warehouse Ingestion and Parquet-to-Star-Schema Loader.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

from datapulse.config import settings
from datapulse.storage.base import BaseStorage
from datapulse.storage.factory import get_storage_client
from datapulse.warehouse.db import DatabaseManager, default_db_manager
from datapulse.warehouse.models import (
    DimCustomer,
    DimProduct,
    FactOrder,
    DataQualityAudit,
    QuarantineAudit,
)
from datapulse.warehouse.migrations import SchemaMigrator
from datapulse.utils.logger import get_logger

logger = get_logger("datapulse.warehouse.loader")


class WarehouseLoader:
    """Loads Parquet lakehouse tier into PostgreSQL / SQLite Star Schema warehouse tables."""

    def __init__(
        self,
        db_mgr: Optional[DatabaseManager] = None,
        storage: Optional[BaseStorage] = None,
    ):
        self.db_mgr = db_mgr or default_db_manager
        self.storage = storage or get_storage_client()
        self.migrator = SchemaMigrator(self.db_mgr)

    def load_lakehouse_to_warehouse(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes idempotent loading from processed Parquet files into dimensional tables.
        """
        # Ensure tables and views exist
        self.migrator.init_schema()

        session: Session = self.db_mgr.get_session()
        load_stats = {"customers_loaded": 0, "products_loaded": 0, "orders_loaded": 0, "audit_records_loaded": 0}

        try:
            cust_parquet = "processed/dim_customers/customers.parquet" if self.storage.exists("processed/dim_customers/customers.parquet") else f"{settings.PROCESSED_DATA_PATH}/dim_customers/customers.parquet"
            prod_parquet = "processed/dim_products/products.parquet" if self.storage.exists("processed/dim_products/products.parquet") else f"{settings.PROCESSED_DATA_PATH}/dim_products/products.parquet"
            orders_parquet_dir = "processed/fact_orders" if self.storage.exists("processed/fact_orders") else f"{settings.PROCESSED_DATA_PATH}/fact_orders"


            # 1. Load Dimensions (Customers)
            if self.storage.exists(cust_parquet):
                df_cust = self.storage.read_parquet(cust_parquet)
                # Coerce all NOT NULL string columns to str, replacing NaN with fallback values
                # This guards against Linux PyArrow Parquet reads producing NaN for string columns
                df_cust["customer_id"] = df_cust["customer_id"].fillna("").astype(str).str.strip()
                df_cust["name"] = df_cust["name"].fillna("Unknown").astype(str).str.strip()
                df_cust["email"] = df_cust["email"].fillna("").astype(str).str.strip()
                df_cust["country"] = df_cust["country"].fillna("Other").astype(str).str.strip()
                df_cust["segment"] = df_cust["segment"].fillna("Consumer").astype(str).str.strip()
                # Drop rows with empty required fields that would fail NOT NULL constraints
                df_cust = df_cust[df_cust["customer_id"].str.len() > 0].copy()
                # Idempotent: delete existing IDs before re-inserting
                existing_ids = list(set(df_cust["customer_id"]))
                session.query(DimCustomer).filter(DimCustomer.customer_id.in_(existing_ids)).delete(synchronize_session=False)

                cust_objects = []
                for _, row in df_cust.iterrows():
                    cust_objects.append(
                        DimCustomer(
                            customer_id=str(row["customer_id"]),
                            name=str(row["name"]) if pd.notna(row["name"]) else "Unknown",
                            email=str(row["email"]) if pd.notna(row["email"]) else "",
                            country=str(row["country"]) if pd.notna(row["country"]) else "Other",
                            segment=str(row["segment"]) if pd.notna(row["segment"]) else "Consumer",
                            signup_date=pd.to_datetime(row["signup_date"]).date(),
                            is_active=bool(row["is_active"]),
                            customer_tier=str(row.get("customer_tier") or "Bronze"),
                            total_spend=float(row.get("total_spend") or 0.0),
                            total_orders=int(row.get("total_orders") or 0),
                            avg_order_value=float(row.get("avg_order_value") or 0.0),
                        )
                    )
                session.bulk_save_objects(cust_objects)
                session.commit()
                load_stats["customers_loaded"] = len(cust_objects)
                logger.info(f"Loaded {len(cust_objects)} customer records into dim_customers.")

            # 2. Load Dimensions (Products)
            if self.storage.exists(prod_parquet):
                df_prod = self.storage.read_parquet(prod_parquet)
                existing_prod_ids = list(set(df_prod["product_id"]))
                session.query(DimProduct).filter(DimProduct.product_id.in_(existing_prod_ids)).delete(synchronize_session=False)

                prod_objects = []
                for _, row in df_prod.iterrows():
                    prod_objects.append(
                        DimProduct(
                            product_id=row["product_id"],
                            sku=row["sku"],
                            product_name=row["product_name"],
                            category=row["category"],
                            unit_price=float(row["unit_price"]),
                            cost_price=float(row["cost_price"]),
                            profit_margin_pct=float(row.get("profit_margin_pct", 0.0)),
                            in_stock=int(row.get("in_stock", 0)),
                            total_units_sold=int(row.get("total_units_sold", 0)),
                            total_revenue=float(row.get("total_revenue", 0.0)),
                        )
                    )
                session.bulk_save_objects(prod_objects)
                session.commit()
                load_stats["products_loaded"] = len(prod_objects)
                logger.info(f"Loaded {len(prod_objects)} product records into dim_products.")

            # 3. Load Fact Orders
            if self.storage.exists(orders_parquet_dir):
                df_orders = self.storage.read_parquet(orders_parquet_dir)
                # Ensure unique order_ids in memory
                df_orders = df_orders.drop_duplicates(subset=["order_id"]).copy()
                existing_order_ids = list(df_orders["order_id"])

                # Delete existing in chunks of 500 to avoid SQLite parameter limit
                chunk_size = 500
                for i in range(0, len(existing_order_ids), chunk_size):
                    chunk_ids = existing_order_ids[i:i + chunk_size]
                    session.query(FactOrder).filter(FactOrder.order_id.in_(chunk_ids)).delete(synchronize_session=False)
                session.commit()

                order_objects = []
                for _, row in df_orders.iterrows():
                    order_dt = pd.to_datetime(row["order_date"])
                    date_key = int(order_dt.strftime("%Y%m%d"))
                    order_objects.append(
                        FactOrder(
                            order_id=str(row["order_id"]),
                            customer_id=str(row["customer_id"]),
                            product_id=str(row["product_id"]),
                            date_key=date_key,
                            order_date=order_dt.to_pydatetime(),
                            quantity=int(row["quantity"]),
                            unit_price=float(row["unit_price"]),
                            discount_rate=float(row.get("discount_rate", 0.0)),
                            total_amount=float(row["total_amount"]),
                            order_status=str(row["order_status"]),
                            payment_method=str(row["payment_method"]),
                        )
                    )
                session.bulk_save_objects(order_objects)
                session.commit()
                load_stats["orders_loaded"] = len(order_objects)
                logger.info(f"Loaded {len(order_objects)} order facts into fact_orders.")


            # 4. Load Quality & Quarantine Audit logs if present
            quarantine_dir = "quarantine" if self.storage.exists("quarantine") else str(settings.QUARANTINE_DATA_PATH)
            audit_files = self.storage.list_files(quarantine_dir, suffix=".json")

            for f_path in audit_files:
                if "quality_report_" in f_path:
                    data = self.storage.read_json(f_path)
                    r_id = data.get("run_id", "unknown")
                    # Check if already loaded
                    if session.query(DataQualityAudit).filter_by(run_id=r_id).count() == 0:
                        for m in data.get("metrics", []):
                            session.add(
                                DataQualityAudit(
                                    run_id=r_id,
                                    check_name=m["check_name"],
                                    dataset=m["dataset"],
                                    status=m["status"],
                                    records_checked=m["records_checked"],
                                    records_passed=m["records_passed"],
                                    records_failed=m["records_failed"],
                                    pass_rate=m["pass_rate"],
                                )
                            )
                        session.commit()
                        load_stats["audit_records_loaded"] += len(data.get("metrics", []))

            logger.info("Warehouse load completed successfully.")
            return load_stats
        except Exception as e:
            session.rollback()
            logger.error(f"Error during warehouse load: {e}")
            raise
        finally:
            session.close()

    def query_mart(self, mart_name: str, limit: int = 10) -> pd.DataFrame:
        """Queries an analytical view mart and returns a pandas DataFrame."""
        view_name = f"v_mart_{mart_name}" if not mart_name.startswith("v_mart_") else mart_name
        query = text(f"SELECT * FROM {view_name} LIMIT {limit};")
        with self.db_mgr.engine.connect() as conn:
            return pd.read_sql(query, conn)
