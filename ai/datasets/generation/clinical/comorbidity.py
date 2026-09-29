"""
comorbidity.py — Metabolic profile assignment and co-occurrence adjustments.

This module assigns internal metabolic profiles to each patient BEFORE feature
generation. These profiles guide feature distributions to achieve realistic
disease co-occurrence patterns and target prevalences.

The profiles are NEVER stored in the output — disease labels are always
derived deterministically from generated features.

Co-occurrence targets (from specification Section 8):
    - 70–80% of T2D patients are also obese
    - ~85–90% of T2D patients also have MetS
    - >80% of NAFLD cases coincide with obesity or elevated FPG
    - Large fraction of obese patients have MetS
"""

import numpy as np
from numpy.random import Generator
from typing import Dict, Tuple

from . import config


def _get_age_modifier(age: int) -> float:
    """Return the age-based glycemic probability modifier.

    Older patients have higher probability of diabetes/prediabetes.

    Args:
        age: Patient age in years.

    Returns:
        Multiplicative modifier for glycemic state probabilities.
    """
    if age >= 61:
        return config.AGE_GLYCEMIC_MODIFIERS["61-85"]
    elif age >= 46:
        return config.AGE_GLYCEMIC_MODIFIERS["46-60"]
    elif age >= 31:
        return config.AGE_GLYCEMIC_MODIFIERS["31-45"]
    else:
        return config.AGE_GLYCEMIC_MODIFIERS["18-30"]


def assign_bmi_categories(n: int, rng: Generator) -> np.ndarray:
    """Assign each patient to a BMI category based on target distribution.

    BMI categories: underweight (5%), normal (31%), overweight (40%), obese (24%)

    Args:
        n: Number of patients.
        rng: NumPy random generator.

    Returns:
        Array of BMI category strings.
    """
    if n <= 0:
        raise ValueError(f"Number of patients must be positive, got {n}")

    categories = rng.choice(
        config.BMI_CATEGORY_NAMES,
        size=n,
        p=config.BMI_CATEGORY_PROPORTIONS,
    )
    return categories


def assign_glycemic_states(
    n: int,
    bmi_categories: np.ndarray,
    ages: np.ndarray,
    rng: Generator,
) -> np.ndarray:
    """Assign each patient an internal glycemic state.

    The glycemic state (normal, prediabetes, diabetes) is determined by
    conditional probabilities based on BMI category, adjusted by age.
    These are calibrated to achieve ~16% T2D and ~18% prediabetes overall.

    Args:
        n: Number of patients.
        bmi_categories: Array of BMI category strings.
        ages: Array of patient ages.
        rng: NumPy random generator.

    Returns:
        Array of glycemic state strings: "normal", "prediabetes", "diabetes".
    """
    if len(bmi_categories) != n or len(ages) != n:
        raise ValueError("Array lengths must match n")

    states = np.empty(n, dtype=object)

    for i in range(n):
        bmi_cat = bmi_categories[i]
        age = ages[i]

        # Get base probabilities for this BMI category
        p_normal, p_pre, p_t2d = config.GLYCEMIC_PROBS_BY_BMI[bmi_cat]

        # Apply age modifier
        age_mod = _get_age_modifier(age)
        p_t2d_adj = p_t2d * age_mod
        p_pre_adj = p_pre * age_mod
        p_normal_adj = 1.0 - p_t2d_adj - p_pre_adj

        # Clamp and renormalize to valid probabilities
        p_normal_adj = max(p_normal_adj, 0.02)
        total = p_t2d_adj + p_pre_adj + p_normal_adj
        probs = [p_normal_adj / total, p_pre_adj / total, p_t2d_adj / total]

        # Sample glycemic state
        state_idx = rng.choice(3, p=probs)
        states[i] = ["normal", "prediabetes", "diabetes"][state_idx]

    return states


def assign_special_flags(
    n: int,
    rng: Generator,
) -> Tuple[np.ndarray, np.ndarray]:
    """Assign borderline and outlier flags to patients.

    ~15% of patients are borderline (values near diagnostic thresholds).
    ~2% of patients are outliers (extreme but plausible values).
    These flags are mutually exclusive.

    Args:
        n: Number of patients.
        rng: NumPy random generator.

    Returns:
        Tuple of (is_borderline, is_outlier) boolean arrays.
    """
    if n <= 0:
        raise ValueError(f"Number of patients must be positive, got {n}")

    random_vals = rng.random(n)

    is_outlier = random_vals < config.OUTLIER_FRACTION
    is_borderline = (
        (random_vals >= config.OUTLIER_FRACTION)
        & (random_vals < config.OUTLIER_FRACTION + config.BORDERLINE_FRACTION)
    )

    return is_borderline, is_outlier


def get_comorbidity_adjustments(
    bmi_categories: np.ndarray,
    glycemic_states: np.ndarray,
) -> Dict[str, np.ndarray]:
    """Compute per-patient feature adjustments for co-occurrence realism.

    Patients with multiple metabolic risk factors get boosted lab/vital
    values to ensure realistic disease clustering. These adjustments are
    added to base feature distributions by other modules.

    Args:
        bmi_categories: Array of BMI category strings.
        glycemic_states: Array of glycemic state strings.

    Returns:
        Dictionary of adjustment arrays (tg_boost, hdl_reduction,
        sbp_boost, alt_boost).
    """
    n = len(bmi_categories)
    if len(glycemic_states) != n:
        raise ValueError("Array lengths must match")

    tg_boost = np.zeros(n, dtype=float)
    hdl_reduction = np.zeros(n, dtype=float)
    sbp_boost = np.zeros(n, dtype=float)
    alt_boost = np.zeros(n, dtype=float)

    for i in range(n):
        is_obese = bmi_categories[i] == "obese"
        is_diabetic = glycemic_states[i] == "diabetes"

        if is_obese and is_diabetic:
            adj = config.COMORBIDITY_ADJUSTMENTS["obese_diabetic"]
        elif is_diabetic:
            adj = config.COMORBIDITY_ADJUSTMENTS["diabetic"]
        elif is_obese:
            adj = config.COMORBIDITY_ADJUSTMENTS["obese"]
        else:
            continue

        tg_boost[i] = adj["tg_boost"]
        hdl_reduction[i] = adj["hdl_reduction"]
        sbp_boost[i] = adj["sbp_boost"]
        alt_boost[i] = adj["alt_boost"]

    return {
        "tg_boost": tg_boost,
        "hdl_reduction": hdl_reduction,
        "sbp_boost": sbp_boost,
        "alt_boost": alt_boost,
    }
