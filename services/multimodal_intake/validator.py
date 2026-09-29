"""
validator.py — Feature Validation & Anomaly Detection Module (Module 6).
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from . import config

logger = logging.getLogger("imdie.validator")


def detect_ocr_anomalies(feature_name: str, value: Any) -> Tuple[bool, str, Optional[float]]:
    """Detect common OCR errors, missing decimals, decimal shifts, and character confusion.

    Examples:
    - HbA1c = 65 -> suggest 6.5
    - HbA1c = 0.65 -> suggest 6.5
    - Fasting_Blood_Glucose = 13.2 -> suggest 132
    - Fasting_Blood_Glucose = -110 -> invalid
    - OCR char confusion 'O' -> 0, 'I' -> 1, 'S' -> 5

    Returns:
        Tuple of (has_anomaly, explanation, suggested_value)
    """
    if value is None or feature_name in ["Patient_ID", "Gender"] or str(feature_name).startswith("Family_History_"):
        return False, "", None
    if isinstance(value, str) and value.strip() in ["Male", "Female", "Other", ""]:
        return False, "", None

    val_str = str(value).strip()

    # Character confusion fixes attempt
    clean_num_str = val_str.replace("O", "0").replace("o", "0").replace("I", "1").replace("l", "1").replace("S", "5")
    try:
        val_float = float(clean_num_str)
    except (ValueError, TypeError):
        return True, f"Value '{value}' contains unparseable characters", None

    if val_float < 0:
        return True, f"{feature_name} cannot be negative ({val_float})", None

    # HbA1c decimal shifts
    if feature_name == "HbA1c":
        if val_float >= 30.0 and val_float <= 150.0:
            suggested = round(val_float / 10.0, 1)
            return True, f"Possible OCR decimal shift: HbA1c value {val_float}% exceeds physiological max (16%). Did you mean {suggested}%?", suggested
        elif val_float > 0.0 and val_float < 2.0:
            suggested = round(val_float * 10.0, 1)
            return True, f"Possible OCR decimal shift: HbA1c value {val_float}% is below physiological min (3.5%). Did you mean {suggested}%?", suggested

    # Fasting Blood Glucose decimal shifts
    if feature_name in ["Fasting_Blood_Glucose", "CGM_Average_Glucose"]:
        if val_float > 0.0 and val_float < 25.0:
            suggested_mg = round(val_float * 10.0, 1)
            return True, f"Fasting Glucose {val_float} appears exceptionally low for mg/dL. If in mmol/L, it converts to {round(val_float * 18.0182, 1)} mg/dL; if decimal shift, {suggested_mg} mg/dL.", suggested_mg

    return False, "", None


def validate_feature_value(feature_name: str, value: Any) -> Tuple[bool, str]:
    """Validate a single feature against physiological limits.

    Args:
        feature_name: Canonical feature name.
        value: Feature value.

    Returns:
        Tuple of (is_valid, error_reason).
    """
    if value is None:
        return True, ""

    if feature_name == "Gender":
        val_str = str(value).strip().capitalize()
        if val_str not in ["Male", "Female", "Other", "0", "1"]:
            return False, f"Gender must be Male or Female, got '{value}'"
        return True, ""

    if feature_name == "Patient_ID":
        return True, ""

    if feature_name.startswith("Family_History_"):
        raw_str = str(value).strip().lower()
        if isinstance(value, dict) and "raw_value" in value:
            raw_str = str(value["raw_value"]).strip().lower()
        if raw_str in ["yes", "y", "true", "1", "1.0", "reported", "present", "no", "n", "false", "0", "0.0", "absent"]:
            return True, ""
        return False, f"{feature_name} must be binary (0/1), got '{value}'"

    has_anomaly, explanation, _ = detect_ocr_anomalies(feature_name, value)
    if has_anomaly:
        return False, explanation

    try:
        val_float = float(value)
        bounds = config.PHYSIOLOGICAL_BOUNDS.get(feature_name)
        if bounds:
            min_b = bounds["min"]
            max_b = bounds["max"]
            if val_float < min_b or val_float > max_b:
                return False, f"{feature_name} value {val_float} is outside physiological bounds [{min_b}, {max_b}]"
    except (ValueError, TypeError):
        pass

    return True, ""


def detect_suspicious_value(feature_name: str, value: Any) -> Tuple[bool, str]:
    """Detect extreme but physically possible clinical readings for verification tagging.

    Returns:
        Tuple of (is_suspicious, explanation_reason).
    """
    try:
        val_f = float(value)
        if feature_name == "HbA1c" and val_f >= 12.0:
            return True, f"Extremely high HbA1c ({val_f}%) flagged for urgent clinical review."
        if feature_name in ["Fasting_Blood_Glucose", "Average_Glucose"] and val_f >= 250.0:
            return True, f"Severe hyperglycemia ({val_f} mg/dL) flagged for urgent clinical review."
        if feature_name == "Systolic_BP" and val_f >= 180.0:
            return True, f"Hypertensive crisis Systolic BP ({val_f} mmHg) flagged for urgent clinical review."
        if feature_name == "Diastolic_BP" and val_f >= 120.0:
            return True, f"Hypertensive crisis Diastolic BP ({val_f} mmHg) flagged for urgent clinical review."
    except (ValueError, TypeError):
        pass
    return False, ""


def validate_cross_field_consistency(features: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Perform cross-field clinical sanity validation.

    Checks:
    - Systolic BP > Diastolic BP
    - Derived BMI vs. Weight / (Height/100)^2
    """
    issues: List[Dict[str, Any]] = []

    # Blood Pressure consistency
    sbp = features.get("Systolic_BP")
    dbp = features.get("Diastolic_BP")
    if sbp is not None and dbp is not None:
        try:
            if float(sbp) <= float(dbp):
                issues.append({
                    "feature": "Systolic_BP",
                    "type": "CROSS_FIELD_BP",
                    "message": f"Invalid Blood Pressure: Systolic BP ({sbp}) must be greater than Diastolic BP ({dbp})"
                })
        except (ValueError, TypeError):
            pass

    # Height, Weight, BMI consistency
    ht = features.get("Height") or features.get("Height_cm")
    wt = features.get("Weight") or features.get("Weight_kg")
    bmi = features.get("BMI")

    if ht is not None and wt is not None:
        try:
            ht_m = float(ht) / 100.0
            calc_bmi = round(float(wt) / (ht_m ** 2), 1)
            if bmi is not None:
                stored_bmi = float(bmi)
                if abs(stored_bmi - calc_bmi) > 2.0:
                    issues.append({
                        "feature": "BMI",
                        "type": "CROSS_FIELD_BMI",
                        "calculated_bmi": calc_bmi,
                        "stored_bmi": stored_bmi,
                        "message": f"BMI mismatch: Stored BMI ({stored_bmi}) differs materially from calculated BMI ({calc_bmi}) derived from Height={ht}cm, Weight={wt}kg. Marked for user VERIFY."
                    })
        except (ValueError, TypeError, ZeroDivisionError):
            pass

    return issues


def validate_feature_dict(features: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str], Dict[str, Dict[str, Any]]]:
    """Validate full feature dictionary and create verify flags for anomalies.

    Args:
        features: Dictionary of canonical features and values.

    Returns:
        Tuple of (clean_features, validation_errors, validation_warnings, verify_flags).
    """
    clean: Dict[str, Any] = {}
    errors: List[str] = []
    warnings: List[str] = []
    verify_flags: Dict[str, Dict[str, Any]] = {}

    for feat, val in features.items():
        has_anomaly, explanation, suggested = detect_ocr_anomalies(feat, val)
        if has_anomaly:
            warnings.append(explanation)
            verify_flags[feat] = {
                "feature": feat,
                "current_value": val,
                "suggested_value": suggested,
                "explanation": explanation,
                "status": "VERIFY"
            }
            # Only keep if suggested value exists, otherwise drop unparseable string
            if suggested is not None:
                clean[feat] = suggested
            continue
        else:
            is_valid, reason = validate_feature_value(feat, val)
            if is_valid:
                clean[feat] = val
            else:
                errors.append(reason)

    # Auto-derive BMI if Height and Weight exist but BMI is missing
    ht = clean.get("Height") or clean.get("Height_cm")
    wt = clean.get("Weight") or clean.get("Weight_kg")
    if ht and wt and "BMI" not in clean:
        try:
            ht_m = float(ht) / 100.0
            wt_k = float(wt)
            if ht_m > 0:
                clean["BMI"] = round(wt_k / (ht_m ** 2), 1)
        except (ValueError, TypeError, ZeroDivisionError):
            pass

    # Cross-field consistency checks
    cross_issues = validate_cross_field_consistency(clean)
    for issue in cross_issues:
        warnings.append(issue["message"])
        if issue["type"] == "CROSS_FIELD_BMI":
            verify_flags["BMI"] = {
                "feature": "BMI",
                "current_value": clean.get("BMI"),
                "suggested_value": issue["calculated_bmi"],
                "explanation": issue["message"],
                "status": "VERIFY"
            }

    return clean, errors, warnings, verify_flags

