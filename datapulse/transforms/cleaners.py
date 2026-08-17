"""
Standardization and Cleaning Transforms for DataPulse Data Lake.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np


class DatasetCleaners:
    """Provides pure transformation functions to standardize and format validated datasets."""

    COUNTRY_MAP: Dict[str, str] = {
        "us": "United States",
        "usa": "United States",
        "united states of america": "United States",
        "united states": "United States",
        "uk": "United Kingdom",
        "united kingdom": "United Kingdom",
        "in": "India",
        "ind": "India",
        "india": "India",
        "de": "Germany",
        "germany": "Germany",
        "ca": "Canada",
        "canada": "Canada",
    }

    @classmethod
    def clean_customers(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans and standardizes customer records."""
        df_clean = df.copy()
        df_clean["customer_id"] = df_clean["customer_id"].astype(str).str.strip()
        df_clean["name"] = df_clean["name"].astype(str).str.strip().str.title()
        df_clean["email"] = df_clean["email"].astype(str).str.strip().str.lower()
        
        # Standardize country
        df_clean["country"] = (
            df_clean["country"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map(cls.COUNTRY_MAP)
            .fillna("Other")
        )
        df_clean["segment"] = df_clean["segment"].astype(str).str.strip()
        df_clean["signup_date"] = pd.to_datetime(df_clean["signup_date"]).dt.date
        df_clean["is_active"] = df_clean["is_active"].astype(str).str.lower().isin(["true", "1", "yes"])

        return df_clean

    @classmethod
    def clean_products(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans and types product catalog."""
        df_clean = df.copy()
        df_clean["product_id"] = df_clean["product_id"].astype(str).str.strip()
        df_clean["sku"] = df_clean["sku"].astype(str).str.strip().str.upper()
        df_clean["product_name"] = df_clean["product_name"].astype(str).str.strip()
        df_clean["category"] = df_clean["category"].astype(str).str.strip().str.title()
        df_clean["unit_price"] = pd.to_numeric(df_clean["unit_price"], errors="coerce").astype(float)
        df_clean["cost_price"] = pd.to_numeric(df_clean["cost_price"], errors="coerce").astype(float)
        df_clean["in_stock"] = pd.to_numeric(df_clean["in_stock"], errors="coerce").fillna(0).astype(int)

        # Derived profit margin %
        df_clean["profit_margin_pct"] = np.where(
            df_clean["unit_price"] > 0,
            np.round((df_clean["unit_price"] - df_clean["cost_price"]) / df_clean["unit_price"] * 100, 2),
            0.0,
        )

        return df_clean

    @classmethod
    def clean_orders(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Cleans orders and extracts calendar partition columns."""
        df_clean = df.copy()
        df_clean["order_id"] = df_clean["order_id"].astype(str).str.strip()
        df_clean["customer_id"] = df_clean["customer_id"].astype(str).str.strip()
        df_clean["product_id"] = df_clean["product_id"].astype(str).str.strip()
        df_clean["quantity"] = pd.to_numeric(df_clean["quantity"], errors="coerce").astype(int)
        df_clean["unit_price"] = pd.to_numeric(df_clean["unit_price"], errors="coerce").astype(float)
        df_clean["discount_rate"] = pd.to_numeric(df_clean["discount_rate"], errors="coerce").fillna(0.0).astype(float)
        
        # Calculate actual net total amount
        df_clean["total_amount"] = np.round(
            df_clean["quantity"] * df_clean["unit_price"] * (1.0 - df_clean["discount_rate"]), 2
        )
        
        order_dt = pd.to_datetime(df_clean["order_date"], errors="coerce")
        df_clean["order_date"] = order_dt
        df_clean["year"] = order_dt.dt.year.astype(int)
        df_clean["month"] = order_dt.dt.month.astype(int)
        df_clean["day"] = order_dt.dt.day.astype(int)
        df_clean["order_status"] = df_clean["order_status"].astype(str).str.strip()
        df_clean["payment_method"] = df_clean["payment_method"].astype(str).str.strip()

        return df_clean
