"""
Schema Evolution & Drift Detector.
Identifies backwards-compatible extensions vs breaking schema modifications.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Set, Dict, Any, Optional
import pandas as pd


class EvolutionVerdict(str, Enum):
    NO_CHANGE = "NO_CHANGE"
    COMPATIBLE_EXTENSION = "COMPATIBLE_EXTENSION"
    BREAKING_CHANGE = "BREAKING_CHANGE"


@dataclass
class SchemaDiffReport:
    dataset: str
    verdict: EvolutionVerdict
    action: str  # 'CONTINUE' or 'HALT'
    baseline_columns: List[str]
    incoming_columns: List[str]
    added_columns: List[str] = field(default_factory=list)
    removed_columns: List[str] = field(default_factory=list)
    missing_required_columns: List[str] = field(default_factory=list)
    message: str = ""


class SchemaEvolutionDetector:
    """Detects schema drift and governs compatibility policies."""

    BASELINE_SCHEMAS: Dict[str, Dict[str, Any]] = {
        "orders": {
            "required": ["order_id", "customer_id", "product_id", "quantity", "unit_price", "order_date"],
            "optional": ["discount_rate", "total_amount", "order_status", "payment_method"],
        },
        "customers": {
            "required": ["customer_id", "name", "email"],
            "optional": ["country", "segment", "signup_date", "is_active"],
        },
        "products": {
            "required": ["product_id", "sku", "product_name", "unit_price"],
            "optional": ["category", "cost_price", "in_stock"],
        },
    }

    def evaluate_schema(self, dataset: str, df: pd.DataFrame) -> SchemaDiffReport:
        """Evaluates incoming DataFrame columns against the baseline contract."""
        baseline = self.BASELINE_SCHEMAS.get(dataset)
        if not baseline:
            raise ValueError(f"Unknown dataset '{dataset}' for schema evolution check.")

        required_cols = set(baseline["required"])
        optional_cols = set(baseline.get("optional", []))
        all_baseline_cols = required_cols | optional_cols
        
        incoming_cols = set(df.columns)

        added = list(incoming_cols - all_baseline_cols)
        removed = list(all_baseline_cols - incoming_cols)
        missing_required = list(required_cols - incoming_cols)

        if missing_required:
            verdict = EvolutionVerdict.BREAKING_CHANGE
            action = "HALT"
            message = f"Breaking Schema Change: Missing required columns: {missing_required}"
        elif added:
            verdict = EvolutionVerdict.COMPATIBLE_EXTENSION
            action = "CONTINUE"
            message = f"Compatible Schema Extension: Added columns {added} with default null-handling."
        elif removed:
            # Optional columns were removed
            verdict = EvolutionVerdict.COMPATIBLE_EXTENSION
            action = "CONTINUE"
            message = f"Compatible Schema Change: Optional columns {removed} dropped."
        else:
            verdict = EvolutionVerdict.NO_CHANGE
            action = "CONTINUE"
            message = "Schema strictly matches baseline contract."

        return SchemaDiffReport(
            dataset=dataset,
            verdict=verdict,
            action=action,
            baseline_columns=sorted(list(all_baseline_cols)),
            incoming_columns=sorted(list(incoming_cols)),
            added_columns=sorted(added),
            removed_columns=sorted(removed),
            missing_required_columns=sorted(missing_required),
            message=message,
        )
