"""
Tests for Airflow DAG definitions and Pipeline Orchestration Runner.
"""

from pathlib import Path
import pytest
from datapulse.orchestration.runner import PipelineRunner
from datapulse.config import settings


def test_pipeline_runner_success(tmp_path: Path):
    # Run with standard 5% anomaly rate and 90% quality threshold (should PASS)
    runner = PipelineRunner(quality_threshold=90.0, auto_generate=True, anomaly_rate=0.05)
    result = runner.run(run_id="test-run-orchestrator-pass")

    assert result["status"] == "SUCCESS"
    assert "quality_gate" in result["stages"]
    assert result["stages"]["quality_gate"]["status"] == "PASSED"
    assert "transformation" in result["stages"]
    assert "warehouse_load" in result["stages"]


def test_pipeline_runner_circuit_breaker_halt(tmp_path: Path):
    # Run with 40% anomaly rate and strict 99% threshold (should TRIGGER CIRCUIT BREAKER and HALT)
    runner = PipelineRunner(quality_threshold=99.0, auto_generate=True, anomaly_rate=0.40)
    result = runner.run(run_id="test-run-circuit-breaker")

    assert result["status"] == "BLOCKED_BY_QUALITY_GATE"
    assert result["stages"]["quality_gate"]["status"] == "FAILED"
    # Transformation and warehouse load must NOT have run
    assert "transformation" not in result["stages"]
    assert "warehouse_load" not in result["stages"]
