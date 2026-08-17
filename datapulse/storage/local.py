"""
Local Filesystem Storage Implementation for DataPulse.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from datapulse.storage.base import BaseStorage
from datapulse.utils.logger import get_logger

logger = get_logger("datapulse.storage.local")


class LocalStorage(BaseStorage):
    """Storage adapter for local disk operations."""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()

    def _resolve(self, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return self.base_path / p

    def read_csv(self, path: str) -> pd.DataFrame:
        target = self._resolve(path)
        if not target.exists():
            raise FileNotFoundError(f"CSV file not found: {target}")
        return pd.read_csv(target, dtype=str)

    def write_csv(self, df: pd.DataFrame, path: str, index: bool = False) -> str:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(target, index=index, encoding="utf-8")
        return str(target)

    def write_parquet(
        self,
        df: pd.DataFrame,
        path: str,
        partition_cols: Optional[List[str]] = None,
        index: bool = False,
    ) -> str:
        import shutil
        target = self._resolve(path)
        if partition_cols:
            if target.exists() and target.is_dir():
                shutil.rmtree(target)
            target.mkdir(parents=True, exist_ok=True)
            df.to_parquet(
                target,
                partition_cols=partition_cols,
                index=index,
                engine="pyarrow",
                compression="snappy",
            )
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(
                target,
                index=index,
                engine="pyarrow",
                compression="snappy",
            )
        return str(target)


    def read_parquet(self, path: str) -> pd.DataFrame:
        target = self._resolve(path)
        if not target.exists():
            raise FileNotFoundError(f"Parquet source not found: {target}")
        return pd.read_parquet(target, engine="pyarrow")

    def write_json(self, data: Any, path: str) -> str:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return str(target)

    def read_json(self, path: str) -> Any:
        target = self._resolve(path)
        if not target.exists():
            raise FileNotFoundError(f"JSON file not found: {target}")
        with open(target, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_files(self, prefix: str, suffix: Optional[str] = None) -> List[str]:
        target = self._resolve(prefix)
        if not target.exists():
            return []
        if target.is_file():
            return [str(target)]
        
        pattern = f"*{suffix}" if suffix else "*"
        return [str(p) for p in target.glob(f"**/{pattern}") if p.is_file()]

    def exists(self, path: str) -> bool:
        return self._resolve(path).exists()
