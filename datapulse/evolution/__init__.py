"""
Schema Evolution & Drift Detection Engine for DataPulse.
"""

from datapulse.evolution.detector import (
    SchemaEvolutionDetector,
    SchemaDiffReport,
    EvolutionVerdict,
)

__all__ = ["SchemaEvolutionDetector", "SchemaDiffReport", "EvolutionVerdict"]
