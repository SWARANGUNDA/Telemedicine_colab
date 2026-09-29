"""
vitals.py — Generate vital sign measurements.

Generates:
    - Systolic_BP (integer, mmHg, range 90–190)
    - Diastolic_BP (integer, mmHg, range 60–120)

Blood pressure is correlated with age and BMI:
    - Older age → higher BP
    - Higher BMI → higher BP
    - Diabetic patients get additional co-occurrence boost

SBP is always greater than DBP (at least 10 mmHg gap).
"""

import numpy as np
from numpy.random import Generator
from typing import Dict

from . import config


def generate_systolic_bp(
    n: int,
    ages: np.ndarray,
    bmis: np.ndarray,
    sbp_adjustments: np.ndarray,
    rng: Generator,
) -> np.ndarray:
    """Generate systolic blood pressure values.

    SBP = base + age_effect + bmi_effect + comorbidity_boost + noise

    Args:
        n: Number of patients.
        ages: Array of patient ages.
        bmis: Array of BMI values.
        sbp_adjustments: Array of comorbidity-based SBP boosts.
        rng: NumPy random generator.

    Returns:
        Array of SBP values (integer, mmHg).
    """
    params = config.SBP_PARAMS

    # Base SBP with individual variation
    base = rng.normal(params["base_mean"], params["base_std"], size=n)

    # Age effect: +0.30 mmHg per year above reference age
    age_effect = params["age_slope"] * (ages.astype(float) - params["age_ref"])

    # BMI effect: +1.5 mmHg per BMI unit above reference
    bmi_effect = params["bmi_slope"] * np.maximum(
        0, bmis - params["bmi_ref"]
    )

    sbp = base + age_effect + bmi_effect + sbp_adjustments

    # Clip to valid range
    sbp = np.clip(sbp, config.FEATURE_RANGES["Systolic_BP"][0],
                  config.FEATURE_RANGES["Systolic_BP"][1])

    return np.round(sbp).astype(int)


def generate_diastolic_bp(
    n: int,
    sbps: np.ndarray,
    rng: Generator,
) -> np.ndarray:
    """Generate diastolic blood pressure values correlated with SBP.

    DBP is derived from SBP to maintain a realistic relationship:
        DBP ≈ SBP × ratio + offset + noise
    With constraint: SBP - DBP ≥ min_gap

    Args:
        n: Number of patients.
        sbps: Array of systolic BP values.
        rng: NumPy random generator.

    Returns:
        Array of DBP values (integer, mmHg).
    """
    params = config.DBP_PARAMS

    # DBP correlated with SBP
    noise = rng.normal(0, params["noise_std"], size=n)
    dbp = sbps.astype(float) * params["sbp_ratio"] + params["offset"] + noise

    # Ensure minimum gap between SBP and DBP
    max_dbp = sbps - params["min_gap"]
    dbp = np.minimum(dbp, max_dbp.astype(float))

    # Clip to valid range
    dbp = np.clip(dbp, config.FEATURE_RANGES["Diastolic_BP"][0],
                  config.FEATURE_RANGES["Diastolic_BP"][1])

    return np.round(dbp).astype(int)


def generate_vitals(
    ages: np.ndarray,
    bmis: np.ndarray,
    sbp_adjustments: np.ndarray,
    rng: Generator,
) -> Dict[str, np.ndarray]:
    """Generate all vital sign features for n patients.

    Args:
        ages: Array of patient ages.
        bmis: Array of BMI values.
        sbp_adjustments: Array of comorbidity SBP boosts from comorbidity module.
        rng: NumPy random generator.

    Returns:
        Dictionary with keys: Systolic_BP, Diastolic_BP.
    """
    n = len(ages)

    sbps = generate_systolic_bp(n, ages, bmis, sbp_adjustments, rng)
    dbps = generate_diastolic_bp(n, sbps, rng)

    return {
        "Systolic_BP": sbps,
        "Diastolic_BP": dbps,
    }
