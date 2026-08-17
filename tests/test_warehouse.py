"""
Tests for DataPulse Star Schema Warehouse, Migrations, and Analytical Marts.
"""

from pathlib import Path
import pandas as pd
import pytest

from datapulse.warehouse.db import DatabaseManager
from datapulse.warehouse.migrations import SchemaMigrator
from datapulse.warehouse.loader import WarehouseLoader
from datapulse.storage.local import LocalStorage
from datapulse.transforms.pipeline import LakehouseTransformPipeline


def test_schema_migration_and_dim_date(tmp_path: Path):
    db_file = tmp_path / "test_dw.db"
    db_mgr = DatabaseManager(db_url=f"sqlite:///{db_file}")

    migrator = SchemaMigrator(db_mgr=db_mgr)
    migrator.init_schema()

    with db_mgr.engine.connect() as conn:
        res = conn.execute(pd.io.sql.text("SELECT COUNT(*) FROM dim_date;")).scalar()
        assert res > 1000  # calendar days populated


def test_warehouse_loader_end_to_end(tmp_path: Path):
    db_file = tmp_path / "test_dw.db"
    db_mgr = DatabaseManager(db_url=f"sqlite:///{db_file}")
    storage = LocalStorage(base_path=str(tmp_path))

    # 1. Transform lakehouse data
    pipeline = LakehouseTransformPipeline(storage=storage)
    valid_datasets = {
        "customers": pd.DataFrame({
            "customer_id": ["C1"],
            "name": ["Alice"],
            "email": ["alice@test.com"],
            "country": ["USA"],
            "segment": ["Corporate"],
            "signup_date": ["2024-01-01"],
            "is_active": ["True"],
        }),
        "products": pd.DataFrame({
            "product_id": ["P1"],
            "sku": ["SKU-100"],
            "product_name": ["Super Laptop"],
            "category": ["Hardware"],
            "unit_price": ["1500.0"],
            "cost_price": ["1000.0"],
            "in_stock": ["10"],
        }),
        "orders": pd.DataFrame({
            "order_id": ["O1"],
            "customer_id": ["C1"],
            "product_id": ["P1"],
            "quantity": ["2"],
            "unit_price": ["1500.0"],
            "discount_rate": ["0.0"],
            "total_amount": ["3000.0"],
            "order_date": ["2024-05-10 14:00:00"],
            "order_status": ["Completed"],
            "payment_method": ["Credit Card"],
        }),
    }
    pipeline.process_and_publish_lake(valid_datasets, run_id="run-wh-test")

    # 2. Ingest to warehouse
    loader = WarehouseLoader(db_mgr=db_mgr, storage=storage)
    stats = loader.load_lakehouse_to_warehouse()

    assert stats["customers_loaded"] == 1
    assert stats["products_loaded"] == 1
    assert stats["orders_loaded"] == 1

    # 3. Query Mart View
    df_mart = loader.query_mart("monthly_revenue")
    assert not df_mart.empty
    assert df_mart.iloc[0]["total_revenue"] == 3000.0
