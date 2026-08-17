"""
Quarantine Manager for isolating and persisting invalid records.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from datapulse.storage.base import BaseStorage
from datapulse.config import settings
from datapulse.utils.logger import get_logger

logger = get_logger("datapulse.quality.quarantine")


class QuarantineManager:
    """Manages recording, formatting, and persisting corrupted rows to the quarantine data zone."""

    def __init__(self, storage: BaseStorage):
        self.storage = storage

    def save_quarantine_batch(
        self,
        run_id: str,
        dataset_name: str,
        quarantined_rows: List[Dict[str, Any]],
        error_map: Dict[int, List[str]],
    ) -> Optional[str]:
        """
        Saves quarantined rows with detailed error reasons to CSV and JSON audit trails.
        """
        if not quarantined_rows:
            logger.info(f"No records quarantined for dataset '{dataset_name}'.")
            return None

        # Build enriched quarantine records
        enriched_records = []
        for idx, row in enumerate(quarantined_rows):
            reasons = error_map.get(idx, ["Unspecified validation failure"])
            enriched_records.append({
                "quarantine_id": f"Q-{run_id}-{dataset_name}-{idx:05d}",
                "run_id": run_id,
                "dataset": dataset_name,
                "quarantine_timestamp": datetime.utcnow().isoformat(),
                "error_reasons": " | ".join(reasons),
                **row,
            })

        df_quarantine = pd.DataFrame(enriched_records)
        quarantine_file_csv = f"quarantine/quarantine_{dataset_name}.csv"
        quarantine_file_json = f"quarantine/quarantine_audit_{run_id}_{dataset_name}.json"


        # Write to storage
        self.storage.write_csv(df_quarantine, quarantine_file_csv)
        self.storage.write_json(enriched_records, quarantine_file_json)

        logger.warning(
            f"Quarantined {len(enriched_records)} invalid records for '{dataset_name}' -> {quarantine_file_csv}"
        )
        return quarantine_file_csv
