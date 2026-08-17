"""
Pydantic Data Models and Schema Contracts for DataPulse.

Enforces strict structural rules, data typing, bounds validation, and serialization contracts.
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class CustomerSegment(str, Enum):
    CONSUMER = "Consumer"
    CORPORATE = "Corporate"
    HOME_OFFICE = "Home Office"
    SMALL_BUSINESS = "Small Business"


class OrderStatus(str, Enum):
    COMPLETED = "Completed"
    PENDING = "Pending"
    PROCESSING = "Processing"
    SHIPPED = "Shipped"
    CANCELLED = "Cancelled"
    REFUNDED = "Refunded"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "Credit Card"
    DEBIT_CARD = "Debit Card"
    UPI = "UPI"
    NET_BANKING = "Net Banking"
    WALLET = "Wallet"
    CASH_ON_DELIVERY = "Cash on Delivery"


# ==========================================
# Raw Schemas (Permissive string-based for ingestion)
# ==========================================

class RawCustomer(BaseModel):
    customer_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    country: Optional[str] = None
    segment: Optional[str] = None
    signup_date: Optional[str] = None
    is_active: Optional[str] = None


class RawProduct(BaseModel):
    product_id: Optional[str] = None
    sku: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[str] = None
    cost_price: Optional[str] = None
    in_stock: Optional[str] = None


class RawOrder(BaseModel):
    order_id: Optional[str] = None
    customer_id: Optional[str] = None
    product_id: Optional[str] = None
    quantity: Optional[str] = None
    unit_price: Optional[str] = None
    discount_rate: Optional[str] = None
    total_amount: Optional[str] = None
    order_date: Optional[str] = None
    order_status: Optional[str] = None
    payment_method: Optional[str] = None


# ==========================================
# Clean Schemas (Strictly validated & typed)
# ==========================================

class CleanCustomer(BaseModel):
    customer_id: str = Field(..., min_length=3, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=5, max_length=255)
    country: str = Field(..., min_length=2, max_length=100)
    segment: CustomerSegment
    signup_date: date
    is_active: bool = True

    @field_validator("country")
    @classmethod
    def standardize_country(cls, v: str) -> str:
        v_clean = v.strip().title()
        mappings = {
            "Us": "United States",
            "Usa": "United States",
            "United States Of America": "United States",
            "Uk": "United Kingdom",
            "In": "India",
            "Ind": "India",
            "De": "Germany",
            "Ca": "Canada",
        }
        return mappings.get(v_clean, v_clean)


class CleanProduct(BaseModel):
    product_id: str = Field(..., min_length=3, max_length=50)
    sku: str = Field(..., min_length=3, max_length=50)
    product_name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    unit_price: float = Field(..., gt=0.0)
    cost_price: float = Field(..., ge=0.0)
    in_stock: int = Field(..., ge=0)

    @property
    def profit_margin(self) -> float:
        if self.unit_price > 0:
            return round((self.unit_price - self.cost_price) / self.unit_price * 100, 2)
        return 0.0


class CleanOrder(BaseModel):
    order_id: str = Field(..., min_length=3, max_length=50)
    customer_id: str = Field(..., min_length=3, max_length=50)
    product_id: str = Field(..., min_length=3, max_length=50)
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0.0)
    discount_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    total_amount: float = Field(..., ge=0.0)
    order_date: datetime
    order_status: OrderStatus
    payment_method: PaymentMethod

    # Derived partition helpers
    @property
    def year(self) -> int:
        return self.order_date.year

    @property
    def month(self) -> int:
        return self.order_date.month

    @property
    def day(self) -> int:
        return self.order_date.day


# ==========================================
# Quality & Quarantine Schemas
# ==========================================

class QuarantineRecord(BaseModel):
    quarantine_id: str
    pipeline_run_id: str
    source_file: str
    dataset_type: str  # 'orders', 'customers', 'products'
    raw_payload: Dict[str, Any]
    error_reasons: List[str]
    quarantine_timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None


class DataQualityMetric(BaseModel):
    check_name: str
    dataset: str
    status: str  # PASSED, FAILED, WARNING
    records_checked: int
    records_passed: int
    records_failed: int
    pass_rate: float
    threshold: float
    details: Optional[Dict[str, Any]] = None


class PipelineRunSummary(BaseModel):
    run_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: str  # SUCCESS, FAILED_QUALITY_GATE, ERROR
    total_records_ingested: int = 0
    total_records_valid: int = 0
    total_records_quarantined: int = 0
    overall_quality_score: float = 0.0
    quality_threshold: float = 95.0
    metrics: List[DataQualityMetric] = []
