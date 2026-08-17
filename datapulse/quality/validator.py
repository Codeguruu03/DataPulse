"""
Data Quality Validator executing comprehensive quality checks across multi-source datasets.
"""

from typing import Tuple, List, Dict, Any, Set
import pandas as pd
from datapulse.quality.rules import RuleEngine, ValidationRuleResult
from datapulse.schemas.models import DataQualityMetric, OrderStatus, PaymentMethod, CustomerSegment
from datapulse.utils.logger import get_logger

logger = get_logger("datapulse.quality.validator")


class DataQualityValidator:
    """Executes schema, domain, and referential integrity validations."""

    def __init__(self):
        self.metrics: List[DataQualityMetric] = []

    def _record_metric(
        self,
        dataset: str,
        rule_res: ValidationRuleResult,
        total_records: int,
    ) -> None:
        failed_count = len(rule_res.failed_indices)
        passed_count = total_records - failed_count
        pass_rate = round((passed_count / total_records * 100), 2) if total_records > 0 else 100.0

        self.metrics.append(
            DataQualityMetric(
                check_name=f"{rule_res.rule_name}:{rule_res.column}",
                dataset=dataset,
                status="PASSED" if rule_res.is_valid else "FAILED",
                records_checked=total_records,
                records_passed=passed_count,
                records_failed=failed_count,
                pass_rate=pass_rate,
                threshold=99.0 if "null" in rule_res.rule_name or "unique" in rule_res.rule_name else 95.0,
                details={"error_message": rule_res.error_message},
            )
        )

    def validate_customers(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]], Dict[int, List[str]]]:
        """Validates customer master records."""
        total_records = len(df)
        failing_map: Dict[int, List[str]] = {}

        # 1. customer_id not null
        r1 = RuleEngine.check_not_null(df, "customer_id")
        self._record_metric("customers", r1, total_records)
        for idx in r1.failed_indices:
            failing_map.setdefault(idx, []).append("customer_id is null or empty")

        # 2. customer_id unique
        r2 = RuleEngine.check_unique(df, "customer_id")
        self._record_metric("customers", r2, total_records)
        for idx in r2.failed_indices:
            failing_map.setdefault(idx, []).append("duplicate customer_id")

        # 3. email not null and basic format
        r3 = RuleEngine.check_not_null(df, "email")
        self._record_metric("customers", r3, total_records)
        for idx in r3.failed_indices:
            failing_map.setdefault(idx, []).append("missing or empty email")

        # Separate valid vs quarantined
        all_failed_indices = set(failing_map.keys())
        valid_df = df.drop(index=list(all_failed_indices)).copy()
        
        quarantined_rows = []
        quarantine_error_map: Dict[int, List[str]] = {}
        for q_idx, original_idx in enumerate(all_failed_indices):
            quarantined_rows.append(df.loc[original_idx].to_dict())
            quarantine_error_map[q_idx] = failing_map[original_idx]

        return valid_df, quarantined_rows, quarantine_error_map

    def validate_products(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]], Dict[int, List[str]]]:
        """Validates product catalog records."""
        total_records = len(df)
        failing_map: Dict[int, List[str]] = {}

        # 1. product_id not null
        r1 = RuleEngine.check_not_null(df, "product_id")
        self._record_metric("products", r1, total_records)
        for idx in r1.failed_indices:
            failing_map.setdefault(idx, []).append("product_id is null or empty")

        # 2. product_id unique
        r2 = RuleEngine.check_unique(df, "product_id")
        self._record_metric("products", r2, total_records)
        for idx in r2.failed_indices:
            failing_map.setdefault(idx, []).append("duplicate product_id")

        # 3. unit_price positive
        r3 = RuleEngine.check_positive_numeric(df, "unit_price", strictly_positive=True)
        self._record_metric("products", r3, total_records)
        for idx in r3.failed_indices:
            failing_map.setdefault(idx, []).append("unit_price must be > 0")

        all_failed_indices = set(failing_map.keys())
        valid_df = df.drop(index=list(all_failed_indices)).copy()

        quarantined_rows = []
        quarantine_error_map: Dict[int, List[str]] = {}
        for q_idx, original_idx in enumerate(all_failed_indices):
            quarantined_rows.append(df.loc[original_idx].to_dict())
            quarantine_error_map[q_idx] = failing_map[original_idx]

        return valid_df, quarantined_rows, quarantine_error_map

    def validate_orders(
        self,
        df: pd.DataFrame,
        valid_customer_ids: Set[str],
        valid_product_ids: Set[str],
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]], Dict[int, List[str]]]:
        """Validates order transactions including referential integrity."""
        total_records = len(df)
        failing_map: Dict[int, List[str]] = {}

        # 1. order_id not null
        r1 = RuleEngine.check_not_null(df, "order_id")
        self._record_metric("orders", r1, total_records)
        for idx in r1.failed_indices:
            failing_map.setdefault(idx, []).append("order_id is null or empty")

        # 2. order_id unique
        r2 = RuleEngine.check_unique(df, "order_id")
        self._record_metric("orders", r2, total_records)
        for idx in r2.failed_indices:
            failing_map.setdefault(idx, []).append("duplicate order_id")

        # 3. customer_id not null
        r3 = RuleEngine.check_not_null(df, "customer_id")
        self._record_metric("orders", r3, total_records)
        for idx in r3.failed_indices:
            failing_map.setdefault(idx, []).append("customer_id is null")

        # 4. quantity strictly positive (>0)
        r4 = RuleEngine.check_positive_numeric(df, "quantity", strictly_positive=True)
        self._record_metric("orders", r4, total_records)
        for idx in r4.failed_indices:
            failing_map.setdefault(idx, []).append("quantity must be greater than 0")

        # 5. unit_price strictly positive (>0)
        r5 = RuleEngine.check_positive_numeric(df, "unit_price", strictly_positive=True)
        self._record_metric("orders", r5, total_records)
        for idx in r5.failed_indices:
            failing_map.setdefault(idx, []).append("unit_price must be greater than 0")

        # 6. order_date valid timestamp
        r6 = RuleEngine.check_valid_datetime(df, "order_date")
        self._record_metric("orders", r6, total_records)
        for idx in r6.failed_indices:
            failing_map.setdefault(idx, []).append("invalid or unparseable order_date format")

        # 7. referential integrity: customer_id exists in valid customers
        r7 = RuleEngine.check_referential_integrity(df, "customer_id", valid_customer_ids)
        self._record_metric("orders", r7, total_records)
        for idx in r7.failed_indices:
            failing_map.setdefault(idx, []).append("orphaned customer_id (not in customer master)")

        # 8. referential integrity: product_id exists in valid products
        r8 = RuleEngine.check_referential_integrity(df, "product_id", valid_product_ids)
        self._record_metric("orders", r8, total_records)
        for idx in r8.failed_indices:
            failing_map.setdefault(idx, []).append("orphaned product_id (not in product catalog)")

        # 9. allowed order_status
        allowed_statuses = set(s.value for s in OrderStatus)
        r9 = RuleEngine.check_allowed_values(df, "order_status", allowed_statuses)
        self._record_metric("orders", r9, total_records)
        for idx in r9.failed_indices:
            failing_map.setdefault(idx, []).append("order_status not in allowed business statuses")

        all_failed_indices = set(failing_map.keys())
        valid_df = df.drop(index=list(all_failed_indices)).copy()

        quarantined_rows = []
        quarantine_error_map: Dict[int, List[str]] = {}
        for q_idx, original_idx in enumerate(all_failed_indices):
            quarantined_rows.append(df.loc[original_idx].to_dict())
            quarantine_error_map[q_idx] = failing_map[original_idx]

        return valid_df, quarantined_rows, quarantine_error_map
