"""
noise.py — Biological noise injection with boundary preservation.

Injects configurable Gaussian noise into generated microbiome features
to simulate measurement variability and biological stochasticity.
Noise is applied post-generation and post-correlation, with clipping
to ensure all values remain within physiological bounds.
"""

import logging

import numpy as np
import pandas as pd

from . import constants
from .config import GutMicrobiomeConfig

logger = logging.getLogger("gut_microbiome_generator")

# Per-feature noise standard deviations (relative to feature scale)
NOISE_SPECS = {
    "Akkermansia":          0.25,
    "Faecalibacterium":     0.35,
    "Bifidobacterium":      0.25,
    "Escherichia_Shigella":  0.15,
    "Roseburia":            0.20,
    "Blautia":              0.25,
    "Prevotella":           0.40,
    "Collinsella":          0.12,
    "Alistipes":            0.18,
    "Shannon_Diversity_Index": 0.05,
}


def inject_noise(
    data: pd.DataFrame,
    rng: np.random.Generator,
    config: GutMicrobiomeConfig,
) -> pd.DataFrame:
    """Inject Gaussian noise into microbiome features.

    Adds zero-mean Gaussian noise to each feature independently. Noise
    amplitude is feature-specific and scaled by config.noise_scale.
    Values are clipped to physiological bounds after injection.

    Args:
        data: DataFrame containing microbiome feature columns.
        rng: NumPy random Generator.
        config: Generator configuration.

    Returns:
        DataFrame with noise-injected values.
    """
    if not config.enable_noise:
        logger.info("Noise injection disabled.")
        return data

    result = data.copy()
    n = len(data)
    scale = config.noise_scale

    for feature in constants.MICROBIOME_FEATURES:
        if feature not in result.columns:
            continue

        noise_std = NOISE_SPECS.get(feature, 0.2) * scale

        noise = rng.normal(0.0, noise_std, size=n)
        result[feature] = result[feature].values + noise

        # Clip to bounds
        if feature == "Shannon_Diversity_Index":
            lower, upper = constants.SHANNON_DIVERSITY_BOUNDS
        else:
            lower, upper = constants.ABUNDANCE_BOUNDS[feature]

        result[feature] = np.clip(result[feature].values, lower, upper)

    logger.info("Gaussian noise injected (scale=%.2f)", scale)

    return result
