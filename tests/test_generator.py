"""
Tests for DataPulse Synthetic Data Generator and Schema Contracts.
"""

from pathlib import Path
import pytest
from datapulse.generator.generator import DataPulseGenerator
from datapulse.schemas.models import CleanCustomer, CleanProduct, CleanOrder


def test_generator_counts():
    gen = DataPulseGenerator(anomaly_rate=0.0, seed=123)
    customers = gen.generate_customers(count=50)
    products = gen.generate_products()
    orders = gen.generate_orders(count=100, customers=customers, products=products)

    assert len(customers) == 50
    assert len(products) == 12
    assert len(orders) == 100


def test_generator_anomalies_injected():
    gen = DataPulseGenerator(anomaly_rate=0.5, seed=42)
    orders = gen.generate_orders(count=200)

    # With a 50% anomaly rate, we expect several flawed records
    negative_qty = [o for o in orders if int(o["quantity"]) <= 0]
    null_cust = [o for o in orders if o["customer_id"] == ""]
    invalid_dates = [o for o in orders if "99:99" in o["order_date"]]

    assert len(negative_qty) > 0 or len(null_cust) > 0 or len(invalid_dates) > 0


def test_clean_schema_validation():
    # Valid customer
    cust = CleanCustomer(
        customer_id="CUST-000001",
        name="Alice Smith",
        email="alice@example.com",
        country="USA",
        segment="Corporate",
        signup_date="2024-01-15",
    )
    assert cust.country == "United States"  # standardizer check

    # Valid product
    prod = CleanProduct(
        product_id="P-PRD-101",
        sku="PRD-101",
        product_name="MacBook Pro 16",
        category="Hardware",
        unit_price=2499.00,
        cost_price=1800.00,
        in_stock=50,
    )
    assert prod.profit_margin > 0.0


def test_generate_and_save_to_disk(tmp_path: Path):
    gen = DataPulseGenerator(anomaly_rate=0.05, seed=99)
    c_file, p_file, o_file = gen.generate_all_and_save(output_dir=tmp_path, num_orders=20, num_customers=10)

    assert c_file.exists()
    assert p_file.exists()
    assert o_file.exists()
