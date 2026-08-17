"""
Spark Session Management for DataPulse.
Configures PySpark local or cluster execution with optimized Parquet settings.
"""

from typing import Optional
from datapulse.config import settings
from datapulse.utils.logger import get_logger

logger = get_logger("datapulse.transforms.spark")


def get_spark_session(app_name: Optional[str] = None):
    """
    Initializes or retrieves an active SparkSession.
    Returns PySpark SparkSession if available, or None with fallback support.
    """
    name = app_name or settings.SPARK_APP_NAME
    try:
        from pyspark.sql import SparkSession

        spark = (
            SparkSession.builder.appName(name)
            .master("local[2]")
            .config("spark.driver.bindAddress", "127.0.0.1")
            .config("spark.driver.host", "127.0.0.1")
            .config("spark.sql.parquet.compression.codec", "snappy")
            .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
            .config("spark.driver.memory", "1g")
            .config("spark.sql.shuffle.partitions", "2")
            .getOrCreate()
        )
        try:
            spark.sparkContext.setLogLevel("ERROR")
        except Exception:
            pass
        logger.info(f"Initialized PySpark Session [{name}] with master [local[2]]")
        return spark
    except Exception as e:
        logger.warning(f"PySpark not available or Java environment not set: {e}. Falling back to vectorized engine.")
        return None
