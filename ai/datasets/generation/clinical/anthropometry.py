"""
anthropometry.py — Generate anthropometric measurements.

Generates:
    - Height_cm (float, gender-specific distribution)
    - Weight_kg (float, derived from BMI and height)
    - BMI (float, category-based distribution)
    - Waist_Circumference_cm (float, correlated with BMI and gender)

BMI is generated first (from assigned category), then height is generated
from gender-specific distributions, and weight is computed as:
    Weight = BMI × (Height / 100)²

This ensures BMI consistency by construction.
"""

import numpy as np
from numpy.random import Generator
from typing import Dict

from . import config


def _sample_truncated_normal(
    rng: Generator,
    mean: float,
    std: float,
    low: float,
    high: float,
    size: int,
) -> np.ndarray:
    """Sample from a truncated normal distribution using rejection.

    Args:
        rng: NumPy random generator.
        mean: Mean of the normal distribution.
        std: Standard deviation.
        low: Lower bound (inclusive).
        high: Upper bound (inclusive).
        size: Number of samples.

    Returns:
        Array of samples within [low, high].
    """
    samples = np.empty(size, dtype=float)
    remaining = size
    idx = 0

    while remaining > 0:
        # Oversample to reduce iterations
        batch = rng.normal(mean, std, size=remaining * 2)
        valid = batch[(batch >= low) & (batch <= high)]
        take = min(len(valid), remaining)
        samples[idx:idx + take] = valid[:take]
        idx += take
        remaining -= take

    return samples


def generate_bmi_values(
    n: int,
    bmi_categories: np.ndarray,
    is_borderline: np.ndarray,
    is_outlier: np.ndarray,
    rng: Generator,
) -> np.ndarray:
    """Generate BMI values within assigned categories.

    Normal patients get BMI from category-specific truncated normal.
    Borderline patients get BMI near the boundaries of THEIR assigned
    category (e.g., overweight borderline → 28.5–29.9, obese borderline
    → 30.0–31.5), preserving the intended obesity prevalence.
    Outlier patients get extreme BMI (40–45).

    Args:
        n: Number of patients.
        bmi_categories: Array of BMI category strings.
        is_borderline: Boolean array for borderline patients.
        is_outlier: Boolean array for outlier patients.
        rng: NumPy random generator.

    Returns:
        Array of BMI values (float).
    """
    bmis = np.empty(n, dtype=float)

    # Standard patients: sample from category distributions
    for cat_name, params in config.BMI_CATEGORY_PARAMS.items():
        mask = (bmi_categories == cat_name) & ~is_borderline & ~is_outlier
        count = mask.sum()
        if count > 0:
            bmis[mask] = _sample_truncated_normal(
                rng,
                params["mean"],
                params["std"],
                params["min"],
                params["max"],
                count,
            )

    # Borderline patients: values near their category boundary
    # Each category's borderline is at the upper edge of their range
    borderline_ranges = {
        "underweight": (17.5, 18.49),    # near normal boundary
        "normal":      (24.0, 24.99),    # near overweight boundary
        "overweight":  (28.5, 29.99),    # near obesity boundary
        "obese":       (30.0, 31.5),     # just above obesity threshold
    }
    for cat_name, (bmin, bmax) in borderline_ranges.items():
        mask = (bmi_categories == cat_name) & is_borderline
        count = mask.sum()
        if count > 0:
            bmean = (bmin + bmax) / 2
            bstd = (bmax - bmin) / 4  # ~95% within range
            bmis[mask] = _sample_truncated_normal(
                rng, bmean, bstd, bmin, bmax, count,
            )

    # Outlier patients: extreme obesity
    outlier_mask = is_outlier
    outlier_count = outlier_mask.sum()
    if outlier_count > 0:
        op = config.BMI_OUTLIER_PARAMS
        bmis[outlier_mask] = _sample_truncated_normal(
            rng, op["mean"], op["std"], op["min"], op["max"], outlier_count,
        )

    return np.round(bmis, 1)


def generate_heights(
    n: int,
    genders: np.ndarray,
    rng: Generator,
) -> np.ndarray:
    """Generate patient heights based on gender-specific distributions.

    Args:
        n: Number of patients.
        genders: Array of gender strings ("Male" or "Female").
        rng: NumPy random generator.

    Returns:
        Array of heights in cm (float, rounded to 1 decimal).
    """
    heights = np.empty(n, dtype=float)

    for gender, params in config.HEIGHT_PARAMS.items():
        mask = genders == gender
        count = mask.sum()
        if count > 0:
            heights[mask] = _sample_truncated_normal(
                rng,
                params["mean"],
                params["std"],
                params["min"],
                params["max"],
                count,
            )

    return np.round(heights, 1)


def compute_weights(
    bmis: np.ndarray,
    heights: np.ndarray,
) -> np.ndarray:
    """Compute weight from BMI and height: Weight = BMI × (Height/100)².

    Values are clipped to the specification range [40, 150] kg.

    Args:
        bmis: Array of BMI values.
        heights: Array of heights in cm.

    Returns:
        Array of weights in kg (float, rounded to 1 decimal).
    """
    heights_m = heights / 100.0
    weights = bmis * (heights_m ** 2)
    weights = np.clip(weights, config.WEIGHT_RANGE[0], config.WEIGHT_RANGE[1])
    return np.round(weights, 1)


def generate_waist_circumference(
    n: int,
    bmis: np.ndarray,
    genders: np.ndarray,
    rng: Generator,
) -> np.ndarray:
    """Generate waist circumference correlated with BMI and gender.

    Uses a linear model: waist = slope × BMI + intercept + noise
    with gender-specific parameters.

    Args:
        n: Number of patients.
        bmis: Array of BMI values.
        genders: Array of gender strings.
        rng: NumPy random generator.

    Returns:
        Array of waist circumference values in cm (float, rounded to 1 decimal).
    """
    waists = np.empty(n, dtype=float)

    for gender, params in config.WAIST_PARAMS.items():
        mask = genders == gender
        count = mask.sum()
        if count > 0:
            noise = rng.normal(0, params["noise_std"], size=count)
            waists[mask] = (
                params["slope"] * bmis[mask]
                + params["intercept"]
                + noise
            )
            waists[mask] = np.clip(
                waists[mask], params["min"], params["max"],
            )

    return np.round(waists, 1)


def generate_anthropometry(
    genders: np.ndarray,
    bmi_categories: np.ndarray,
    is_borderline: np.ndarray,
    is_outlier: np.ndarray,
    rng: Generator,
) -> Dict[str, np.ndarray]:
    """Generate all anthropometric features for n patients.

    Generation order: BMI → Height → Weight (computed) → Waist
    This ensures BMI consistency by construction.

    Args:
        genders: Array of gender strings.
        bmi_categories: Array of BMI category strings.
        is_borderline: Boolean array for borderline patients.
        is_outlier: Boolean array for outlier patients.
        rng: NumPy random generator.

    Returns:
        Dictionary with keys: Height_cm, Weight_kg, BMI,
        Waist_Circumference_cm.
    """
    n = len(genders)

    bmis = generate_bmi_values(n, bmi_categories, is_borderline, is_outlier, rng)
    heights = generate_heights(n, genders, rng)
    weights = compute_weights(bmis, heights)

    # Recompute BMI from actual height/weight to ensure consistency
    heights_m = heights / 100.0
    bmis = np.round(weights / (heights_m ** 2), 1)
    bmis = np.clip(bmis, config.FEATURE_RANGES["BMI"][0],
                   config.FEATURE_RANGES["BMI"][1])

    waists = generate_waist_circumference(n, bmis, genders, rng)

    return {
        "Height_cm": heights,
        "Weight_kg": weights,
        "BMI": bmis,
        "Waist_Circumference_cm": waists,
    }
