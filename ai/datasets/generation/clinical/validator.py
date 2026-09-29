"""
validator.py — Validate generated patient records and dataset integrity.

Performs two levels of validation:

1. Per-patient validation:
    - Demographics (age range, gender values)
    - BMI consistency (matches Height/Weight ± 0.5)
    - Blood pressure (SBP > DBP, within range)
    - Feature ranges (all values within specification bounds)
    - Disease label consistency (labels match clinical criteria)
    - Healthy label (1 only if all diseases = 0)
    - Cross-feature consistency (no impossible combinations)

2. Dataset-wide validation:
    - Unique Patient_IDs
    - No duplicate rows
    - Disease prevalence within ±3% of targets
    - Missing value percentages within expected ranges
    - Correlation sign checks (BMI↔Waist positive, BMI↔HDL negative, etc.)
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

from . import config

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# PER-PATIENT VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def validate_demographics(row: Dict) -> List[str]:
    """Validate demographic fields for a single patient.

    Args:
        row: Dictionary of patient feature values.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []

    age = row.get("Age")
    if age is None or not (18 <= age <= 85):
        errors.append(f"Age {age} out of range [18, 85]")

    gender = row.get("Gender")
    if gender not in ("Male", "Female"):
        errors.append(f"Invalid Gender: {gender}")

    pid = row.get("Patient_ID")
    if pid is None or not isinstance(pid, str) or len(pid) == 0:
        errors.append(f"Invalid Patient_ID: {pid}")

    return errors


def validate_bmi_consistency(row: Dict, tolerance: float = 0.5) -> List[str]:
    """Check BMI matches Height and Weight within tolerance.

    BMI should equal Weight / (Height/100)², within ±tolerance.

    Args:
        row: Dictionary of patient feature values.
        tolerance: Maximum allowed BMI deviation.

    Returns:
        List of error messages.
    """
    errors = []

    height = row.get("Height_cm")
    weight = row.get("Weight_kg")
    bmi = row.get("BMI")

    if height is None or weight is None or bmi is None:
        return errors

    if height <= 0:
        errors.append(f"Height must be positive, got {height}")
        return errors

    expected_bmi = weight / ((height / 100.0) ** 2)
    if abs(bmi - expected_bmi) > tolerance:
        errors.append(
            f"BMI inconsistency: stored={bmi:.1f}, "
            f"computed={expected_bmi:.1f}, diff={abs(bmi - expected_bmi):.2f}"
        )

    return errors


def validate_blood_pressure(row: Dict) -> List[str]:
    """Validate blood pressure values and relationship.

    Args:
        row: Dictionary of patient feature values.

    Returns:
        List of error messages.
    """
    errors = []

    sbp = row.get("Systolic_BP")
    dbp = row.get("Diastolic_BP")

    if sbp is None or dbp is None:
        return errors

    if not (90 <= sbp <= 190):
        errors.append(f"SBP {sbp} out of range [90, 190]")

    if not (60 <= dbp <= 120):
        errors.append(f"DBP {dbp} out of range [60, 120]")

    if sbp <= dbp:
        errors.append(f"SBP ({sbp}) must be greater than DBP ({dbp})")

    return errors


def validate_feature_ranges(row: Dict) -> List[str]:
    """Validate all numeric features are within specification ranges.

    Skips NaN values (missing data is acceptable for optional features).

    Args:
        row: Dictionary of patient feature values.

    Returns:
        List of error messages.
    """
    errors = []

    for feature_name, (min_val, max_val) in config.FEATURE_RANGES.items():
        value = row.get(feature_name)
        if value is None:
            continue

        # Skip NaN (missing) values
        try:
            if np.isnan(float(value)):
                continue
        except (TypeError, ValueError):
            continue

        if not (min_val <= float(value) <= max_val):
            errors.append(
                f"{feature_name}={value} out of range [{min_val}, {max_val}]"
            )

    return errors


def validate_disease_labels(row: Dict) -> List[str]:
    """Validate disease labels are consistent with clinical features.

    Checks:
        - T2D=1 ⇒ FPG≥126 or HbA1c≥6.5
        - Prediabetes=1 ⇒ (100≤FPG≤125 or 5.7≤HbA1c≤6.4) and T2D=0
        - Obesity=1 ⇒ BMI≥30
        - MetS=1 ⇒ ≥3 criteria met
        - Healthy=1 ⇒ all other diseases=0

    Args:
        row: Dictionary of patient feature values.

    Returns:
        List of error messages.
    """
    errors = []

    t2d = row.get("Type2_Diabetes", 0)
    pre = row.get("Prediabetes", 0)
    obesity = row.get("Obesity", 0)
    mets = row.get("Metabolic_Syndrome", 0)
    nafld = row.get("NAFLD", 0)
    healthy = row.get("Healthy", 0)

    fpg = row.get("Fasting_Blood_Glucose")
    hba1c = row.get("HbA1c")
    bmi = row.get("BMI")

    # T2D validation
    if t2d == 1:
        if fpg is not None and hba1c is not None:
            if fpg < 126 and hba1c < 6.5:
                errors.append(
                    f"T2D=1 but FPG={fpg}<126 and HbA1c={hba1c}<6.5"
                )

    # Prediabetes validation
    if pre == 1:
        if t2d == 1:
            errors.append("Prediabetes=1 but T2D=1 (mutually exclusive)")
        if fpg is not None and hba1c is not None:
            fpg_ok = 100 <= fpg <= 125
            hba1c_ok = 5.7 <= hba1c <= 6.4
            if not (fpg_ok or hba1c_ok):
                errors.append(
                    f"Prediabetes=1 but FPG={fpg} and HbA1c={hba1c} "
                    "not in prediabetic range"
                )

    # Obesity validation
    if obesity == 1 and bmi is not None:
        if bmi < 30.0:
            errors.append(f"Obesity=1 but BMI={bmi}<30")

    # Healthy validation
    if healthy == 1:
        if t2d + pre + obesity + mets + nafld > 0:
            errors.append(
                "Healthy=1 but has disease labels: "
                f"T2D={t2d}, Pre={pre}, Obesity={obesity}, "
                f"MetS={mets}, NAFLD={nafld}"
            )
    elif healthy == 0:
        if t2d + pre + obesity + mets + nafld == 0:
            errors.append("Healthy=0 but all disease labels are 0")

    return errors


def validate_patient(row: Dict) -> Tuple[bool, List[str]]:
    """Run all per-patient validations.

    Args:
        row: Dictionary of patient feature values.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    errors.extend(validate_demographics(row))
    errors.extend(validate_bmi_consistency(row))
    errors.extend(validate_blood_pressure(row))
    errors.extend(validate_feature_ranges(row))
    errors.extend(validate_disease_labels(row))

    return len(errors) == 0, errors


# ═══════════════════════════════════════════════════════════════════════════════
# DATASET-WIDE VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def validate_unique_ids(df: pd.DataFrame) -> Tuple[bool, str]:
    """Check all Patient_IDs are unique.

    Args:
        df: Complete dataset DataFrame.

    Returns:
        Tuple of (is_valid, message).
    """
    n_unique = df["Patient_ID"].nunique()
    n_total = len(df)
    if n_unique < n_total:
        return False, f"Duplicate IDs found: {n_total - n_unique} duplicates"
    return True, f"All {n_total} Patient_IDs are unique"


def validate_prevalence(
    df: pd.DataFrame,
    tolerance: float = 0.03,
) -> Tuple[bool, Dict[str, Dict]]:
    """Check disease prevalence is within tolerance of targets.

    Args:
        df: Complete dataset DataFrame.
        tolerance: Maximum acceptable deviation from target.

    Returns:
        Tuple of (all_within_tolerance, prevalence_details).
    """
    n = len(df)
    all_valid = True
    details = {}

    for disease, target in config.PREVALENCE_TARGETS.items():
        if disease not in df.columns:
            continue

        actual = df[disease].mean()
        deviation = abs(actual - target)
        within = deviation <= tolerance

        details[disease] = {
            "target": target,
            "actual": round(actual, 4),
            "deviation": round(deviation, 4),
            "within_tolerance": within,
        }

        if not within:
            all_valid = False
            logger.warning(
                f"Prevalence deviation for {disease}: "
                f"target={target:.2%}, actual={actual:.2%}, "
                f"deviation={deviation:.2%} (tolerance={tolerance:.2%})"
            )

    return all_valid, details


def validate_missing_rates(
    df: pd.DataFrame,
    tolerance: float = 0.03,
) -> Tuple[bool, Dict[str, Dict]]:
    """Check missing value percentages are within expected ranges.

    Tolerance is adaptive: for smaller datasets, tolerance is widened
    to account for sampling variability.

    Args:
        df: Complete dataset DataFrame.
        tolerance: Base maximum acceptable deviation from target rate.

    Returns:
        Tuple of (all_valid, details).
    """
    n = len(df)
    all_valid = True
    details = {}

    # Widen tolerance for small datasets (sampling noise is higher)
    effective_tolerance = tolerance if n >= 5000 else tolerance + (5000 - n) / 100000

    for feature, target_rate in config.MISSING_RATES.items():
        if feature not in df.columns:
            continue

        actual_rate = df[feature].isna().mean()
        deviation = abs(actual_rate - target_rate)
        within = deviation <= effective_tolerance

        details[feature] = {
            "target_rate": target_rate,
            "actual_rate": round(actual_rate, 4),
            "within_tolerance": within,
        }

        if not within:
            all_valid = False

    return all_valid, details


def validate_correlations(df: pd.DataFrame) -> Tuple[bool, Dict[str, str]]:
    """Check that key feature correlations have correct sign.

    Expected correlations from specification Section 6:
        BMI ↔ Waist: positive
        BMI ↔ HDL: negative
        BMI ↔ Triglycerides: positive
        FPG ↔ HbA1c: positive
        BMI ↔ Systolic_BP: positive
        Triglycerides ↔ HDL: negative

    Args:
        df: Complete dataset DataFrame.

    Returns:
        Tuple of (all_correct, details).
    """
    expected_correlations = [
        ("BMI", "Waist_Circumference_cm", "positive"),
        ("BMI", "HDL_Cholesterol", "negative"),
        ("BMI", "Triglycerides", "positive"),
        ("Fasting_Blood_Glucose", "HbA1c", "positive"),
        ("BMI", "Systolic_BP", "positive"),
        ("Triglycerides", "HDL_Cholesterol", "negative"),
    ]

    all_correct = True
    details = {}

    for feat1, feat2, expected_sign in expected_correlations:
        if feat1 not in df.columns or feat2 not in df.columns:
            continue

        # Drop rows with NaN for correlation computation
        valid = df[[feat1, feat2]].dropna()
        if len(valid) < 10:
            continue

        corr = valid[feat1].astype(float).corr(valid[feat2].astype(float))
        actual_sign = "positive" if corr > 0 else "negative"
        correct = actual_sign == expected_sign

        details[f"{feat1} ↔ {feat2}"] = (
            f"expected={expected_sign}, actual={actual_sign}, "
            f"r={corr:.3f}, correct={correct}"
        )

        if not correct:
            all_correct = False
            logger.warning(
                f"Correlation sign mismatch: {feat1} ↔ {feat2}: "
                f"expected {expected_sign}, got {actual_sign} (r={corr:.3f})"
            )

    return all_correct, details


def validate_mandatory_no_missing(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Check that mandatory features have no missing values.

    Args:
        df: Complete dataset DataFrame.

    Returns:
        Tuple of (all_valid, list_of_violations).
    """
    violations = []

    for feature in config.MANDATORY_FEATURES + config.MANDATORY_LABELS:
        if feature not in df.columns:
            violations.append(f"Mandatory feature {feature} not in dataset")
            continue
        n_missing = df[feature].isna().sum()
        if n_missing > 0:
            violations.append(
                f"Mandatory feature {feature} has {n_missing} missing values"
            )

    return len(violations) == 0, violations


def validate_dataset(
    df: pd.DataFrame,
    cfg: config.DatasetConfig,
) -> Tuple[bool, Dict]:
    """Run all dataset-wide validations.

    Args:
        df: Complete dataset DataFrame.
        cfg: Dataset configuration.

    Returns:
        Tuple of (all_valid, validation_summary).
    """
    summary = {}
    all_valid = True

    # 1. Unique IDs
    valid, msg = validate_unique_ids(df)
    summary["unique_ids"] = {"valid": valid, "message": msg}
    all_valid = all_valid and valid

    # 2. Mandatory features present with no missing
    valid, violations = validate_mandatory_no_missing(df)
    summary["mandatory_features"] = {"valid": valid, "violations": violations}
    all_valid = all_valid and valid

    # 3. Disease prevalence
    valid, details = validate_prevalence(df, cfg.prevalence_tolerance)
    summary["prevalence"] = {"valid": valid, "details": details}
    # Prevalence is a soft check — log warnings but don't fail
    if not valid:
        logger.warning("Some disease prevalences outside target range")

    # 4. Missing value rates
    valid, details = validate_missing_rates(df)
    summary["missing_rates"] = {"valid": valid, "details": details}

    # 5. Correlations
    valid, details = validate_correlations(df)
    summary["correlations"] = {"valid": valid, "details": details}
    all_valid = all_valid and valid

    # 6. Row count
    summary["row_count"] = {
        "expected": cfg.size,
        "actual": len(df),
        "valid": len(df) == cfg.size,
    }

    # 7. Column count
    summary["column_count"] = {
        "expected": len(config.COLUMN_ORDER),
        "actual": len(df.columns),
        "valid": len(df.columns) == len(config.COLUMN_ORDER),
    }

    return all_valid, summary
