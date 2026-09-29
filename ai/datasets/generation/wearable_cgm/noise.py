"""
noise.py — Measurement noise, missing value, and outlier injection module.

Applies Gaussian sensor noise, simulates Missing-at-Random (MAR) data gaps,
and injects realistic extreme outliers into generated wearable metrics.
"""

import numpy as np
from numpy.random import Generator
from typing import Dict, Any

from . import config, constants


def inject_gaussian_noise(
    wearables: Dict[str, np.ndarray],
    rng: Generator,
    config_obj: config.WearableDatasetConfig = config.WearableDatasetConfig(),
) -> Dict[str, np.ndarray]:
    """Inject small Gaussian measurement noise mimicking wearable sensor noise.

    Args:
        wearables: Dictionary of generated wearable feature arrays.
        rng: NumPy random generator.
        config_obj: Configuration object.

    Returns:
        Dictionary of noisy feature arrays.
    """
    if not config_obj.enable_noise:
        return wearables

    noisy_data = {}

    for feature, array in wearables.items():
        if feature in config.NOISE_SPEC:
            spec = config.NOISE_SPEC[feature]
            std = spec["std"] * config_obj.noise_scale
            max_noise = spec["max"] * config_obj.noise_scale

            # Sample Gaussian noise and clip
            noise = rng.normal(0, std, size=len(array))
            noise = np.clip(noise, -max_noise, max_noise)

            noisy_arr = array + noise

            # Respect physiological bounds
            if feature in constants.FEATURE_BOUNDS:
                min_b, max_b = constants.FEATURE_BOUNDS[feature]
                noisy_arr = np.clip(noisy_arr, min_b, max_b)

            if feature == "Average_Daily_Steps":
                noisy_arr = np.round(noisy_arr).astype(int)
            else:
                noisy_arr = np.round(noisy_arr, 1)

            noisy_data[feature] = noisy_arr
        else:
            noisy_data[feature] = array

    return noisy_data


def inject_outliers(
    wearables: Dict[str, np.ndarray],
    rng: Generator,
    config_obj: config.WearableDatasetConfig = config.WearableDatasetConfig(),
) -> Dict[str, np.ndarray]:
    """Inject controlled plausible extreme outliers (~1-2% of records).

    Args:
        wearables: Dictionary of wearable feature arrays.
        rng: NumPy random generator.
        config_obj: Configuration object.

    Returns:
        Dictionary of feature arrays with injected outliers.
    """
    if not config_obj.enable_outliers:
        return wearables

    n = len(wearables["Average_Daily_Steps"])
    n_outliers = int(n * config_obj.outlier_fraction)

    if n_outliers == 0:
        return wearables

    # 1. Athlete Outliers: Very high steps, low RHR
    athlete_idx = rng.choice(n, size=n_outliers // 2, replace=False)
    wearables["Average_Daily_Steps"][athlete_idx] = rng.integers(18000, 24500, size=len(athlete_idx))
    wearables["Resting_Heart_Rate"][athlete_idx] = np.round(rng.uniform(42.0, 50.0, size=len(athlete_idx)), 1)

    # 2. Extreme Hyperglycemia Outliers: High average glucose, low TIR
    glycemic_idx = rng.choice(n, size=n_outliers // 2, replace=False)
    wearables["Average_Glucose"][glycemic_idx] = np.round(rng.uniform(210.0, 248.0, size=len(glycemic_idx)), 1)
    wearables["Time_In_Range"][glycemic_idx] = np.round(rng.uniform(5.0, 25.0, size=len(glycemic_idx)), 1)
    wearables["Time_Above_Range"][glycemic_idx] = np.round(100.0 - wearables["Time_In_Range"][glycemic_idx] - 2.0, 1)

    # Clip all features strictly to bounds
    for feat in constants.FEATURE_BOUNDS:
        if feat in wearables:
            min_b, max_b = constants.FEATURE_BOUNDS[feat]
            wearables[feat] = np.clip(wearables[feat], min_b, max_b)

    return wearables


def inject_missingness(
    wearables: Dict[str, np.ndarray],
    rng: Generator,
    config_obj: config.WearableDatasetConfig = config.WearableDatasetConfig(),
) -> Dict[str, np.ndarray]:
    """Inject Missing-at-Random (MAR) gaps into optional wearable metrics if enabled.

    Args:
        wearables: Dictionary of feature arrays.
        rng: NumPy random generator.
        config_obj: Configuration object.

    Returns:
        Dictionary of feature arrays with NaNs injected where applicable.
    """
    if not config_obj.enable_missingness:
        return wearables

    n = len(wearables["Average_Daily_Steps"])
    rate = config_obj.missing_rate_default

    for feature in ["Sleep_Duration", "Calories_Burned", "Glucose_Variability"]:
        if feature in wearables:
            mask = rng.random(n) < rate
            arr = wearables[feature].astype(float)
            arr[mask] = np.nan
            wearables[feature] = arr

    return wearables
