"""
heart.py — Cardiovascular feature generator.

Generates Resting_Heart_Rate (RHR) conditioned on patient clinical context
(BMI, Systolic BP) and physical activity levels (Average Daily Steps).
"""

import numpy as np
from numpy.random import Generator
from typing import Dict

from . import config


def generate_heart_features(
    context: Dict[str, np.ndarray],
    activity_features: Dict[str, np.ndarray],
    rng: Generator,
    config_obj: config.WearableDatasetConfig = config.WearableDatasetConfig(),
) -> Dict[str, np.ndarray]:
    """Generate Resting_Heart_Rate (bpm) conditioned on clinical and activity state.

    Args:
        context: Patient clinical context dictionary.
        activity_features: Generated activity metrics dictionary.
        rng: NumPy random generator.
        config_obj: Configuration object.

    Returns:
        Dictionary containing Resting_Heart_Rate array.
    """
    n = len(context["Patient_ID"])
    bmis = context["BMI"]
    sbp = context["Systolic_BP"]
    steps = activity_features["Average_Daily_Steps"]

    bmi_excess = np.maximum(0.0, bmis - 22.5)
    sbp_excess = np.maximum(0.0, sbp - 110.0)

    # RHR increases with BMI/BP and decreases with activity volume (fitness)
    rhr_mean = (
        config.RHR_BASE_MEAN
        + config.RHR_BMI_SLOPE * bmi_excess
        + config.RHR_BP_SLOPE * sbp_excess
        + config.RHR_STEPS_SLOPE * steps
    )

    noise = rng.normal(0, config.RHR_NOISE_STD * config_obj.noise_scale, size=n)
    rhr = np.clip(
        rhr_mean + noise,
        config.RHR_MIN,
        config.RHR_MAX,
    )
    rhr = np.round(rhr, 1)

    return {
        "Resting_Heart_Rate": rhr,
    }
