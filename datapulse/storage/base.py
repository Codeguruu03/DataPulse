"""
Base Storage Interface defining required storage client operations.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd


class BaseStorage(ABC):
    """Abstract Base Class for DataPulse Storage Handlers."""

    @abstractmethod
    def read_csv(self, path: str) -> pd.DataFrame:
        """Reads a CSV file into a pandas DataFrame."""
        pass

    @abstractmethod
    def write_csv(self, df: pd.DataFrame, path: str, index: bool = False) -> str:
        """Writes a pandas DataFrame to CSV."""
        pass

    @abstractmethod
    def write_parquet(
        self,
        df: pd.DataFrame,
        path: str,
        partition_cols: Optional[List[str]] = None,
        index: bool = False,
    ) -> str:
        """Writes a pandas DataFrame to Parquet format."""
        pass

    @abstractmethod
    def read_parquet(self, path: str) -> pd.DataFrame:
        """Reads a Parquet file or directory into a pandas DataFrame."""
        pass

    @abstractmethod
    def write_json(self, data: Any, path: str) -> str:
        """Writes a JSON-serializable object to the storage target."""
        pass

    @abstractmethod
    def read_json(self, path: str) -> Any:
        """Reads and parses a JSON file from storage."""
        pass

    @abstractmethod
    def list_files(self, prefix: str, suffix: Optional[str] = None) -> List[str]:
        """Lists files in the designated path matching optional prefix/suffix."""
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Checks if a file or directory exists."""
        pass
