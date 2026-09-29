"""
missingness.py — Simulate realistic missing data patterns.

Applies controlled missing values (NaN) to optional features according
to the specification's missingness percentages and conditional logic.

Mandatory features (0% missing): Patient_ID, Age, Gender, Height, Weight,
BMI, SBP, DBP, FPG, HbA1c, and all disease labels.

Optional features with missingness:
    Waist_Circumference_cm: ~3%
    LDL_Cholesterol: ~2%
    HDL_Cholesterol: ~2%
    Triglycerides: ~2%
    ALT: ~5%
    AST: ~5%
    Family_History_Diabetes: ~5%
    Family_History_Obesity: ~5%
    Family_History_Hypertension: ~5%
    Family_History_NAFLD: ~8%

Missingness is MAR (Missing At Random): younger/healthier patients are
more likely to have missing labs, per specification Section 13.

Panel logic: LDL/HDL/TG share a single missing mask (lipid panel ordered
together). ALT/AST share a single missing mask (liver panel together).
"""

import numpy as np
from numpy.random import Generator
from typing import Dict

from . import config


def _compute_conditional_missing_prob(
    base_rate: float,
    ages: np.ndarray,
    bmis: np.ndarray,
    feature_type: str,
) -> np.ndarray:
    """Compute per-patient missing probability with conditional logic.

    Younger, healthier patients are less likely to have extensive labs,
    so missingness is higher for them (MAR pattern per specification).

    Args:
        base_rate: Base missing probability from specification.
        ages: Array of patient ages.
        bmis: Array of BMI values.
        feature_type: Type of feature ("lab", "waist", or "family_history").

    Returns:
        Array of per-patient missing probabilities.
    """
    n = len(ages)
    probs = np.full(n, base_rate)

    if feature_type == "lab":
        # Younger + healthier patients more likely to have missing labs
        young_healthy = (ages < 30) & (bmis < 25)
        probs[young_healthy] = min(base_rate * 1.8, 0.12)

        # Obese/diabetic patients less likely to have missing labs
        # (they get more thorough workups)
        high_risk = bmis >= 30
        probs[high_risk] = base_rate * 0.5

    elif feature_type == "waist":
        # Waist less likely measured in younger healthy patients
        young_healthy = (ages < 30) & (bmis < 25)
        probs[young_healthy] = min(base_rate * 1.5, 0.08)

    # family_history uses base_rate uniformly (random per spec)

    return probs


def apply_missingness(
    data: Dict[str, np.ndarray],
    ages: np.ndarray,
    bmis: np.ndarray,
    rng: Generator,
) -> Dict[str, np.ndarray]:
    """Apply missing values to optional features.

    Lab panels are handled as groups: lipid panel (LDL, HDL, TG) shares
    one missing mask, and liver panel (ALT, AST) shares another.
    This is clinically realistic since they are ordered as single tests.

    Args:
        data: Dictionary of all patient features (modified in-place).
        ages: Array of patient ages.
        bmis: Array of BMI values.
        rng: NumPy random generator.

    Returns:
        The same dictionary with missing values applied.
    """
    n = len(ages)

    # ── Step 1: Generate panel-level missing masks ──

    # Lipid panel (LDL, HDL, TG) — ordered together, missing at ~2%
    lipid_probs = _compute_conditional_missing_prob(
        config.MISSING_RATES.get("LDL_Cholesterol", 0.02),
        ages, bmis, "lab",
    )
    lipid_missing = rng.random(n) < lipid_probs

    # Liver panel (ALT, AST) — ordered together, missing at ~5%
    liver_probs = _compute_conditional_missing_prob(
        config.MISSING_RATES.get("ALT", 0.05),
        ages, bmis, "lab",
    )
    liver_missing = rng.random(n) < liver_probs

    # ── Step 2: Apply panel masks ──

    lipid_features = ["LDL_Cholesterol", "HDL_Cholesterol", "Triglycerides"]
    for feat in lipid_features:
        if feat in data:
            data[feat] = data[feat].astype(float)
            data[feat][lipid_missing] = np.nan

    liver_features = ["ALT", "AST"]
    for feat in liver_features:
        if feat in data:
            data[feat] = data[feat].astype(float)
            data[feat][liver_missing] = np.nan

    # ── Step 3: Apply individual missing masks for non-panel features ──

    panel_features = set(lipid_features + liver_features)

    for feature_name, base_rate in config.MISSING_RATES.items():
        if feature_name not in data or feature_name in panel_features:
            continue

        # Determine feature type
        if feature_name == "Waist_Circumference_cm":
            feature_type = "waist"
        elif feature_name.startswith("Family_History"):
            feature_type = "family_history"
        else:
            feature_type = "other"

        # Compute per-patient missing probabilities
        missing_probs = _compute_conditional_missing_prob(
            base_rate, ages, bmis, feature_type,
        )

        # Generate and apply missing mask
        missing_mask = rng.random(n) < missing_probs

        data[feature_name] = data[feature_name].astype(float)
        data[feature_name][missing_mask] = np.nan

    return data
