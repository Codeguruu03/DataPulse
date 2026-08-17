"""
Realistic Synthetic Data Generator for DataPulse.

Simulates enterprise e-commerce / B2B sales data with realistic business distributions,
referential relationships, and configurable data anomalies for quality gate testing.
"""

import os
import random
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from faker import Faker

from datapulse.utils.logger import get_logger
from datapulse.config import settings

logger = get_logger("datapulse.generator")
fake = Faker()
Faker.seed(42)
random.seed(42)

# Standard Product Catalog Templates
PRODUCT_TEMPLATES = [
    ("PRD-101", "MacBook Pro 16", "Hardware", 2499.00, 1800.00),
    ("PRD-102", "Dell UltraSharp 32 4K", "Hardware", 899.00, 620.00),
    ("PRD-103", "Ergonomic Mechanical Keyboard", "Accessories", 189.00, 95.00),
    ("PRD-104", "Wireless Noise-Canceling Headset", "Accessories", 299.00, 150.00),
    ("PRD-105", "Enterprise Cloud Database License", "Software", 4500.00, 500.00),
    ("PRD-106", "Security Endpoint Protection Sub", "Software", 1200.00, 200.00),
    ("PRD-107", "4K Ultra-HD Webcam", "Accessories", 199.00, 110.00),
    ("PRD-108", "Executive Standing Desk", "Furniture", 750.00, 420.00),
    ("PRD-109", "Mesh High-Back Ergonomic Chair", "Furniture", 550.00, 310.00),
    ("PRD-110", "AI Analytics Enterprise SaaS", "Software", 3500.00, 400.00),
    ("PRD-111", "USB-C Dual 4K Docking Station", "Hardware", 249.00, 130.00),
    ("PRD-112", "Portable SSD 2TB Rugged", "Storage", 179.00, 95.00),
]

SEGMENTS = ["Consumer", "Corporate", "Home Office", "Small Business"]
ORDER_STATUSES = ["Completed", "Pending", "Processing", "Shipped", "Cancelled", "Refunded"]
PAYMENT_METHODS = ["Credit Card", "Debit Card", "UPI", "Net Banking", "Wallet", "Cash on Delivery"]
COUNTRY_VARIANTS = ["United States", "USA", "US", "United Kingdom", "UK", "India", "Ind", "Germany", "Canada"]


class DataPulseGenerator:
    """
    Generates synthetic transactional datasets with configurable noise and corruption rates.
    """

    def __init__(self, anomaly_rate: float = 0.05, seed: Optional[int] = 42):
        self.anomaly_rate = anomaly_rate
        if seed is not None:
            random.seed(seed)
            Faker.seed(seed)

    def generate_customers(self, count: int = 500) -> List[Dict[str, Any]]:
        """Generates customer profiles."""
        customers = []
        for i in range(1, count + 1):
            cust_id = f"CUST-{i:06d}"
            name = fake.name()
            email = fake.ascii_company_email()
            country = random.choice(COUNTRY_VARIANTS)
            segment = random.choice(SEGMENTS)
            signup_date = fake.date_between(start_date="-3y", end_date="today").isoformat()
            is_active = "True" if random.random() > 0.1 else "False"

            # Potential anomaly in customer record
            if random.random() < (self.anomaly_rate * 0.5):
                flaw_type = random.choice(["missing_id", "invalid_email", "null_name"])
                if flaw_type == "missing_id":
                    cust_id = ""
                elif flaw_type == "invalid_email":
                    email = "not_an_email"
                elif flaw_type == "null_name":
                    name = ""

            customers.append({
                "customer_id": cust_id,
                "name": name,
                "email": email,
                "country": country,
                "segment": segment,
                "signup_date": signup_date,
                "is_active": is_active,
            })
        return customers

    def generate_products(self) -> List[Dict[str, Any]]:
        """Generates product catalog based on realistic templates."""
        products = []
        for sku, name, cat, price, cost in PRODUCT_TEMPLATES:
            products.append({
                "product_id": f"P-{sku}",
                "sku": sku,
                "product_name": name,
                "category": cat,
                "unit_price": str(price),
                "cost_price": str(cost),
                "in_stock": str(random.randint(20, 500)),
            })
        return products

    def generate_orders(
        self,
        count: int = 5000,
        customers: Optional[List[Dict[str, Any]]] = None,
        products: Optional[List[Dict[str, Any]]] = None,
        start_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generates transaction orders referencing customers and products,
        injecting realistic data quality issues at the specified anomaly_rate.
        """
        if not customers:
            customers = self.generate_customers(200)
        if not products:
            products = self.generate_products()

        valid_cust_ids = [c["customer_id"] for c in customers if c["customer_id"]]
        valid_prod_dict = {p["product_id"]: float(p["unit_price"]) for p in products}
        prod_keys = list(valid_prod_dict.keys())

        start_dt = start_date or (datetime.utcnow() - timedelta(days=180))
        orders = []

        for i in range(1, count + 1):
            order_id = f"ORD-{i:07d}"
            customer_id = random.choice(valid_cust_ids)
            product_id = random.choice(prod_keys)
            base_unit_price = valid_prod_dict[product_id]
            quantity = random.choices([1, 2, 3, 4, 5, 10], weights=[50, 25, 12, 8, 4, 1])[0]
            discount_rate = random.choices([0.0, 0.05, 0.10, 0.15, 0.20], weights=[60, 15, 12, 8, 5])[0]
            
            unit_price = base_unit_price
            total_amount = round(quantity * unit_price * (1.0 - discount_rate), 2)
            
            random_days = random.randint(0, 180)
            random_seconds = random.randint(0, 86400)
            order_dt = start_dt + timedelta(days=random_days, seconds=random_seconds)
            order_date_str = order_dt.strftime("%Y-%m-%d %H:%M:%S")

            order_status = random.choice(ORDER_STATUSES)
            payment_method = random.choice(PAYMENT_METHODS)

            # Injected anomalies based on anomaly_rate
            if random.random() < self.anomaly_rate:
                anomaly_type = random.choice([
                    "negative_quantity",
                    "negative_price",
                    "null_customer_id",
                    "duplicate_order_id",
                    "invalid_date_format",
                    "orphan_foreign_key",
                    "corrupted_status",
                    "zero_quantity",
                ])

                if anomaly_type == "negative_quantity":
                    quantity = -random.randint(1, 5)
                    total_amount = round(quantity * unit_price, 2)
                elif anomaly_type == "negative_price":
                    unit_price = -base_unit_price
                    total_amount = round(quantity * unit_price, 2)
                elif anomaly_type == "null_customer_id":
                    customer_id = ""
                elif anomaly_type == "duplicate_order_id":
                    # Duplicate an earlier order ID
                    if orders:
                        order_id = orders[random.randint(0, len(orders) - 1)]["order_id"]
                elif anomaly_type == "invalid_date_format":
                    order_date_str = "2026-99-99 25:99:99"
                elif anomaly_type == "orphan_foreign_key":
                    customer_id = f"CUST-ORPHAN-{random.randint(900000, 999999)}"
                elif anomaly_type == "corrupted_status":
                    order_status = "UNKNOWN_ERROR_STATUS"
                elif anomaly_type == "zero_quantity":
                    quantity = 0
                    total_amount = 0.0

            orders.append({
                "order_id": order_id,
                "customer_id": customer_id,
                "product_id": product_id,
                "quantity": str(quantity),
                "unit_price": str(unit_price),
                "discount_rate": str(discount_rate),
                "total_amount": str(total_amount),
                "order_date": order_date_str,
                "order_status": order_status,
                "payment_method": payment_method,
            })

        return orders

    def generate_all_and_save(
        self,
        output_dir: Optional[Path] = None,
        num_orders: int = 5000,
        num_customers: int = 500,
    ) -> Tuple[Path, Path, Path]:
        """Generates all datasets and writes raw CSV files to the designated raw directory."""
        target_dir = output_dir or settings.RAW_DATA_PATH
        target_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating synthetic enterprise datasets with {self.anomaly_rate * 100:.1f}% anomaly rate...")

        customers = self.generate_customers(num_customers)
        products = self.generate_products()
        orders = self.generate_orders(num_orders, customers=customers, products=products)

        customers_file = target_dir / "customers.csv"
        products_file = target_dir / "products.csv"
        orders_file = target_dir / "orders.csv"

        self._write_csv(customers_file, customers)
        self._write_csv(products_file, products)
        self._write_csv(orders_file, orders)

        logger.info(f"Generated {len(customers)} customers -> {customers_file}")
        logger.info(f"Generated {len(products)} products -> {products_file}")
        logger.info(f"Generated {len(orders)} orders -> {orders_file}")

        return customers_file, products_file, orders_file

    def _write_csv(self, filepath: Path, data: List[Dict[str, Any]]) -> None:
        if not data:
            return
        fieldnames = list(data[0].keys())
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
