"""
Central Configuration Module for DataPulse.

Supports configuration loading from environment variables, .env files, and CLI parameters.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "DataPulse"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Deployment mode: 'local' or 'aws'
    DEPLOYMENT_MODE: str = Field(default="local", description="local or aws")

    # Storage Settings
    STORAGE_BACKEND: str = Field(default="local", description="local or s3")
    LOCAL_STORAGE_PATH: str = Field(default="./data", description="Base local data storage path")
    S3_BUCKET_NAME: str = Field(default="datapulse-data-lake-dev", description="S3 Bucket for cloud mode")
    AWS_REGION: str = Field(default="us-east-1", description="AWS Region")

    # Warehouse Settings
    WAREHOUSE_BACKEND: str = Field(default="postgres", description="postgres or redshift")
    WAREHOUSE_HOST: str = Field(default="localhost", description="Database host")
    WAREHOUSE_PORT: int = Field(default=5432, description="Database port")
    WAREHOUSE_DB: str = Field(default="datapulse_dw", description="Database name")
    WAREHOUSE_USER: str = Field(default="postgres", description="Database user")
    WAREHOUSE_PASSWORD: str = Field(default="postgres", description="Database password")
    WAREHOUSE_SCHEMA: str = Field(default="analytics", description="Database schema")

    # Processing Engine Settings
    PROCESSING_ENGINE: str = Field(default="spark", description="spark or pandas")
    SPARK_MASTER: str = Field(default="local[*]", description="Spark master URL")
    SPARK_APP_NAME: str = Field(default="DataPulse-ETL", description="Spark application name")

    # Quality Gate Thresholds
    QUALITY_THRESHOLD_PERCENT: float = Field(default=95.0, description="Minimum data quality pass rate (%)")
    MAX_DUPLICATE_RATE: float = Field(default=0.02, description="Max allowed duplicate rate (2%)")
    MAX_NULL_KEY_RATE: float = Field(default=0.00, description="Max allowed null primary key rate (0%)")

    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", description="FastAPI host")
    API_PORT: int = Field(default=8000, description="FastAPI port")

    # Base Paths
    @property
    def BASE_DIR(self) -> Path:
        return Path(__file__).resolve().parent.parent

    @property
    def RAW_DATA_PATH(self) -> Path:
        return Path(self.LOCAL_STORAGE_PATH) / "raw"

    @property
    def PROCESSED_DATA_PATH(self) -> Path:
        return Path(self.LOCAL_STORAGE_PATH) / "processed"

    @property
    def QUARANTINE_DATA_PATH(self) -> Path:
        return Path(self.LOCAL_STORAGE_PATH) / "quarantine"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.WAREHOUSE_USER}:{self.WAREHOUSE_PASSWORD}@"
            f"{self.WAREHOUSE_HOST}:{self.WAREHOUSE_PORT}/{self.WAREHOUSE_DB}"
        )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton settings instance
settings = Settings()
