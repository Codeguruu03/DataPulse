"""Test settings and configuration loading."""
from datapulse.config import Settings


def test_default_settings():
    config = Settings()
    assert config.APP_NAME == "DataPulse"
    assert config.QUALITY_THRESHOLD_PERCENT == 95.0
    assert config.STORAGE_BACKEND == "local"
    assert config.WAREHOUSE_BACKEND == "postgres"
    assert "datapulse_dw" in config.DATABASE_URL
