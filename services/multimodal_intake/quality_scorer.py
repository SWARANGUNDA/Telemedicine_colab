"""
quality_scorer.py — Data Quality Assessment Module (Module 7).

Calculates a deterministic, objective Data Quality Score (0 - 100) and transparent
"Why this score?" breakdown payload.
"""

from typing import Any, Dict, List, Set
from . import config


def calculate_data_quality_scores(
    clinical_dict: Dict[str, Any],
    wearable_dict: Dict[str, Any],
    gut_dict: Dict[str, Any],
    verify_flags: Dict[str, Any] = None,
    conflict_map: Dict[str, Any] = None,
    user_status_map: Dict[str, str] = None,
    imputed_fields: Set[str] = None
) -> Dict[str, Any]:
    """Calculate deterministic Data Quality Score (0-100) and breakdown components.

    Formula:
      Data Quality Score = max(0.0, min(Cap, BaseScore - ImputationDeductions))
    """
    verify_flags = verify_flags or {}
    conflict_map = conflict_map or {}
    user_status_map = user_status_map or {}
    imputed_fields = imputed_fields or set()

    def extract_val(val_item):
        if val_item is None:
            return None
        if isinstance(val_item, dict):
            return val_item.get("raw_value") if "raw_value" in val_item else val_item.get("value")
        return val_item

    def extract_conf(val_item, feat_name):
        status = user_status_map.get(feat_name)
        if status in ["MANUAL", "EDITED"]:
            return 1.0
        if isinstance(val_item, dict):
            return float(val_item.get("confidence", 0.90))
        return 1.0

    # 1. Evaluate Active Modalities and Counts
    clin_primary = [
        "Height", "Weight", "BMI", "Waist_Circumference", "Systolic_BP", "Diastolic_BP",
        "Fasting_Blood_Glucose", "HbA1c", "LDL", "HDL", "Triglycerides", "ALT", "AST",
        "Family_History_Diabetes", "Family_History_Hypertension", "Family_History_CVD"
    ]
    clin_all = [f for f in config.CLINICAL_FEATURES if f != "Patient_ID"]
    wear_features = config.WEARABLE_FEATURES
    gut_features = config.GUT_FEATURES

    has_clinical = any(extract_val(clinical_dict.get(f)) is not None for f in clin_primary) if clinical_dict else False
    has_wearable = any(extract_val(wearable_dict.get(f)) is not None for f in wear_features) if wearable_dict else False
    has_gut = any(extract_val(gut_dict.get(f)) is not None for f in gut_features) if gut_dict else False
    has_cgm = any(extract_val(wearable_dict.get(f)) is not None for f in ["CGM_Average_Glucose", "CGM_Glucose_CV", "CGM_Time_In_Range"]) if wearable_dict else False

    # Filter canonical feature targets for active modalities only
    active_target_features = []
    if has_clinical:
        active_target_features.extend(clin_all)
    if has_wearable:
        active_target_features.extend(wear_features)
    if has_gut:
        active_target_features.extend(gut_features)

    # Classify feature counts
    provided_count = 0
    extracted_count = 0
    manual_count = 0
    edited_count = 0
    missing_count = 0
    verify_count = len(verify_flags)
    conflict_count = len(conflict_map)

    confidence_scores = []
    deductions_list = []

    combined_dict = {}
    if clinical_dict:
        combined_dict.update(clinical_dict)
    if wearable_dict:
        combined_dict.update(wearable_dict)
    if gut_dict:
        combined_dict.update(gut_dict)

    if active_target_features:
        for feat in active_target_features:
            item = combined_dict.get(feat)
            val = extract_val(item)
            status = user_status_map.get(feat)

            if val is not None and str(val).strip() != "":
                provided_count += 1
                conf = extract_conf(item, feat)
                confidence_scores.append(conf)

                if status == "MANUAL":
                    manual_count += 1
                elif status == "EDITED":
                    edited_count += 1
                else:
                    extracted_count += 1
            else:
                missing_count += 1

    # 2. Compute Completeness & Confidence
    total_active_target = len(active_target_features)
    completeness_pct = (provided_count / total_active_target) * 100.0 if total_active_target > 0 else 0.0
    mean_conf_pct = (sum(confidence_scores) / len(confidence_scores)) * 100.0 if confidence_scores else 0.0

    # 3. Input Quality Score & Coverage
    active_mod_count = sum([1 for m in [has_clinical, has_wearable, has_gut] if m])
    multimodal_coverage_pct = round((active_mod_count / 3.0) * 100.0, 1) if active_mod_count > 0 else 0.0
    input_quality_base = round(0.65 * completeness_pct + 0.35 * mean_conf_pct, 1) if active_mod_count > 0 else 0.0

    # 4. Imputation Deduction
    imputed_count = len(imputed_fields) if imputed_fields is not None else 0
    imputation_deductions = round(imputed_count * 3.0, 1)

    if missing_count > 0:
        deductions_list.append(f"Missing {missing_count} feature(s) across active modalities (-{round(missing_count * 2.5, 1)}%)")
    if imputed_count > 0:
        deductions_list.append(f"{imputed_count} feature(s) backend median-imputed before prediction (-{imputation_deductions}%)")
    if not (has_clinical and has_wearable and has_gut):
        missing_mods = []
        if not has_clinical: missing_mods.append("Clinical")
        if not has_wearable: missing_mods.append("Wearable")
        if not has_gut: missing_mods.append("Gut")
        deductions_list.append(f"Multimodal coverage is {multimodal_coverage_pct}% ({', '.join(missing_mods)} missing)")

    # 5. Capping Rules for Unresolved VERIFY or CONFLICT items
    cap = 100.0
    if verify_count > 0 and conflict_count > 0:
        cap = 50.0
        deductions_list.append("Score capped at 50.0% due to unresolved VERIFY anomalies and CONFLICT items")
    elif conflict_count > 0:
        cap = 60.0
        deductions_list.append("Score capped at 60.0% due to unresolved duplicate feature CONFLICTS")
    elif verify_count > 0:
        cap = 65.0
        deductions_list.append("Score capped at 65.0% due to unresolved VERIFY clinical anomalies")

    raw_final = input_quality_base - imputation_deductions
    final_score = round(max(0.0, min(cap, raw_final)), 1)

    # 6. Quality Label
    if provided_count == 0 or final_score == 0.0:
        quality_label = "NO DATA / NOT ASSESSED"
    elif final_score >= 85.0:
        quality_label = "High Input Quality"
    elif final_score >= 60.0:
        quality_label = "Moderate Input Quality"
    else:
        quality_label = "Low Input Quality / Verification Required"

    score_breakdown = {
        "overall_quality_score": final_score,
        "input_quality_score": final_score,
        "multimodal_coverage_pct": multimodal_coverage_pct,
        "quality_label": quality_label,
        "base_score": input_quality_base,
        "cap_applied": cap if cap < 100.0 else None,
        "counts": {
            "provided": provided_count,
            "extracted": extracted_count,
            "manual": manual_count,
            "edited": edited_count,
            "missing": missing_count,
            "imputed": imputed_count,
            "verify": verify_count,
            "conflict": conflict_count
        },
        "coverage": {
            "clinical": has_clinical,
            "wearable": has_wearable,
            "gut": has_gut,
            "cgm": has_cgm
        },
        "deductions_list": deductions_list if deductions_list else ["Full data completeness and high extraction confidence verified."]
    }

    return {
        "overall_quality_score": final_score,
        "overall_score": final_score,
        "input_quality_score": final_score,
        "multimodal_coverage_pct": multimodal_coverage_pct,
        "quality_label": quality_label,
        "clinical_score": round(completeness_pct, 1),
        "wearable_score": round(mean_conf_pct, 1),
        "gut_score": multimodal_coverage_pct,
        "score_breakdown": score_breakdown
    }

