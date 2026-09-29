"""
bacteria.py — Bacterial abundance generators for beneficial, inflammatory,
and context-dependent genera.

Generates relative abundance (%) for each bacterial genus using
parameterized statistical distributions whose location and scale
parameters are modulated by the patient's latent metabolic risk score
and disease-specific shift factors.

Generation follows three pathways:
  1. Beneficial bacteria: Higher in healthy, depleted in disease.
  2. Inflammatory bacteria: Low in healthy, elevated in disease.
  3. Context-dependent bacteria: High variance, moderate disease shifts.
"""

import logging

import numpy as np
import pandas as pd

from . import constants
from .distributions import (
    sample_lognormal_bounded,
    sample_truncated_normal,
    sample_gamma_bounded,
)

logger = logging.getLogger("gut_microbiome_generator")


def generate_beneficial_bacteria(
    rng: np.random.Generator,
    risk_scores: np.ndarray,
    disease_shifts: pd.DataFrame,
    age_values: np.ndarray,
) -> pd.DataFrame:
    """Generate relative abundance for beneficial bacterial genera.

    Beneficial bacteria (Akkermansia, Faecalibacterium, Bifidobacterium,
    Roseburia, Alistipes) are abundant in metabolically healthy individuals
    and depleted in metabolic disease. Generation uses truncated normal
    distributions whose mean decreases with metabolic risk.

    Args:
        rng: NumPy random Generator.
        risk_scores: Patient-level metabolic risk in [0, 1].
        disease_shifts: Per-patient disease-specific mean shifts.
        age_values: Patient ages (used for age-related modulation).

    Returns:
        DataFrame with beneficial bacteria abundance columns.
    """
    n = len(risk_scores)
    result = pd.DataFrame(index=range(n))

    for bacterium in constants.BENEFICIAL_BACTERIA:
        base_mean, base_std = constants.HEALTHY_DISTRIBUTION[bacterium]
        lower, upper = constants.ABUNDANCE_BOUNDS[bacterium]

        # Modulate mean: decrease with increasing risk
        risk_shift = risk_scores * base_mean * 0.55
        disease_shift = disease_shifts[bacterium].values if bacterium in disease_shifts.columns else 0.0

        # Age modulation: slight decrease in beneficial bacteria with age
        age_shift = (
            (age_values - constants.AGE_REFERENCE) *
            constants.AGE_BENEFICIAL_SLOPE
        )
        age_shift = np.clip(age_shift, -1.5, 1.0)

        adjusted_mean = base_mean - risk_shift + disease_shift + age_shift
        adjusted_mean = np.clip(adjusted_mean, lower + 0.1, upper * 0.8)

        # Slightly increase variance for diseased patients
        adjusted_std = base_std * (1.0 + risk_scores * 0.3)

        # Sample per patient
        values = np.zeros(n)
        for i in range(n):
            values[i] = sample_truncated_normal(
                rng, adjusted_mean[i], adjusted_std[i],
                lower, upper, size=1,
            )[0]

        result[bacterium] = values

    return result


def generate_inflammatory_bacteria(
    rng: np.random.Generator,
    risk_scores: np.ndarray,
    disease_shifts: pd.DataFrame,
    age_values: np.ndarray,
) -> pd.DataFrame:
    """Generate relative abundance for inflammatory bacterial genera.

    Inflammatory bacteria (Escherichia_Shigella, Collinsella) are typically
    low in healthy individuals and elevated with metabolic disease and
    systemic inflammation. Uses gamma distributions for right-skewed profiles.

    Args:
        rng: NumPy random Generator.
        risk_scores: Patient-level metabolic risk in [0, 1].
        disease_shifts: Per-patient disease-specific mean shifts.
        age_values: Patient ages.

    Returns:
        DataFrame with inflammatory bacteria abundance columns.
    """
    n = len(risk_scores)
    result = pd.DataFrame(index=range(n))

    for bacterium in constants.INFLAMMATORY_BACTERIA:
        base_mean, base_std = constants.HEALTHY_DISTRIBUTION[bacterium]
        lower, upper = constants.ABUNDANCE_BOUNDS[bacterium]

        # Modulate mean: increase with risk
        risk_boost = risk_scores * base_mean * 1.8
        disease_shift = disease_shifts[bacterium].values if bacterium in disease_shifts.columns else 0.0

        # Age modulation: slight increase in inflammatory bacteria with age
        age_shift = (
            (age_values - constants.AGE_REFERENCE) *
            constants.AGE_INFLAMMATORY_SLOPE
        )
        age_shift = np.clip(age_shift, -0.5, 1.5)

        adjusted_mean = base_mean + risk_boost + disease_shift + age_shift
        adjusted_mean = np.clip(adjusted_mean, lower + 0.05, upper * 0.85)

        adjusted_std = base_std * (1.0 + risk_scores * 0.5)

        values = np.zeros(n)
        for i in range(n):
            values[i] = sample_gamma_bounded(
                rng, adjusted_mean[i], adjusted_std[i],
                lower, upper, size=1,
            )[0]

        result[bacterium] = values

    return result


def generate_context_dependent_bacteria(
    rng: np.random.Generator,
    risk_scores: np.ndarray,
    disease_shifts: pd.DataFrame,
    age_values: np.ndarray,
) -> pd.DataFrame:
    """Generate relative abundance for context-dependent bacterial genera.

    Context-dependent bacteria (Prevotella, Blautia) exhibit high
    inter-individual variability driven by diet, geography, and host
    genetics. Disease effects are moderate and inconsistent.

    Uses log-normal distributions to capture the naturally right-skewed,
    high-variance profile of these genera.

    Args:
        rng: NumPy random Generator.
        risk_scores: Patient-level metabolic risk in [0, 1].
        disease_shifts: Per-patient disease-specific mean shifts.
        age_values: Patient ages.

    Returns:
        DataFrame with context-dependent bacteria abundance columns.
    """
    n = len(risk_scores)
    result = pd.DataFrame(index=range(n))

    for bacterium in constants.CONTEXT_DEPENDENT_BACTERIA:
        base_mean, base_std = constants.HEALTHY_DISTRIBUTION[bacterium]
        lower, upper = constants.ABUNDANCE_BOUNDS[bacterium]

        # Moderate, inconsistent risk modulation
        if bacterium == "Prevotella":
            # Prevotella: slightly elevated in disease (context-dependent)
            risk_shift = risk_scores * 1.2
        else:
            # Blautia: slightly depleted in disease (emerging evidence)
            risk_shift = -risk_scores * 0.8

        disease_shift = disease_shifts[bacterium].values if bacterium in disease_shifts.columns else 0.0

        adjusted_mean = base_mean + risk_shift + disease_shift
        adjusted_mean = np.clip(adjusted_mean, lower + 0.1, upper * 0.7)

        # Context-dependent bacteria have inherently high variance
        adjusted_std = base_std * (1.0 + rng.uniform(0.0, 0.3, size=n))

        values = np.zeros(n)
        for i in range(n):
            values[i] = sample_lognormal_bounded(
                rng, adjusted_mean[i], adjusted_std[i],
                lower, upper, size=1,
            )[0]

        result[bacterium] = values

    return result
