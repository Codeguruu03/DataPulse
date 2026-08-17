"""
Amazon S3 Storage Adapter for Cloud Deployment Mode.
"""

import io
import json
from typing import List, Dict, Any, Optional
import pandas as pd

from datapulse.storage.base import BaseStorage
from datapulse.utils.logger import get_logger

logger = get_logger("datapulse.storage.s3")


class S3Storage(BaseStorage):
    """Storage adapter for AWS S3 object store operations."""

    def __init__(self, bucket_name: str, region_name: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.region_name = region_name
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client("s3", region_name=self.region_name)
            except Exception as e:
                logger.warning(f"boto3 initialization warning: {e}. S3 operations require configured AWS credentials.")
                raise
        return self._client

    def _parse_s3_key(self, path: str) -> str:
        if path.startswith("s3://"):
            parts = path[5:].split("/", 1)
            return parts[1] if len(parts) > 1 else ""
        return path.lstrip("/")

    def read_csv(self, path: str) -> pd.DataFrame:
        key = self._parse_s3_key(path)
        obj = self.client.get_object(Bucket=self.bucket_name, Key=key)
        return pd.read_csv(io.BytesIO(obj["Body"].read()), dtype=str)

    def write_csv(self, df: pd.DataFrame, path: str, index: bool = False) -> str:
        key = self._parse_s3_key(path)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=index)
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=csv_buffer.getvalue().encode("utf-8"),
            ContentType="text/csv",
        )
        return f"s3://{self.bucket_name}/{key}"

    def write_parquet(
        self,
        df: pd.DataFrame,
        path: str,
        partition_cols: Optional[List[str]] = None,
        index: bool = False,
    ) -> str:
        key = self._parse_s3_key(path)
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=index, engine="pyarrow", compression="snappy")
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=buffer.getvalue(),
            ContentType="application/octet-stream",
        )
        return f"s3://{self.bucket_name}/{key}"

    def read_parquet(self, path: str) -> pd.DataFrame:
        key = self._parse_s3_key(path)
        obj = self.client.get_object(Bucket=self.bucket_name, Key=key)
        return pd.read_parquet(io.BytesIO(obj["Body"].read()), engine="pyarrow")

    def write_json(self, data: Any, path: str) -> str:
        key = self._parse_s3_key(path)
        json_bytes = json.dumps(data, indent=2, default=str).encode("utf-8")
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=json_bytes,
            ContentType="application/json",
        )
        return f"s3://{self.bucket_name}/{key}"

    def read_json(self, path: str) -> Any:
        key = self._parse_s3_key(path)
        obj = self.client.get_object(Bucket=self.bucket_name, Key=key)
        return json.loads(obj["Body"].read().decode("utf-8"))

    def list_files(self, prefix: str, suffix: Optional[str] = None) -> List[str]:
        s3_prefix = self._parse_s3_key(prefix)
        paginator = self.client.get_paginator("list_objects_v2")
        keys = []
        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=s3_prefix):
            for item in page.get("Contents", []):
                key = item["Key"]
                if suffix is None or key.endswith(suffix):
                    keys.append(f"s3://{self.bucket_name}/{key}")
        return keys

    def exists(self, path: str) -> bool:
        key = self._parse_s3_key(path)
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception:
            return False
