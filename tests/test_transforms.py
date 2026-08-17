"""
Tests for DataPulse Transformation and Partitioned Parquet Lakehouse.
"""

from pathlib import Path
import pandas as pd
import pytest

from datapulse.storage.local import LocalStorage
from datapulse.transforms.cleaners import DatasetCleaners
from datapulse.transforms.enrichment import DatasetEnricher
from datapulse.transforms.pipeline import LakehouseTransformPipeline


def test_cleaners_standardization():
    raw_c = pd.DataFrame({
        "customer_id": ["CUST-1", "CUST-2"],
        "name": ["john doe", "jane smith"],
        "email": ["JOHN@EXAMPLE.COM", "Jane@Example.Com"],
        "country": ["usa", "ind"],
        "segment": ["Corporate", "Consumer"],
        "signup_date": ["2023-05-10", "2023-06-15"],
        "is_active": ["True", "false"],
    })

    cleaned_c = DatasetCleaners.clean_customers(raw_c)
    assert cleaned_c.loc[0, "name"] == "John Doe"
    assert cleaned_c.loc[0, "email"] == "john@example.com"
    assert cleaned_c.loc[0, "country"] == "United States"
    assert cleaned_c.loc[1, "country"] == "India"
    assert cleaned_c.loc[0, "is_active"] == True
    assert cleaned_c.loc[1, "is_active"] == False


def test_enrichment_rfm_calculation():
    customers = pd.DataFrame({
        "customer_id": ["C1", "C2"],
        "name": ["Alice", "Bob"],
    })

    orders = pd.DataFrame({
        "order_id": ["O1", "O2", "O3"],
        "customer_id": ["C1", "C1", "C2"],
        "total_amount": [5000.0, 6000.0, 200.0],
        "order_date": ["2024-01-01", "2024-01-05", "2024-01-02"],
    })

    enriched_c = DatasetEnricher.enrich_customers(customers, orders)
    c1 = enriched_c[enriched_c["customer_id"] == "C1"].iloc[0]
    assert c1["total_spend"] == 11000.0
    assert c1["total_orders"] == 2
    assert c1["customer_tier"] == "Diamond"

    c2 = enriched_c[enriched_c["customer_id"] == "C2"].iloc[0]
    assert c2["total_spend"] == 200.0
    assert c2["customer_tier"] == "Bronze"


def test_lakehouse_pipeline_parquet_partitions(tmp_path: Path):
    storage = LocalStorage(base_path=str(tmp_path))
    pipeline = LakehouseTransformPipeline(storage=storage)

    valid_datasets = {
        "customers": pd.DataFrame({
            "customer_id": ["C1"],
            "name": ["Alice"],
            "email": ["alice@test.com"],
            "country": ["USA"],
            "segment": ["Consumer"],
            "signup_date": ["2024-01-01"],
            "is_active": ["True"],
        }),
        "products": pd.DataFrame({
            "product_id": ["P1"],
            "sku": ["SKU1"],
            "product_name": ["Widget"],
            "category": ["Hardware"],
            "unit_price": ["100.0"],
            "cost_price": ["50.0"],
            "in_stock": ["20"],
        }),
        "orders": pd.DataFrame({
            "order_id": ["O1", "O2"],
            "customer_id": ["C1", "C1"],
            "product_id": ["P1", "P1"],
            "quantity": ["2", "1"],
            "unit_price": ["100.0", "100.0"],
            "discount_rate": ["0.0", "0.1"],
            "total_amount": ["200.0", "90.0"],
            "order_date": ["2024-03-15 10:00:00", "2024-04-20 12:00:00"],
            "order_status": ["Completed", "Completed"],
            "payment_method": ["UPI", "Credit Card"],
        }),
    }

    manifest = pipeline.process_and_publish_lake(valid_datasets, run_id="test-run-trans")
    assert manifest["records_processed"]["orders"] == 2
    assert manifest["partitions_created"] == 2  # month 3 and month 4
