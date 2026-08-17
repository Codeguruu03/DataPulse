"""
Tests for DataPulse Storage Abstraction and Data Quality Gate Engine.
"""

from pathlib import Path
import pandas as pd
import pytest

from datapulse.storage.local import LocalStorage
from datapulse.storage.factory import get_storage_client
from datapulse.quality.rules import RuleEngine
from datapulse.quality.validator import DataQualityValidator
from datapulse.quality.gate import DataQualityGate
from datapulse.generator.generator import DataPulseGenerator


def test_storage_local_crud(tmp_path: Path):
    storage = LocalStorage(base_path=str(tmp_path))
    df = pd.DataFrame({"col_a": ["1", "2"], "col_b": ["alpha", "beta"]})

    # Test CSV write & read
    csv_file = storage.write_csv(df, "test.csv")
    assert storage.exists("test.csv")
    df_read = storage.read_csv("test.csv")
    assert len(df_read) == 2

    # Test JSON write & read
    json_file = storage.write_json({"status": "ok"}, "test.json")
    data_read = storage.read_json("test.json")
    assert data_read["status"] == "ok"


def test_rule_engine_checks():
    df = pd.DataFrame({
        "order_id": ["ORD-1", "ORD-2", "ORD-2", ""],
        "quantity": ["5", "-3", "10", "0"],
        "price": ["100.0", "50.0", "-20.0", "30.0"],
        "date": ["2024-01-01", "2024-02-01", "invalid-date", "2024-04-01"],
    })

    # Null check
    r_null = RuleEngine.check_not_null(df, "order_id")
    assert not r_null.is_valid
    assert 3 in r_null.failed_indices

    # Unique check
    r_uniq = RuleEngine.check_unique(df, "order_id")
    assert not r_uniq.is_valid
    assert 1 in r_uniq.failed_indices and 2 in r_uniq.failed_indices

    # Positive numeric check
    r_num = RuleEngine.check_positive_numeric(df, "quantity", strictly_positive=True)
    assert not r_num.is_valid
    assert 1 in r_num.failed_indices and 3 in r_num.failed_indices

    # Date check
    r_date = RuleEngine.check_valid_datetime(df, "date")
    assert not r_date.is_valid
    assert 2 in r_date.failed_indices


def test_quality_gate_end_to_end(tmp_path: Path):
    storage = LocalStorage(base_path=str(tmp_path))
    gen = DataPulseGenerator(anomaly_rate=0.05, seed=42)

    raw_dir = tmp_path / "raw"
    c_path, p_path, o_path = gen.generate_all_and_save(output_dir=raw_dir, num_orders=200, num_customers=50)

    gate = DataQualityGate(storage=storage, quality_threshold=90.0)
    passed, summary, datasets = gate.evaluate_pipeline_batch(
        raw_customers_path=str(c_path),
        raw_products_path=str(p_path),
        raw_orders_path=str(o_path),
        run_id="test-run-001",
    )

    assert summary.total_records_ingested > 200
    assert summary.total_records_valid > 0
    assert summary.total_records_quarantined > 0
    assert summary.overall_quality_score >= 90.0
    assert passed is True
    assert len(datasets["orders"]) == summary.total_records_valid - len(datasets["customers"]) - len(datasets["products"])
