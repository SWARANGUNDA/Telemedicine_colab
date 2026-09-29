"""
fuser.py — Multi-Report Fusion Module (Module 10).

Users may upload multiple reports (e.g. Health Checkup + Lipid Profile + LFT + CGM).
Merges all extracted reports into one unified patient profile while resolving
duplicates and handling missing values.
"""

import logging
from typing import Any, Dict, List, Tuple
from .resolver import merge_and_resolve_reports

logger = logging.getLogger("imdie.fuser")


class PatientProfile:
    """Unified Patient Profile containing fused multi-report features."""

    def __init__(self, patient_id: str = "P_GUEST"):
        self.patient_id: str = patient_id
        self.clinical_features: Dict[str, Any] = {}
        self.wearable_features: Dict[str, Any] = {}
        self.gut_features: Dict[str, Any] = {}
        self.raw_reports_count: int = 0
        self.fusion_warnings: List[str] = []
        self.patient_id_conflict: bool = False
        self.different_patient_warning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Patient_ID": self.patient_id,
            "clinical_features": self.clinical_features,
            "wearable_features": self.wearable_features,
            "gut_features": self.gut_features,
            "raw_reports_count": self.raw_reports_count,
            "fusion_warnings": self.fusion_warnings,
            "patient_id_conflict": self.patient_id_conflict,
            "patient_id_conflict_requires_confirmation": self.patient_id_conflict
        }


def fuse_multiple_reports(
    processed_reports: List[Dict[str, Any]]
) -> Tuple[PatientProfile, List[str]]:
    """Fuse multiple processed report dictionaries into a single PatientProfile.

    Args:
        processed_reports: List of extracted/normalized report dicts containing
                           'CLINICAL', 'WEARABLE', 'GUT_MICROBIOME' feature maps.

    Returns:
        Tuple of (unified_patient_profile, cumulative_warnings).
    """
    profile = PatientProfile()
    profile.raw_reports_count = len(processed_reports)
    all_warnings: List[str] = []

    clinical_reports: List[Dict[str, Any]] = []
    wearable_reports: List[Dict[str, Any]] = []
    gut_reports: List[Dict[str, Any]] = []

    cumulative_conflict_map: Dict[str, Dict[str, Any]] = {}
    pids_found = set()

    for report in processed_reports:
        metadata = report.get("metadata", {})
        top_pid = report.get("Patient_ID")
        if top_pid:
            raw_top = top_pid["raw_value"] if isinstance(top_pid, dict) and "raw_value" in top_pid else str(top_pid)
            if raw_top and raw_top != "P_GUEST":
                pids_found.add(raw_top)

        for mod in ["CLINICAL", "WEARABLE", "GUT_MICROBIOME"]:
            feat_dict = report.get(mod, {})
            pid = feat_dict.get("Patient_ID")
            if pid:
                raw_pid = pid["raw_value"] if isinstance(pid, dict) and "raw_value" in pid else str(pid)
                if raw_pid and raw_pid != "P_GUEST":
                    pids_found.add(raw_pid)

        clin_feats = report.get("CLINICAL", {})
        has_primary_clin = any(k not in ("Patient_ID", "Age", "Gender") for k in clin_feats.keys())
        if has_primary_clin:
            clinical_reports.append({"features": clin_feats, "metadata": metadata})
        if "WEARABLE" in report and report["WEARABLE"]:
            wearable_reports.append({"features": report["WEARABLE"], "metadata": metadata})
        if "GUT_MICROBIOME" in report and report["GUT_MICROBIOME"]:
            gut_reports.append({"features": report["GUT_MICROBIOME"], "metadata": metadata})

    if len(pids_found) > 1:
        pid_list_str = ", ".join(f"'{p}'" for p in sorted(pids_found))
        pid_warn = f"⚠️ Patient ID Mismatch Detected across reports ({pid_list_str}). Please confirm these uploaded reports belong to the same individual patient before proceeding."
        all_warnings.append(pid_warn)
        profile.different_patient_warning = pid_warn
        profile.patient_id_conflict = True

    # Merge clinical features
    if clinical_reports:
        merged_clin, warn, c_map = merge_and_resolve_reports(clinical_reports)
        profile.clinical_features = merged_clin
        all_warnings.extend(warn)
        cumulative_conflict_map.update(c_map)

    # Merge wearable features
    if wearable_reports:
        merged_wear, warn, c_map = merge_and_resolve_reports(wearable_reports)
        profile.wearable_features = merged_wear
        all_warnings.extend(warn)
        cumulative_conflict_map.update(c_map)

    # Merge gut features
    if gut_reports:
        merged_gut, warn, c_map = merge_and_resolve_reports(gut_reports)
        profile.gut_features = merged_gut
        all_warnings.extend(warn)
        cumulative_conflict_map.update(c_map)

    # Extract Patient_ID if present
    patient_id = (
        profile.clinical_features.get("Patient_ID") or
        profile.wearable_features.get("Patient_ID") or
        profile.gut_features.get("Patient_ID") or
        "P_GUEST"
    )
    if isinstance(patient_id, dict):
        patient_id = patient_id.get("raw_value", "P_GUEST")

    profile.patient_id = str(patient_id)
    profile.fusion_warnings = all_warnings
    profile.conflict_map = cumulative_conflict_map

    logger.info(
        "Fused %d reports for patient '%s': Clinical (%d), Wearables (%d), Gut (%d)",
        profile.raw_reports_count, profile.patient_id,
        len(profile.clinical_features), len(profile.wearable_features), len(profile.gut_features)
    )

    return profile, all_warnings
