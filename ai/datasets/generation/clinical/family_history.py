"""
family_history.py — Generate family history binary variables.

Generates:
    - Family_History_Diabetes (0/1)
    - Family_History_Obesity (0/1)
    - Family_History_Hypertension (0/1)
    - Family_History_NAFLD (0/1)

Family history probabilities are modulated by the patient's own
metabolic state to create realistic correlations (patients with
diabetes are more likely to have family history of diabetes, etc.).
"""

import numpy as np
from numpy.random import Generator
from typing import Dict

from . import config


def generate_family_history(
    n: int,
    bmis: np.ndarray,
    glycemic_states: np.ndarray,
    sbps: np.ndarray,
    rng: Generator,
) -> Dict[str, np.ndarray]:
    """Generate all family history binary indicators.

    Each family history variable has a base probability that increases
    for patients who themselves have the related condition.

    Args:
        n: Number of patients.
        bmis: Array of BMI values (for obesity family history).
        glycemic_states: Array of glycemic state strings.
        sbps: Array of systolic BP values (for hypertension family history).
        rng: NumPy random generator.

    Returns:
        Dictionary with keys: Family_History_Diabetes, Family_History_Obesity,
        Family_History_Hypertension, Family_History_NAFLD.
    """
    if len(bmis) != n or len(glycemic_states) != n or len(sbps) != n:
        raise ValueError("All input arrays must have length n")

    results = {}

    # Family History of Diabetes
    fh_params = config.FAMILY_HISTORY_PARAMS["Family_History_Diabetes"]
    probs = np.full(n, fh_params["base_rate"])
    is_glycemic = (glycemic_states == "diabetes") | (glycemic_states == "prediabetes")
    probs[is_glycemic] = fh_params["diabetic_boost"]
    results["Family_History_Diabetes"] = (rng.random(n) < probs).astype(int)

    # Family History of Obesity
    fh_params = config.FAMILY_HISTORY_PARAMS["Family_History_Obesity"]
    probs = np.full(n, fh_params["base_rate"])
    is_obese = bmis >= 30.0
    probs[is_obese] = fh_params["obese_boost"]
    results["Family_History_Obesity"] = (rng.random(n) < probs).astype(int)

    # Family History of Hypertension
    fh_params = config.FAMILY_HISTORY_PARAMS["Family_History_Hypertension"]
    probs = np.full(n, fh_params["base_rate"])
    is_hypertensive = sbps >= 130
    probs[is_hypertensive] = fh_params["hypertensive_boost"]
    results["Family_History_Hypertension"] = (rng.random(n) < probs).astype(int)

    # Family History of NAFLD
    fh_params = config.FAMILY_HISTORY_PARAMS["Family_History_NAFLD"]
    probs = np.full(n, fh_params["base_rate"])
    # NAFLD risk: obese OR diabetic
    is_nafld_risk = is_obese | (glycemic_states == "diabetes")
    probs[is_nafld_risk] = fh_params["nafld_risk_boost"]
    results["Family_History_NAFLD"] = (rng.random(n) < probs).astype(int)

    return results
