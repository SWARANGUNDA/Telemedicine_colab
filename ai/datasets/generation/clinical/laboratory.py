"""
laboratory.py — Generate laboratory parameter values.

Generates:
    - Fasting_Blood_Glucose (integer, mg/dL, range 70–250)
    - HbA1c (float, %, range 4.5–12.0)
    - LDL_Cholesterol (integer, mg/dL, range 40–250)
    - HDL_Cholesterol (integer, mg/dL, range 20–90)
    - Triglycerides (integer, mg/dL, range 40–500)
    - ALT (integer, U/L, range 10–200)
    - AST (integer, U/L, range 10–150)

FPG and HbA1c are generated based on the patient's glycemic state
(normal/prediabetes/diabetes) to ensure consistency.

Lipids are correlated with BMI (higher BMI → higher TG, lower HDL).
Liver enzymes are correlated with BMI and metabolic state.

Borderline patients get values near diagnostic thresholds.
Outlier patients get extreme but plausible values.
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
    """Sample from a truncated normal distribution using rejection."""
    samples = np.empty(size, dtype=float)
    remaining = size
    idx = 0

    while remaining > 0:
        batch = rng.normal(mean, std, size=max(remaining * 2, 10))
        valid = batch[(batch >= low) & (batch <= high)]
        take = min(len(valid), remaining)
        samples[idx:idx + take] = valid[:take]
        idx += take
        remaining -= take

    return samples


def generate_fasting_glucose(
    n: int,
    glycemic_states: np.ndarray,
    is_borderline: np.ndarray,
    is_outlier: np.ndarray,
    rng: Generator,
) -> np.ndarray:
    """Generate fasting blood glucose values based on glycemic state.

    Normal: 70–99 mg/dL
    Prediabetes: 100–125 mg/dL
    Diabetes: 126–250 mg/dL

    Borderline patients get values near cutoffs.
    Outlier diabetic patients get very high values (200–250).

    Args:
        n: Number of patients.
        glycemic_states: Array of glycemic state strings.
        is_borderline: Boolean array for borderline patients.
        is_outlier: Boolean array for outlier patients.
        rng: NumPy random generator.

    Returns:
        Array of FPG values (integer, mg/dL).
    """
    fpg = np.empty(n, dtype=float)

    for state in ["normal", "prediabetes", "diabetes"]:
        params = config.GLYCEMIC_FEATURE_PARAMS[state]

        # Standard patients in this glycemic state
        mask = (glycemic_states == state) & ~is_borderline & ~is_outlier
        count = mask.sum()
        if count > 0:
            fpg[mask] = _sample_truncated_normal(
                rng, params["fpg_mean"], params["fpg_std"],
                params["fpg_min"], params["fpg_max"], count,
            )

    # Borderline patients: values near the upper edge of THEIR glycemic state
    # This preserves the glycemic assignment while creating challenging cases
    borderline_by_state = {
        "normal":      {"fpg_mean": 95.0,  "fpg_std": 2.0, "fpg_min": 90,  "fpg_max": 99},
        "prediabetes": {"fpg_mean": 122.0, "fpg_std": 2.0, "fpg_min": 118, "fpg_max": 125},
        "diabetes":    {"fpg_mean": 130.0, "fpg_std": 3.0, "fpg_min": 126, "fpg_max": 138},
    }
    for state, bp in borderline_by_state.items():
        mask = (glycemic_states == state) & is_borderline
        count = mask.sum()
        if count > 0:
            fpg[mask] = _sample_truncated_normal(
                rng, bp["fpg_mean"], bp["fpg_std"],
                bp["fpg_min"], bp["fpg_max"], count,
            )

    # Outlier patients: extreme diabetic values
    outlier_mask = is_outlier
    outlier_count = outlier_mask.sum()
    if outlier_count > 0:
        op = config.OUTLIER_DIABETES_PARAMS
        fpg[outlier_mask] = _sample_truncated_normal(
            rng, op["fpg_mean"], op["fpg_std"],
            op["fpg_min"], op["fpg_max"], outlier_count,
        )

    return np.round(fpg).astype(int)


def generate_hba1c(
    n: int,
    glycemic_states: np.ndarray,
    fpg_values: np.ndarray,
    is_borderline: np.ndarray,
    is_outlier: np.ndarray,
    rng: Generator,
) -> np.ndarray:
    """Generate HbA1c values correlated with glycemic state and FPG.

    HbA1c is generated within glycemic-state-appropriate ranges,
    then adjusted to correlate with FPG within each state.

    Args:
        n: Number of patients.
        glycemic_states: Array of glycemic state strings.
        fpg_values: Array of fasting glucose values (for correlation).
        is_borderline: Boolean array for borderline patients.
        is_outlier: Boolean array for outlier patients.
        rng: NumPy random generator.

    Returns:
        Array of HbA1c values (float, %).
    """
    hba1c = np.empty(n, dtype=float)

    for state in ["normal", "prediabetes", "diabetes"]:
        params = config.GLYCEMIC_FEATURE_PARAMS[state]

        mask = (glycemic_states == state) & ~is_borderline & ~is_outlier
        count = mask.sum()
        if count > 0:
            # Generate base HbA1c
            base = _sample_truncated_normal(
                rng, params["hba1c_mean"], params["hba1c_std"],
                params["hba1c_min"], params["hba1c_max"], count,
            )

            # Add correlation with FPG (within-state)
            fpg_subset = fpg_values[mask].astype(float)
            fpg_z = (fpg_subset - params["fpg_mean"]) / max(params["fpg_std"], 1.0)
            correlation_effect = 0.3 * fpg_z * params["hba1c_std"]
            hba1c_vals = base + correlation_effect

            # Clip to state range
            hba1c_vals = np.clip(
                hba1c_vals, params["hba1c_min"], params["hba1c_max"],
            )
            hba1c[mask] = hba1c_vals

    # Borderline patients: HbA1c at upper edge of THEIR glycemic state
    borderline_hba1c_by_state = {
        "normal":      {"mean": 5.45, "std": 0.08, "min": 5.3, "max": 5.6},
        "prediabetes": {"mean": 6.3,  "std": 0.08, "min": 6.1, "max": 6.4},
        "diabetes":    {"mean": 6.7,  "std": 0.15, "min": 6.5, "max": 7.0},
    }
    for state, bp in borderline_hba1c_by_state.items():
        mask = (glycemic_states == state) & is_borderline
        count = mask.sum()
        if count > 0:
            hba1c[mask] = _sample_truncated_normal(
                rng, bp["mean"], bp["std"],
                bp["min"], bp["max"], count,
            )

    # Outlier patients: very high HbA1c
    outlier_mask = is_outlier
    outlier_count = outlier_mask.sum()
    if outlier_count > 0:
        op = config.OUTLIER_DIABETES_PARAMS
        hba1c[outlier_mask] = _sample_truncated_normal(
            rng, op["hba1c_mean"], op["hba1c_std"],
            op["hba1c_min"], op["hba1c_max"], outlier_count,
        )

    return np.round(hba1c, 1)


def generate_ldl(
    n: int,
    bmis: np.ndarray,
    is_outlier: np.ndarray,
    rng: Generator,
) -> np.ndarray:
    """Generate LDL cholesterol values correlated with BMI.

    Args:
        n: Number of patients.
        bmis: Array of BMI values.
        is_outlier: Boolean array for outlier patients.
        rng: NumPy random generator.

    Returns:
        Array of LDL values (integer, mg/dL).
    """
    params = config.LDL_PARAMS
    ldl_range = config.FEATURE_RANGES["LDL_Cholesterol"]

    # Base LDL with BMI effect
    base = rng.normal(params["mean"], params["std"], size=n)
    bmi_effect = params["bmi_slope"] * np.maximum(0, bmis - params["bmi_ref"])
    ldl = base + bmi_effect

    # Outliers: very high LDL
    if is_outlier.any():
        op = config.OUTLIER_LIPID_PARAMS["ldl"]
        outlier_count = is_outlier.sum()
        ldl[is_outlier] = _sample_truncated_normal(
            rng, op["mean"], op["std"], op["min"], op["max"], outlier_count,
        )

    ldl = np.clip(ldl, ldl_range[0], ldl_range[1])
    return np.round(ldl).astype(int)


def generate_hdl(
    n: int,
    genders: np.ndarray,
    bmis: np.ndarray,
    tg_values: np.ndarray,
    hdl_adjustments: np.ndarray,
    rng: Generator,
) -> np.ndarray:
    """Generate HDL cholesterol values.

    HDL is gender-specific, inversely correlated with BMI and TG,
    and reduced for multi-morbid patients.

    Args:
        n: Number of patients.
        genders: Array of gender strings.
        bmis: Array of BMI values.
        tg_values: Array of triglyceride values (for inverse correlation).
        hdl_adjustments: Array of comorbidity HDL reductions.
        rng: NumPy random generator.

    Returns:
        Array of HDL values (integer, mg/dL).
    """
    hdl = np.empty(n, dtype=float)
    hdl_range = config.FEATURE_RANGES["HDL_Cholesterol"]

    for gender, params in config.HDL_PARAMS.items():
        mask = genders == gender
        count = mask.sum()
        if count > 0:
            base = rng.normal(params["mean"], params["std"], size=count)

            # BMI inverse effect
            bmi_effect = config.HDL_BMI_SLOPE * np.maximum(
                0, bmis[mask] - 25.0,
            )

            # TG inverse correlation: high TG pushes HDL lower
            tg_effect = -0.02 * np.maximum(0, tg_values[mask].astype(float) - 150.0)

            # Comorbidity reduction
            hdl[mask] = base + bmi_effect + tg_effect - hdl_adjustments[mask]

    hdl = np.clip(hdl, hdl_range[0], hdl_range[1])
    return np.round(hdl).astype(int)


def generate_triglycerides(
    n: int,
    bmis: np.ndarray,
    glycemic_states: np.ndarray,
    tg_adjustments: np.ndarray,
    is_outlier: np.ndarray,
    rng: Generator,
) -> np.ndarray:
    """Generate triglyceride values correlated with BMI and glycemic state.

    Args:
        n: Number of patients.
        bmis: Array of BMI values.
        glycemic_states: Array of glycemic state strings.
        tg_adjustments: Array of comorbidity TG boosts.
        is_outlier: Boolean array for outlier patients.
        rng: NumPy random generator.

    Returns:
        Array of triglyceride values (integer, mg/dL).
    """
    params = config.TRIGLYCERIDE_PARAMS
    tg_range = config.FEATURE_RANGES["Triglycerides"]

    # Base TG with BMI effect
    base = rng.normal(params["mean"], params["std"], size=n)
    bmi_effect = params["bmi_slope"] * np.maximum(0, bmis - params["bmi_ref"])

    # Diabetes boost
    diabetes_boost = np.where(
        glycemic_states == "diabetes", params["diabetes_boost"], 0.0,
    )

    tg = base + bmi_effect + diabetes_boost + tg_adjustments

    # Outliers: severe dyslipidemia
    if is_outlier.any():
        op = config.OUTLIER_LIPID_PARAMS["triglycerides"]
        outlier_count = is_outlier.sum()
        tg[is_outlier] = _sample_truncated_normal(
            rng, op["mean"], op["std"], op["min"], op["max"], outlier_count,
        )

    tg = np.clip(tg, tg_range[0], tg_range[1])
    return np.round(tg).astype(int)


def generate_alt(
    n: int,
    bmis: np.ndarray,
    glycemic_states: np.ndarray,
    alt_adjustments: np.ndarray,
    is_outlier: np.ndarray,
    rng: Generator,
) -> np.ndarray:
    """Generate ALT (liver enzyme) values correlated with BMI and metabolic state.

    ALT is elevated in patients with obesity, diabetes, and NAFLD risk.

    Args:
        n: Number of patients.
        bmis: Array of BMI values.
        glycemic_states: Array of glycemic state strings.
        alt_adjustments: Array of comorbidity ALT boosts.
        is_outlier: Boolean array for outlier patients.
        rng: NumPy random generator.

    Returns:
        Array of ALT values (integer, U/L).
    """
    params = config.ALT_PARAMS
    alt_range = config.FEATURE_RANGES["ALT"]

    # Base ALT
    base = rng.normal(params["mean"], params["std"], size=n)

    # BMI effect
    bmi_effect = params["bmi_slope"] * np.maximum(0, bmis - params["bmi_ref"])

    # Metabolic boost for obese+diabetic patients
    is_metabolic = (
        (bmis >= 30) & (glycemic_states == "diabetes")
    )
    metabolic_boost = np.where(is_metabolic, params["metabolic_boost"], 0.0)

    alt = base + bmi_effect + metabolic_boost + alt_adjustments

    # Outliers: significantly elevated liver enzymes
    if is_outlier.any():
        op = config.OUTLIER_LIVER_PARAMS
        outlier_count = is_outlier.sum()
        alt[is_outlier] = _sample_truncated_normal(
            rng, op["alt_mean"], op["alt_std"],
            op["alt_min"], op["alt_max"], outlier_count,
        )

    alt = np.clip(alt, alt_range[0], alt_range[1])
    return np.round(alt).astype(int)


def generate_ast(
    n: int,
    alt_values: np.ndarray,
    is_outlier: np.ndarray,
    rng: Generator,
) -> np.ndarray:
    """Generate AST (liver enzyme) values correlated with ALT.

    AST tracks ALT loosely (r ≈ 0.7) and is generally lower.

    Args:
        n: Number of patients.
        alt_values: Array of ALT values (for correlation).
        is_outlier: Boolean array for outlier patients.
        rng: NumPy random generator.

    Returns:
        Array of AST values (integer, U/L).
    """
    params = config.AST_PARAMS
    ast_range = config.FEATURE_RANGES["AST"]

    # AST correlated with ALT
    noise = rng.normal(0, params["std"], size=n)
    ast = (
        params["alt_correlation"] * alt_values.astype(float)
        + (1 - params["alt_correlation"]) * params["mean"]
        + noise
    )

    # Outliers: elevated AST
    if is_outlier.any():
        op = config.OUTLIER_LIVER_PARAMS
        outlier_count = is_outlier.sum()
        ast[is_outlier] = _sample_truncated_normal(
            rng, op["ast_mean"], op["ast_std"],
            op["ast_min"], op["ast_max"], outlier_count,
        )

    ast = np.clip(ast, ast_range[0], ast_range[1])
    return np.round(ast).astype(int)


def generate_laboratory(
    ages: np.ndarray,
    genders: np.ndarray,
    bmis: np.ndarray,
    glycemic_states: np.ndarray,
    is_borderline: np.ndarray,
    is_outlier: np.ndarray,
    adjustments: Dict[str, np.ndarray],
    rng: Generator,
) -> Dict[str, np.ndarray]:
    """Generate all laboratory parameter values.

    Args:
        ages: Array of patient ages.
        genders: Array of gender strings.
        bmis: Array of BMI values.
        glycemic_states: Array of glycemic state strings.
        is_borderline: Boolean array for borderline patients.
        is_outlier: Boolean array for outlier patients.
        adjustments: Dictionary of comorbidity adjustments
            (tg_boost, hdl_reduction, alt_boost).
        rng: NumPy random generator.

    Returns:
        Dictionary with keys: Fasting_Blood_Glucose, HbA1c,
        LDL_Cholesterol, HDL_Cholesterol, Triglycerides, ALT, AST.
    """
    n = len(ages)

    # Generate in dependency order
    fpg = generate_fasting_glucose(
        n, glycemic_states, is_borderline, is_outlier, rng,
    )
    hba1c = generate_hba1c(
        n, glycemic_states, fpg, is_borderline, is_outlier, rng,
    )

    # Lipids
    tg = generate_triglycerides(
        n, bmis, glycemic_states, adjustments["tg_boost"], is_outlier, rng,
    )
    ldl = generate_ldl(n, bmis, is_outlier, rng)
    hdl = generate_hdl(
        n, genders, bmis, tg, adjustments["hdl_reduction"], rng,
    )

    # Liver enzymes
    alt = generate_alt(
        n, bmis, glycemic_states, adjustments["alt_boost"], is_outlier, rng,
    )
    ast = generate_ast(n, alt, is_outlier, rng)

    return {
        "Fasting_Blood_Glucose": fpg,
        "HbA1c": hba1c,
        "LDL_Cholesterol": ldl,
        "HDL_Cholesterol": hdl,
        "Triglycerides": tg,
        "ALT": alt,
        "AST": ast,
    }
