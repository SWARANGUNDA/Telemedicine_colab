"""
utils.py — Utility functions for random seed management and logging.

Provides deterministic RNG initialization using numpy.random.default_rng(),
patient-level sub-seed generation, and structured logging configuration.
"""

import logging
import sys
from typing import Optional

import numpy as np


def create_rng(seed: int) -> np.random.Generator:
    """Create a reproducible NumPy random number generator.

    Args:
        seed: Master random seed for reproducibility.

    Returns:
        A numpy.random.Generator instance seeded deterministically.
    """
    return np.random.default_rng(seed)


def create_patient_rng(master_rng: np.random.Generator,
                       patient_index: int) -> np.random.Generator:
    """Create a deterministic sub-RNG for a specific patient.

    Allows regeneration of individual patient microbiome profiles without
    affecting the global random state. Uses SeedSequence spawning.

    Args:
        master_rng: The master generator (used to derive child seeds).
        patient_index: Zero-based patient index.

    Returns:
        An independent Generator for that patient.
    """
    child_seed = np.random.SeedSequence(
        master_rng.bit_generator.seed_seq.entropy,
        spawn_key=(patient_index,),
    )
    return np.random.default_rng(child_seed)


def setup_logging(level: int = logging.INFO,
                  log_file: Optional[str] = None) -> logging.Logger:
    """Configure structured logging for the generator pipeline.

    Args:
        level: Logging level (default INFO).
        log_file: Optional file path for log output.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("gut_microbiome_generator")
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional file handler
    if log_file is not None:
        file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def clip_array(values: np.ndarray,
               lower: float,
               upper: float) -> np.ndarray:
    """Clip array values to specified bounds.

    Args:
        values: Input array.
        lower: Lower bound.
        upper: Upper bound.

    Returns:
        Clipped array.
    """
    return np.clip(values, lower, upper)


def safe_float(value: object, default: float = np.nan) -> float:
    """Safely convert a value to float, returning default on failure.

    Handles empty strings and None gracefully (common in CSV data with
    missing values).

    Args:
        value: Value to convert.
        default: Default if conversion fails.

    Returns:
        Float value or default.
    """
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
