"""
Tests for Lineage Tracker, Schema Evolution, and Pipeline Replay.
"""

from pathlib import Path
import pandas as pd
import pytest

from datapulse.lineage.tracker import LineageTracker
from datapulse.evolution.detector import SchemaEvolutionDetector, EvolutionVerdict
from datapulse.replay.controller import PipelineReplayController


def test_lineage_tracker():
    tracker = LineageTracker()
    tree = tracker.trace_upstream("v_mart_monthly_revenue")

    node_names = [n["name"] for n in tree]
    assert "v_mart_monthly_revenue" in node_names
    assert "dw_fact_orders" in node_names
    assert "lake_fact_orders" in node_names
    assert "quality_gate_orders" in node_names
    assert "raw_orders" in node_names

    mermaid = tracker.generate_mermaid_diagram("v_mart_monthly_revenue")
    assert "graph TD" in mermaid
    assert "raw_orders" in mermaid


def test_schema_evolution_detector():
    detector = SchemaEvolutionDetector()

    # 1. Exact match
    df_exact = pd.DataFrame(columns=["order_id", "customer_id", "product_id", "quantity", "unit_price", "discount_rate", "total_amount", "order_date", "order_status", "payment_method"])
    rep_exact = detector.evaluate_schema("orders", df_exact)
    assert rep_exact.verdict == EvolutionVerdict.NO_CHANGE
    assert rep_exact.action == "CONTINUE"

    # 2. Compatible extension (added coupon_code)
    df_extended = pd.DataFrame(columns=["order_id", "customer_id", "product_id", "quantity", "unit_price", "discount_rate", "total_amount", "order_date", "order_status", "payment_method", "coupon_code"])
    rep_ext = detector.evaluate_schema("orders", df_extended)
    assert rep_ext.verdict == EvolutionVerdict.COMPATIBLE_EXTENSION
    assert "coupon_code" in rep_ext.added_columns
    assert rep_ext.action == "CONTINUE"

    # 3. Breaking change (missing customer_id)
    df_broken = pd.DataFrame(columns=["order_id", "product_id", "quantity", "unit_price", "order_date"])
    rep_broken = detector.evaluate_schema("orders", df_broken)
    assert rep_broken.verdict == EvolutionVerdict.BREAKING_CHANGE
    assert rep_broken.action == "HALT"
    assert "customer_id" in rep_broken.missing_required_columns


def test_pipeline_replay_execution(tmp_path: Path):
    from datapulse.storage.local import LocalStorage
    from datapulse.generator.generator import DataPulseGenerator

    storage = LocalStorage(base_path=str(tmp_path))
    gen = DataPulseGenerator(anomaly_rate=0.05, seed=10)
    raw_dir = tmp_path / "raw"
    c_f, p_f, o_f = gen.generate_all_and_save(output_dir=raw_dir, num_orders=100, num_customers=30)

    controller = PipelineReplayController(storage=storage)
    res = controller.replay_from_validation(
        replay_run_id="replay-test-001",
        threshold=90.0,
        raw_customers_path=str(c_f),
        raw_products_path=str(p_f),
        raw_orders_path=str(o_f),
    )

    assert res["status"] == "SUCCESS"
    assert res["checkpoint"] == "VALIDATION"
    assert res["orders_replayed"] > 0


