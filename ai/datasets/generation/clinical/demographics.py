"""
demographics.py — Generate patient demographic features.

Generates:
    - Patient_ID (unique string identifiers)
    - Age (integer, 18–85, weighted distribution)
    - Gender (categorical, Male/Female, balanced 50/50)

All distributions follow the Dataset Design Specification.
"""

import numpy as np
from numpy.random import Generator
from typing import Dict

from . import config


def generate_patient_ids(n: int) -> np.ndarray:
    """Generate unique patient identifiers in format P00001 to P{n}.

    Args:
        n: Number of patients to generate.

    Returns:
        Array of string patient IDs.

    Raises:
        ValueError: If n is not positive.
    """
    if n <= 0:
        raise ValueError(f"Number of patients must be positive, got {n}")

    return np.array([f"P{i:05d}" for i in range(1, n + 1)], dtype=object)


def generate_ages(n: int, rng: Generator) -> np.ndarray:
    """Generate patient ages using weighted age-bin distribution.

    Distribution from specification:
        18–30: 20%, 31–45: 30%, 46–60: 30%, 61–85: 20%
    Ages are uniformly distributed within each bin.

    Args:
        n: Number of patients.
        rng: NumPy random generator for reproducibility.

    Returns:
        Array of integer ages.

    Raises:
        ValueError: If n is not positive.
    """
    if n <= 0:
        raise ValueError(f"Number of patients must be positive, got {n}")

    ages = np.empty(n, dtype=int)

    # Assign each patient to an age bin
    bin_indices = rng.choice(
        len(config.AGE_BINS),
        size=n,
        p=config.AGE_WEIGHTS,
    )

    # Generate uniform age within each bin
    for bin_idx, (age_min, age_max) in enumerate(config.AGE_BINS):
        mask = bin_indices == bin_idx
        count = mask.sum()
        if count > 0:
            ages[mask] = rng.integers(age_min, age_max + 1, size=count)

    return ages


def generate_genders(n: int, rng: Generator) -> np.ndarray:
    """Generate patient genders with configurable male probability.

    Args:
        n: Number of patients.
        rng: NumPy random generator for reproducibility.

    Returns:
        Array of gender strings ("Male" or "Female").

    Raises:
        ValueError: If n is not positive.
    """
    if n <= 0:
        raise ValueError(f"Number of patients must be positive, got {n}")

    is_male = rng.random(n) < config.MALE_PROBABILITY
    genders = np.where(is_male, "Male", "Female")
    return genders


def generate_demographics(n: int, rng: Generator) -> Dict[str, np.ndarray]:
    """Generate all demographic features for n patients.

    This is the main entry point for the demographics module.

    Args:
        n: Number of patients.
        rng: NumPy random generator.

    Returns:
        Dictionary with keys: Patient_ID, Age, Gender.
    """
    return {
        "Patient_ID": generate_patient_ids(n),
        "Age": generate_ages(n, rng),
        "Gender": generate_genders(n, rng),
    }
