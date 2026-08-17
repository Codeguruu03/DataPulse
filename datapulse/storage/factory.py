"""
Storage client factory for dynamic backend initialization.
"""

from typing import Optional
from datapulse.storage.base import BaseStorage
from datapulse.storage.local import LocalStorage
from datapulse.storage.s3 import S3Storage
from datapulse.config import settings


def get_storage_client(backend: Optional[str] = None) -> BaseStorage:
    """Instantiates and returns the configured storage client backend."""
    selected_backend = (backend or settings.STORAGE_BACKEND).lower()

    if selected_backend == "s3":
        return S3Storage(
            bucket_name=settings.S3_BUCKET_NAME,
            region_name=settings.AWS_REGION,
        )
    elif selected_backend == "local":
        return LocalStorage(base_path=str(settings.BASE_DIR))
    else:
        raise ValueError(f"Unsupported storage backend: '{selected_backend}'. Choose 'local' or 's3'.")
