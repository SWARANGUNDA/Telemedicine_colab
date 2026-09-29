"""
diversity.py — Shannon Diversity Index modeler.

Computes the Shannon Diversity Index for each patient based on their
generated bacterial abundance profile and metabolic risk score. The index
reflects community richness and evenness — higher beneficial bacteria
abundance and lower inflammatory bacteria increase diversity.

The Shannon index is modeled as a function of:
  - Base diversity (population mean)
  - Beneficial bacteria abundance (positive contribution)
  - Inflammatory bacteria abundance (negative contribution)
  - Metabolic risk score (general depression)
  - Age modulation
  - Gaussian noise for biological variability
"""

import logging

import numpy as np
import pandas as pd

from . import constants

logger = logging.getLogger("gut_microbiome_generator")


def generate_shannon_diversity(
    rng: np.random.Generator,
    bacteria_df: pd.DataFrame,
    risk_scores: np.ndarray,
    age_values: np.ndarray,
) -> np.ndarray:
    """Generate Shannon Diversity Index for all patients.

    Combines a base diversity value with contributions from the bacterial
    abundance profile. Higher beneficial bacteria and lower inflammatory
    bacteria increase the index. Risk score provides a general depressive
    effect on diversity.

    Args:
        rng: NumPy random Generator.
        bacteria_df: DataFrame of all 9 bacterial abundance columns.
        risk_scores: Patient-level metabolic risk in [0, 1].
        age_values: Patient ages.

    Returns:
        Array of Shannon Diversity Index values, shape (n_patients,).
    """
    n = len(risk_scores)

    # Start from base diversity
    diversity = np.full(n, constants.SHANNON_BASE_MEAN)

    # Beneficial bacteria contribution (positive)
    for bacterium in constants.BENEFICIAL_BACTERIA:
        if bacterium in bacteria_df.columns:
            base_mean = constants.HEALTHY_DISTRIBUTION[bacterium][0]
            deviation = (bacteria_df[bacterium].values - base_mean) / base_mean
            diversity += deviation * constants.SHANNON_BENEFICIAL_WEIGHT * base_mean

    # Inflammatory bacteria contribution (negative)
    for bacterium in constants.INFLAMMATORY_BACTERIA:
        if bacterium in bacteria_df.columns:
            base_mean = constants.HEALTHY_DISTRIBUTION[bacterium][0]
            deviation = (bacteria_df[bacterium].values - base_mean) / base_mean
            diversity += deviation * constants.SHANNON_INFLAMMATORY_WEIGHT * base_mean

    # Risk score depression
    diversity += risk_scores * constants.SHANNON_RISK_SLOPE

    # Age modulation: slight decrease in elderly
    age_shift = (
        (age_values - constants.AGE_REFERENCE) *
        constants.AGE_DIVERSITY_SLOPE
    )
    diversity += age_shift

    # Gaussian noise for biological variability
    noise = rng.normal(0.0, constants.SHANNON_BASE_STD, size=n)
    diversity += noise

    # Clip to biological bounds
    lower, upper = constants.SHANNON_DIVERSITY_BOUNDS
    diversity = np.clip(diversity, lower, upper)

    logger.info(
        "Shannon Diversity: mean=%.3f, std=%.3f, min=%.3f, max=%.3f",
        np.mean(diversity),
        np.std(diversity),
        np.min(diversity),
        np.max(diversity),
    )

    return diversity
