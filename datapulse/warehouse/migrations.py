"""
Schema Migration & Analytical Data Mart View Definitions.
"""

from datetime import date, timedelta
from typing import Optional
from sqlalchemy import text
from datapulse.warehouse.models import Base, DimDate
from datapulse.warehouse.db import DatabaseManager, default_db_manager
from datapulse.utils.logger import get_logger

logger = get_logger("datapulse.warehouse.migrations")


class SchemaMigrator:
    """Manages creation of Star Schema tables, DimDate population, and analytical view creation."""

    def __init__(self, db_mgr: Optional[DatabaseManager] = None):
        self.db_mgr = db_mgr or default_db_manager

    def init_schema(self) -> None:
        """Creates all warehouse tables and analytical view marts."""
        logger.info("Initializing DataPulse Star Schema tables...")
        Base.metadata.create_all(self.db_mgr.engine)
        self.populate_dim_date()
        self.create_analytical_views()
        logger.info("Warehouse Star Schema & Marts initialized successfully.")

    def populate_dim_date(self, start_year: int = 2023, end_year: int = 2027) -> None:
        """Populates the Date dimension table with precomputed calendar attributes."""
        session = self.db_mgr.get_session()
        try:
            # Check if already populated
            if session.query(DimDate).count() > 0:
                return

            logger.info(f"Populating dim_date dimension from {start_year} to {end_year}...")
            start_date = date(start_year, 1, 1)
            end_date = date(end_year, 12, 31)
            curr = start_date

            date_records = []
            while curr <= end_date:
                date_key = int(curr.strftime("%Y%m%d"))
                quarter = (curr.month - 1) // 3 + 1
                date_records.append(
                    DimDate(
                        date_key=date_key,
                        full_date=curr,
                        year=curr.year,
                        quarter=quarter,
                        month=curr.month,
                        month_name=curr.strftime("%B"),
                        day=curr.day,
                        day_of_week=curr.weekday(),
                        day_name=curr.strftime("%A"),
                        is_weekend=curr.weekday() >= 5,
                    )
                )
                curr += timedelta(days=1)

            session.bulk_save_objects(date_records)
            session.commit()
            logger.info(f"Populated {len(date_records)} calendar dates into dim_date.")
        except Exception as e:
            session.rollback()
            logger.error(f"Error populating dim_date: {e}")
            raise
        finally:
            session.close()

    def create_analytical_views(self) -> None:
        """Creates SQL Analytical Mart Views."""
        views_sql = [
            # 1. Monthly Revenue Mart
            """
            CREATE VIEW IF NOT EXISTS v_mart_monthly_revenue AS
            SELECT 
                d.year,
                d.month,
                d.month_name,
                COUNT(f.order_key) AS total_orders,
                COUNT(DISTINCT f.customer_id) AS distinct_customers,
                ROUND(SUM(f.total_amount), 2) AS total_revenue,
                ROUND(AVG(f.total_amount), 2) AS avg_order_value
            FROM fact_orders f
            JOIN dim_date d ON f.date_key = d.date_key
            GROUP BY d.year, d.month, d.month_name
            ORDER BY d.year DESC, d.month DESC;
            """,
            # 2. Product Performance Mart
            """
            CREATE VIEW IF NOT EXISTS v_mart_top_products AS
            SELECT 
                p.product_id,
                p.product_name,
                p.category,
                p.unit_price,
                p.profit_margin_pct,
                COUNT(f.order_key) AS order_count,
                SUM(f.quantity) AS units_sold,
                ROUND(SUM(f.total_amount), 2) AS gross_revenue
            FROM dim_products p
            LEFT JOIN fact_orders f ON p.product_id = f.product_id
            GROUP BY p.product_id, p.product_name, p.category, p.unit_price, p.profit_margin_pct
            ORDER BY gross_revenue DESC;
            """,
            # 3. Customer Segment Analytics Mart
            """
            CREATE VIEW IF NOT EXISTS v_mart_customer_retention AS
            SELECT 
                c.segment,
                c.customer_tier,
                COUNT(DISTINCT c.customer_id) AS total_customers,
                ROUND(SUM(c.total_spend), 2) AS aggregate_spend,
                ROUND(AVG(c.total_spend), 2) AS avg_customer_spend,
                ROUND(AVG(c.avg_order_value), 2) AS avg_order_value
            FROM dim_customers c
            GROUP BY c.segment, c.customer_tier
            ORDER BY aggregate_spend DESC;
            """,
            # 4. Data Quality Audit Trend Mart
            """
            CREATE VIEW IF NOT EXISTS v_mart_quality_trends AS
            SELECT 
                run_id,
                DATE(evaluated_at) AS audit_date,
                COUNT(audit_id) AS checks_executed,
                SUM(records_checked) AS total_records_checked,
                SUM(records_passed) AS total_records_passed,
                SUM(records_failed) AS total_records_failed,
                ROUND(AVG(pass_rate), 2) AS avg_check_pass_rate
            FROM data_quality_audit
            GROUP BY run_id, DATE(evaluated_at)
            ORDER BY audit_date DESC;
            """,
        ]

        with self.db_mgr.engine.connect() as conn:
            for sql in views_sql:
                try:
                    conn.execute(text(sql))
                except Exception as e:
                    logger.warning(f"Notice on view creation: {e}")
            conn.commit()
