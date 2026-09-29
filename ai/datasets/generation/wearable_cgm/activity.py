"""
activity.py — Physical activity feature generator.

Generates Average_Daily_Steps, Active_Minutes, Sedentary_Time_Minutes, and
Calories_Burned, conditioned on patient clinical context (BMI, Age, Weight, Gender).
"""

import numpy as np
from numpy.random import Generator
from typing import Dict

from . import config


def generate_activity_features(
    context: Dict[str, np.ndarray],
    rng: Generator,
    config_obj: config.WearableDatasetConfig = config.WearableDatasetConfig(),
) -> Dict[str, np.ndarray]:
    """Generate physical activity metrics conditioned on clinical variables.

    Args:
        context: Dictionary containing patient clinical context arrays.
        rng: NumPy random generator.
        config_obj: Configuration object.

    Returns:
        Dictionary of generated activity feature arrays.
    """
    n = len(context["Patient_ID"])
    bmis = context["BMI"]
    ages = context["Age"]
    weights = context["Weight_kg"]
    genders = context["Gender"]

    # ── 1. Average Daily Steps ──
    # Base steps reduced by BMI > 22 and Age > 30
    bmi_excess = np.maximum(0.0, bmis - 22.0)
    age_excess = np.maximum(0.0, ages - 30.0)

    steps_mean = (
        config.STEPS_BASE_MEAN
        + config.STEPS_BMI_SLOPE * bmi_excess
        + config.STEPS_AGE_SLOPE * age_excess
    )
    steps_mean = np.maximum(1500.0, steps_mean)

    # Log-normal noise to create realistic right-skewed step distribution
    noise = rng.normal(0, config.STEPS_NOISE_STD * config_obj.noise_scale, size=n)
    steps = np.clip(
        steps_mean + noise,
        config.STEPS_MIN,
        config.STEPS_MAX,
    )
    steps_int = np.round(steps).astype(int)

    # ── 2. Active Minutes (MVPA) ──
    # Moderate-to-vigorous activity scales with daily steps and drops with obesity
    bmi_obese_excess = np.maximum(0.0, bmis - 25.0)
    active_mean = (
        config.ACTIVE_MINUTES_STEP_SLOPE * steps_int
        + config.ACTIVE_MINUTES_BMI_SLOPE * bmi_obese_excess
    )
    active_mean = np.maximum(2.0, active_mean)

    active_noise = rng.normal(
        0, config.ACTIVE_MINUTES_NOISE_STD * config_obj.noise_scale, size=n
    )
    active_minutes = np.clip(
        active_mean + active_noise,
        config.ACTIVE_MINUTES_MIN,
        config.ACTIVE_MINUTES_MAX,
    )
    active_minutes = np.round(active_minutes, 1)

    # ── 3. Sedentary Time (Minutes) ──
    # High sedentary time correlates with BMI and inversely with daily steps
    sedentary_mean = (
        config.SEDENTARY_BASE
        + config.SEDENTARY_BMI_SLOPE * bmi_obese_excess
        + config.SEDENTARY_STEPS_SLOPE * steps_int
    )
    sedentary_noise = rng.normal(
        0, config.SEDENTARY_NOISE_STD * config_obj.noise_scale, size=n
    )
    sedentary_minutes = np.clip(
        sedentary_mean + sedentary_noise,
        config.SEDENTARY_MIN,
        config.SEDENTARY_MAX,
    )
    sedentary_minutes = np.round(sedentary_minutes, 1)

    # ── 4. Calories Burned ──
    # BMR(Gender, Weight) + activity energy expenditure + noise
    is_male = (genders == "Male") | (genders == "1") | (genders == 1)
    base_bmr = np.where(
        is_male, config.CALORIES_BMR_MALE, config.CALORIES_BMR_FEMALE
    )
    weight_bmr = base_bmr + config.CALORIES_WEIGHT_SLOPE * (weights - 70.0)

    calories_mean = (
        weight_bmr
        + config.CALORIES_STEPS_SLOPE * steps_int
        + config.CALORIES_ACTIVE_MIN_SLOPE * active_minutes
    )
    calories_noise = rng.normal(
        0, config.CALORIES_NOISE_STD * config_obj.noise_scale, size=n
    )
    calories_burned = np.clip(
        calories_mean + calories_noise,
        config.CALORIES_MIN,
        config.CALORIES_MAX,
    )
    calories_burned = np.round(calories_burned, 1)

    return {
        "Average_Daily_Steps": steps_int,
        "Active_Minutes": active_minutes,
        "Sedentary_Time_Minutes": sedentary_minutes,
        "Calories_Burned": calories_burned,
    }
