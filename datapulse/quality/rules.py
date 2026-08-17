"""
Rule Engine for Data Quality Validations.
Defines vectorized verification checks for tabular datasets.
"""

from dataclasses import dataclass
from typing import List, Set, Any, Optional, Tuple
import pandas as pd
import numpy as np


@dataclass
class ValidationRuleResult:
    rule_name: str
    column: str
    is_valid: bool
    failed_indices: List[int]
    error_message: str


class RuleEngine:
    """Executes atomic data validation rules over pandas DataFrames."""

    @staticmethod
    def check_not_null(df: pd.DataFrame, column: str) -> ValidationRuleResult:
        """Verifies that a column contains no null, empty string, or whitespace-only values."""
        if column not in df.columns:
            return ValidationRuleResult(
                rule_name="not_null",
                column=column,
                is_valid=False,
                failed_indices=list(df.index),
                error_message=f"Missing column '{column}' in dataset",
            )
        
        series = df[column].astype(str).str.strip()
        failed_mask = df[column].isna() | (series == "") | (series.str.lower() == "nan") | (series.str.lower() == "null")
        failed_indices = list(df[failed_mask].index)

        return ValidationRuleResult(
            rule_name="not_null",
            column=column,
            is_valid=len(failed_indices) == 0,
            failed_indices=failed_indices,
            error_message=f"Column '{column}' has {len(failed_indices)} NULL/empty values",
        )

    @staticmethod
    def check_unique(df: pd.DataFrame, column: str) -> ValidationRuleResult:
        """Verifies that all non-null values in a column are strictly unique."""
        if column not in df.columns:
            return ValidationRuleResult(
                rule_name="unique",
                column=column,
                is_valid=False,
                failed_indices=list(df.index),
                error_message=f"Missing column '{column}' in dataset",
            )

        # Mark all duplicate occurrences as failed
        duplicated_mask = df.duplicated(subset=[column], keep=False) & df[column].notna()
        failed_indices = list(df[duplicated_mask].index)

        return ValidationRuleResult(
            rule_name="unique",
            column=column,
            is_valid=len(failed_indices) == 0,
            failed_indices=failed_indices,
            error_message=f"Column '{column}' has {len(failed_indices)} duplicate entries",
        )

    @staticmethod
    def check_positive_numeric(df: pd.DataFrame, column: str, strictly_positive: bool = True) -> ValidationRuleResult:
        """Verifies that numeric values are strictly positive (>0) or non-negative (>=0)."""
        if column not in df.columns:
            return ValidationRuleResult(
                rule_name="positive_numeric",
                column=column,
                is_valid=False,
                failed_indices=list(df.index),
                error_message=f"Missing column '{column}' in dataset",
            )

        numeric_vals = pd.to_numeric(df[column], errors="coerce")
        if strictly_positive:
            failed_mask = numeric_vals.isna() | (numeric_vals <= 0)
        else:
            failed_mask = numeric_vals.isna() | (numeric_vals < 0)

        failed_indices = list(df[failed_mask].index)

        return ValidationRuleResult(
            rule_name="positive_numeric",
            column=column,
            is_valid=len(failed_indices) == 0,
            failed_indices=failed_indices,
            error_message=f"Column '{column}' has {len(failed_indices)} non-positive/invalid numeric entries",
        )

    @staticmethod
    def check_valid_datetime(df: pd.DataFrame, column: str) -> ValidationRuleResult:
        """Verifies that date strings can be parsed into valid timestamps."""
        if column not in df.columns:
            return ValidationRuleResult(
                rule_name="valid_datetime",
                column=column,
                is_valid=False,
                failed_indices=list(df.index),
                error_message=f"Missing column '{column}' in dataset",
            )

        parsed_dates = pd.to_datetime(df[column], errors="coerce")
        failed_mask = parsed_dates.isna()
        failed_indices = list(df[failed_mask].index)

        return ValidationRuleResult(
            rule_name="valid_datetime",
            column=column,
            is_valid=len(failed_indices) == 0,
            failed_indices=failed_indices,
            error_message=f"Column '{column}' has {len(failed_indices)} unparseable/invalid date strings",
        )

    @staticmethod
    def check_referential_integrity(
        child_df: pd.DataFrame,
        child_col: str,
        parent_valid_keys: Set[str],
    ) -> ValidationRuleResult:
        """Verifies foreign key constraints (child key must exist in parent key set)."""
        if child_col not in child_df.columns:
            return ValidationRuleResult(
                rule_name="referential_integrity",
                column=child_col,
                is_valid=False,
                failed_indices=list(child_df.index),
                error_message=f"Missing column '{child_col}' for foreign key validation",
            )

        failed_mask = ~child_df[child_col].astype(str).isin(parent_valid_keys)
        failed_indices = list(child_df[failed_mask].index)

        return ValidationRuleResult(
            rule_name="referential_integrity",
            column=child_col,
            is_valid=len(failed_indices) == 0,
            failed_indices=failed_indices,
            error_message=f"Foreign key '{child_col}' has {len(failed_indices)} orphaned references",
        )

    @staticmethod
    def check_allowed_values(df: pd.DataFrame, column: str, allowed: Set[str]) -> ValidationRuleResult:
        """Verifies categorical membership against an allowed enum set."""
        if column not in df.columns:
            return ValidationRuleResult(
                rule_name="allowed_values",
                column=column,
                is_valid=False,
                failed_indices=list(df.index),
                error_message=f"Missing column '{column}' in dataset",
            )

        failed_mask = ~df[column].astype(str).isin(allowed)
        failed_indices = list(df[failed_mask].index)

        return ValidationRuleResult(
            rule_name="allowed_values",
            column=column,
            is_valid=len(failed_indices) == 0,
            failed_indices=failed_indices,
            error_message=f"Column '{column}' has {len(failed_indices)} values outside allowed set",
        )
