"""
Enrichment and Feature Engineering Transformations.
Computes analytical dimensions, customer 360 KPIs, and product performance aggregates.
"""

from datetime import datetime
import pandas as pd
import numpy as np


class DatasetEnricher:
    """Computes derived analytical facts and enriched dimensions."""

    @staticmethod
    def enrich_customers(
        df_customers: pd.DataFrame,
        df_orders: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Enriches customer dimension with RFM and transactional summary features:
        - Total Spend (Monetary)
        - Total Orders (Frequency)
        - Average Order Value (AOV)
        - Days Since Last Purchase (Recency)
        - Value Tier (Diamond, Gold, Silver, Bronze)
        """
        if df_orders.empty:
            df_cust_enriched = df_customers.copy()
            df_cust_enriched["total_spend"] = 0.0
            df_cust_enriched["total_orders"] = 0
            df_cust_enriched["avg_order_value"] = 0.0
            df_cust_enriched["days_since_last_order"] = 999
            df_cust_enriched["customer_tier"] = "Bronze"
            return df_cust_enriched

        now = pd.to_datetime(df_orders["order_date"].max()) if not df_orders.empty else pd.to_datetime(datetime.utcnow())

        agg_df = (
            df_orders.groupby("customer_id")
            .agg(
                total_spend=("total_amount", "sum"),
                total_orders=("order_id", "count"),
                avg_order_value=("total_amount", "mean"),
                last_order_date=("order_date", "max"),
            )
            .reset_index()
        )

        agg_df["total_spend"] = agg_df["total_spend"].round(2)
        agg_df["avg_order_value"] = agg_df["avg_order_value"].round(2)
        agg_df["days_since_last_order"] = (now - pd.to_datetime(agg_df["last_order_date"])).dt.days

        # Classify customer tier based on total spend
        conditions = [
            (agg_df["total_spend"] >= 10000),
            (agg_df["total_spend"] >= 5000),
            (agg_df["total_spend"] >= 1000),
        ]
        choices = ["Diamond", "Gold", "Silver"]
        agg_df["customer_tier"] = np.select(conditions, choices, default="Bronze")

        df_enriched = pd.merge(df_customers, agg_df, on="customer_id", how="left")
        df_enriched["total_spend"] = df_enriched["total_spend"].fillna(0.0)
        df_enriched["total_orders"] = df_enriched["total_orders"].fillna(0).astype(int)
        df_enriched["avg_order_value"] = df_enriched["avg_order_value"].fillna(0.0)
        df_enriched["days_since_last_order"] = df_enriched["days_since_last_order"].fillna(999).astype(int)
        df_enriched["customer_tier"] = df_enriched["customer_tier"].fillna("Bronze")

        return df_enriched

    @staticmethod
    def enrich_products(
        df_products: pd.DataFrame,
        df_orders: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Enriches product dimension with performance metrics:
        - Total Units Sold
        - Total Generated Revenue
        - Revenue Rank
        """
        if df_orders.empty:
            df_prod_enriched = df_products.copy()
            df_prod_enriched["total_units_sold"] = 0
            df_prod_enriched["total_revenue"] = 0.0
            return df_prod_enriched

        agg_df = (
            df_orders.groupby("product_id")
            .agg(
                total_units_sold=("quantity", "sum"),
                total_revenue=("total_amount", "sum"),
            )
            .reset_index()
        )

        agg_df["total_revenue"] = agg_df["total_revenue"].round(2)
        df_enriched = pd.merge(df_products, agg_df, on="product_id", how="left")
        df_enriched["total_units_sold"] = df_enriched["total_units_sold"].fillna(0).astype(int)
        df_enriched["total_revenue"] = df_enriched["total_revenue"].fillna(0.0)

        return df_enriched
