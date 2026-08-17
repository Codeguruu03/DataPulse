"""
Pluggable Storage Abstraction Layer for DataPulse.
Supports local filesystem and AWS S3 storage seamlessly.
"""

from datapulse.storage.base import BaseStorage
from datapulse.storage.local import LocalStorage
from datapulse.storage.s3 import S3Storage
from datapulse.storage.factory import get_storage_client

__all__ = ["BaseStorage", "LocalStorage", "S3Storage", "get_storage_client"]
