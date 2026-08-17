"""
SQLAlchemy Star Schema ORM Models for Analytical Warehouse.
"""

from datetime import datetime, date
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DimCustomer(Base):
    __tablename__ = "dim_customers"

    customer_key = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False, index=True)
    segment = Column(String(50), nullable=False, index=True)
    signup_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    customer_tier = Column(String(50), default="Bronze")
    total_spend = Column(Float, default=0.0)
    total_orders = Column(Integer, default=0)
    avg_order_value = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    orders = relationship("FactOrder", back_populates="customer")


class DimProduct(Base):
    __tablename__ = "dim_products"

    product_key = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(50), unique=True, nullable=False, index=True)
    sku = Column(String(50), nullable=False)
    product_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    unit_price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=False)
    profit_margin_pct = Column(Float, default=0.0)
    in_stock = Column(Integer, default=0)
    total_units_sold = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    orders = relationship("FactOrder", back_populates="product")


class DimDate(Base):
    __tablename__ = "dim_date"

    date_key = Column(Integer, primary_key=True)  # Format: YYYYMMDD
    full_date = Column(Date, unique=True, nullable=False)
    year = Column(Integer, nullable=False, index=True)
    quarter = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False, index=True)
    month_name = Column(String(20), nullable=False)
    day = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    day_name = Column(String(20), nullable=False)
    is_weekend = Column(Boolean, default=False)


class FactOrder(Base):
    __tablename__ = "fact_orders"

    order_key = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(String(50), ForeignKey("dim_customers.customer_id"), nullable=False, index=True)
    product_id = Column(String(50), ForeignKey("dim_products.product_id"), nullable=False, index=True)
    date_key = Column(Integer, nullable=False, index=True)
    order_date = Column(DateTime, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount_rate = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    order_status = Column(String(50), nullable=False, index=True)
    payment_method = Column(String(50), nullable=False)
    loaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    customer = relationship("DimCustomer", back_populates="orders")
    product = relationship("DimProduct", back_populates="orders")

    __table_args__ = (
        Index("idx_orders_composite", "order_date", "customer_id", "product_id"),
    )


class DataQualityAudit(Base):
    __tablename__ = "data_quality_audit"

    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(100), nullable=False, index=True)
    check_name = Column(String(100), nullable=False)
    dataset = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    records_checked = Column(Integer, nullable=False)
    records_passed = Column(Integer, nullable=False)
    records_failed = Column(Integer, nullable=False)
    pass_rate = Column(Float, nullable=False)
    evaluated_at = Column(DateTime, default=datetime.utcnow)


class QuarantineAudit(Base):
    __tablename__ = "quarantine_audit"

    quarantine_key = Column(Integer, primary_key=True, autoincrement=True)
    quarantine_id = Column(String(100), unique=True, nullable=False, index=True)
    run_id = Column(String(100), nullable=False, index=True)
    dataset = Column(String(50), nullable=False)
    error_reasons = Column(Text, nullable=False)
    raw_record = Column(Text, nullable=False)
    quarantine_timestamp = Column(DateTime, default=datetime.utcnow)
    is_resolved = Column(Boolean, default=False)
