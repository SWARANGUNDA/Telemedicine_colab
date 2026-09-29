"""
validation.py — Patient-level and dataset-wide validation module.

Validates physiological limits, time-budget constraints, glucose summation rules,
activity consistency, PID alignment, and statistical correlation signs.
Supports single-patient regeneration logic.
"""

import logging
from typing import Dict, Tuple, List, Any
import numpy as np
import pandas as pd

from . import constants

logger = logging.getLogger(__name__)


def validate_patient_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a single patient's wearable measurements against physiological rules.

    Args:
        record: Dictionary containing single patient feature values.

    Returns:
        Tuple of (is_valid: bool, list_of_error_messages: List[str]).
    """
    errors: List[str] = []

    # 1. Feature Range Bounds Check
    for feature, (min_val, max_val) in constants.FEATURE_BOUNDS.items():
        if feature in record and record[feature] is not None and not np.isnan(record[feature]):
            val = float(record[feature])
            if val < min_val or val > max_val:
                errors.append(
                    f"Outlier_Bounds_Violation: {feature}={val:.1f} outside [{min_val}, {max_val}]"
                )

    # 2. Daily Time-Budget Check (Active + Sedentary + Sleep * 60 <= 1440)
    if "Active_Minutes" in record and "Sedentary_Time_Minutes" in record and "Sleep_Duration" in record:
        active = float(record["Active_Minutes"])
        sedentary = float(record["Sedentary_Time_Minutes"])
        sleep_min = float(record["Sleep_Duration"]) * 60.0
        total_time = active + sedentary + sleep_min

        if total_time > constants.DAILY_TIME_BUDGET_MINUTES + 1.0:  # 1 min grace tolerance
            errors.append(
                f"Time_Budget_Exceeded: Total minutes {total_time:.1f} > 1440"
            )

    # 3. Glucose Summation Check (TIR + TAR <= 100%)
    if "Time_In_Range" in record and "Time_Above_Range" in record:
        tir = float(record["Time_In_Range"])
        tar = float(record["Time_Above_Range"])

        if (tir + tar) > 100.1:
            errors.append(
                f"Glucose_Sum_Mismatch: TIR ({tir:.1f}%) + TAR ({tar:.1f}%) > 100%"
            )

    # 4. Activity Consistency Check
    if "Average_Daily_Steps" in record and "Sedentary_Time_Minutes" in record:
        steps = float(record["Average_Daily_Steps"])
        sedentary = float(record["Sedentary_Time_Minutes"])

        if steps > 20000 and sedentary > 720:
            errors.append(
                f"Activity_Inconsistency: Extremely high steps ({steps}) with >12h sedentary time"
            )

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_wearable_dataset(
    wearable_df: pd.DataFrame,
    clinical_df: pd.DataFrame,
) -> Tuple[bool, Dict[str, Any]]:
    """Validate the complete generated wearable dataset against the master clinical dataset.

    Args:
        wearable_df: Generated wearable DataFrame.
        clinical_df: Master clinical DataFrame.

    Returns:
        Tuple of (all_passed: bool, validation_summary: Dict).
    """
    logger.info("Executing dataset-wide validation suite...")
    summary: Dict[str, Any] = {}
    all_passed = True

    # Check 1: Patient ID Alignment & Preservation
    pid_match = (
        len(wearable_df) == len(clinical_df)
        and (wearable_df["Patient_ID"].values == clinical_df["Patient_ID"].values).all()
    )
    summary["pid_alignment"] = {
        "valid": pid_match,
        "message": "✓ Patient IDs match Clinical Master perfectly" if pid_match else "✗ Patient ID mismatch!",
    }
    if not pid_match:
        all_passed = False

    # Check 2: Preserved Identity Fields (Age, Gender)
    age_match = (wearable_df["Age"].values == clinical_df["Age"].values).all()
    gender_match = (wearable_df["Gender"].values == clinical_df["Gender"].values).all()
    identity_valid = age_match and gender_match
    summary["identity_preservation"] = {
        "valid": identity_valid,
        "message": "✓ Age and Gender preserved 100%" if identity_valid else "✗ Identity mutation detected!",
    }
    if not identity_valid:
        all_passed = False

    # Check 3: Mandatory Feature Completeness (0% missing on generated wearable features)
    missing_counts = wearable_df[constants.WEARABLE_GENERATED_FEATURES].isnull().sum()
    total_missing = missing_counts.sum()
    summary["mandatory_completeness"] = {
        "valid": total_missing == 0,
        "message": f"✓ 0 missing values across generated features" if total_missing == 0 else f"⚠ {total_missing} missing values present",
    }

    # Check 4: Range Bounds Across Whole Dataset
    out_of_bounds = 0
    for col, (min_val, max_val) in constants.FEATURE_BOUNDS.items():
        if col in wearable_df.columns:
            vals = wearable_df[col].dropna()
            oob = ((vals < min_val) | (vals > max_val)).sum()
            out_of_bounds += oob

    summary["range_bounds"] = {
        "valid": out_of_bounds == 0,
        "message": "✓ All feature values within physiological limits" if out_of_bounds == 0 else f"✗ {out_of_bounds} values out of bounds!",
    }
    if out_of_bounds > 0:
        all_passed = False

    # Check 5: Key Correlation Direction Sign Verification
    corr_matrix = wearable_df[constants.WEARABLE_GENERATED_FEATURES].corr()
    corr_checks: Dict[str, Any] = {}

    for (feat1, feat2), expected_direction in constants.EXPECTED_CORRELATIONS.items():
        if feat1 in corr_matrix.columns and feat2 in corr_matrix.columns:
            val = corr_matrix.loc[feat1, feat2]
            is_valid = (val < 0) if expected_direction == "negative" else (val > 0)
            corr_checks[f"{feat1} ↔ {feat2}"] = {
                "correlation": round(val, 3),
                "expected": expected_direction,
                "valid": is_valid,
            }
            if not is_valid:
                all_passed = False

    summary["correlations"] = {
        "valid": all_passed,
        "details": corr_checks,
    }

    return all_passed, summary
