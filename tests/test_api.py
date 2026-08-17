"""
Tests for DataPulse FastAPI Serving Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from datapulse.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "version" in data


def test_analytics_summary_endpoint(client):
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_revenue" in data
    assert "total_orders" in data
    assert "overall_quality_score" in data


def test_analytics_monthly_revenue_endpoint(client):
    response = client.get("/api/v1/analytics/monthly-revenue")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_quality_quarantine_endpoint(client):
    response = client.get("/api/v1/quality/quarantine?dataset=orders&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "dataset" in data
    assert "records" in data


def test_pipeline_status_and_trigger(client):
    status_resp = client.get("/api/v1/pipeline/status")
    assert status_resp.status_code == 200

    trigger_resp = client.post(
        "/api/v1/pipeline/trigger",
        json={"threshold": 95.0, "anomaly_rate": 0.05, "auto_generate": False},
    )
    assert trigger_resp.status_code == 200
    assert trigger_resp.json()["status"] == "ACCEPTED"
