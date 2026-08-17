"""Test settings and configuration loading."""
from datapulse.config import Settings


def test_default_settings():
    config = Settings()
    assert config.APP_NAME == "DataPulse"
    assert config.QUALITY_THRESHOLD_PERCENT >= 80.0
    assert config.STORAGE_BACKEND in ["local", "s3"]
    assert config.WAREHOUSE_BACKEND in ["postgres", "sqlite", "redshift"]
    assert "datapulse_dw" in config.DATABASE_URL or "datapulse" in config.DATABASE_URL
