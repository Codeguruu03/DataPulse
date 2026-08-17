"""
Logging configuration for DataPulse with structured formatting and console styling.
"""

import logging
import sys
from typing import Optional


def get_logger(name: str = "datapulse", level: Optional[int] = None) -> logging.Logger:
    """Returns a configured logger instance for DataPulse."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level or logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level or logging.INFO)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger
