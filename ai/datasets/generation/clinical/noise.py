"""
noise.py — Inject clinically realistic measurement noise.

Adds small Gaussian perturbations to numeric features to simulate
real-world measurement variability (lab error, scale variation, etc.).

Noise magnitudes from specification Section 11:
    Height: ±0.5 cm
    Weight: ±1 kg
    BP: ±3 mmHg
    HbA1c: ±0.2%
    FPG: ±5 mg/dL
    LDL: ±5 mg/dL
    HDL: ±3 mg/dL
    TG: ±8 mg/dL
    ALT/AST: ±3 U/L

BMI is recomputed from noisy Height and Weight.
All values are clipped to valid ranges after noise injection.
"""

import numpy as np
from numpy.random import Generator
from typing import Dict

from . import config


def _add_noise_to_feature(
    values: np.ndarray,
    noise_std: float,
    max_noise: float,
    value_range: tuple,
    rng: Generator,
    is_integer: bool = False,
) -> np.ndarray:
    """Add Gaussian noise to a feature array, clipped to valid range.

    Args:
        values: Original feature values.
        noise_std: Standard deviation of the Gaussian noise.
        max_noise: Maximum absolute noise (for clipping).
        value_range: (min, max) valid range for the feature.
        rng: NumPy random generator.
        is_integer: If True, round result to integer.

    Returns:
        Noisy feature values, clipped to valid range.
    """
    noise = rng.normal(0, noise_std, size=len(values))
    noise = np.clip(noise, -max_noise, max_noise)

    noisy_values = values.astype(float) + noise
    noisy_values = np.clip(noisy_values, value_range[0], value_range[1])

    if is_integer:
        return np.round(noisy_values).astype(int)
    else:
        return np.round(noisy_values, 1)


def inject_noise(
    data: Dict[str, np.ndarray],
    rng: Generator,
) -> Dict[str, np.ndarray]:
    """Inject measurement noise into all applicable features.

    Noise is added to Height, Weight, BP, and all lab values.
    BMI is then recomputed from noisy Height and Weight.
    All values are clipped to specification ranges.

    Args:
        data: Dictionary of all patient features (modified in-place).
        rng: NumPy random generator.

    Returns:
        The same dictionary with noise applied.
    """
    # Define which features get integer rounding
    integer_features = {
        "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose",
        "LDL_Cholesterol", "HDL_Cholesterol", "Triglycerides",
        "ALT", "AST",
    }

    # Apply noise to each configured feature
    for feature_name, noise_params in config.NOISE_PARAMS.items():
        if feature_name not in data:
            continue

        is_int = feature_name in integer_features
        feature_range = config.FEATURE_RANGES[feature_name]

        data[feature_name] = _add_noise_to_feature(
            data[feature_name],
            noise_params["std"],
            noise_params["max_noise"],
            feature_range,
            rng,
            is_integer=is_int,
        )

    # Recompute BMI from noisy Height and Weight
    heights_m = data["Height_cm"].astype(float) / 100.0
    data["BMI"] = np.round(
        data["Weight_kg"].astype(float) / (heights_m ** 2), 1,
    )
    data["BMI"] = np.clip(
        data["BMI"],
        config.FEATURE_RANGES["BMI"][0],
        config.FEATURE_RANGES["BMI"][1],
    )

    # Ensure SBP > DBP after noise (maintain at least min_gap)
    min_gap = config.DBP_PARAMS["min_gap"]
    gap_violation = data["Systolic_BP"] - data["Diastolic_BP"] < min_gap
    if gap_violation.any():
        data["Diastolic_BP"] = np.where(
            gap_violation,
            data["Systolic_BP"] - min_gap,
            data["Diastolic_BP"],
        )
        # Re-clip DBP
        data["Diastolic_BP"] = np.clip(
            data["Diastolic_BP"],
            config.FEATURE_RANGES["Diastolic_BP"][0],
            config.FEATURE_RANGES["Diastolic_BP"][1],
        )

    return data
