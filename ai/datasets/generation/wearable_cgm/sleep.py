"""
sleep.py — Sleep feature generator.

Generates Sleep_Duration (hours) conditioned on patient age, BMI, and clinical state.
"""

import numpy as np
from numpy.random import Generator
from typing import Dict

from . import config


def generate_sleep_features(
    context: Dict[str, np.ndarray],
    rng: Generator,
    config_obj: config.WearableDatasetConfig = config.WearableDatasetConfig(),
) -> Dict[str, np.ndarray]:
    """Generate Sleep_Duration (hours) conditioned on clinical features.

    Args:
        context: Patient clinical context dictionary.
        rng: NumPy random generator.
        config_obj: Configuration object.

    Returns:
        Dictionary containing Sleep_Duration array.
    """
    n = len(context["Patient_ID"])
    ages = context["Age"]
    bmis = context["BMI"]

    age_excess = np.maximum(0.0, ages - 40.0)
    bmi_excess = np.maximum(0.0, bmis - 25.0)

    sleep_mean = (
        config.SLEEP_BASE_MEAN
        + config.SLEEP_AGE_SLOPE * age_excess
        + config.SLEEP_BMI_SLOPE * bmi_excess
    )

    noise = rng.normal(0, config.SLEEP_NOISE_STD * config_obj.noise_scale, size=n)
    sleep_duration = np.clip(
        sleep_mean + noise,
        config.SLEEP_MIN,
        config.SLEEP_MAX,
    )
    sleep_duration = np.round(sleep_duration, 1)

    return {
        "Sleep_Duration": sleep_duration,
    }
