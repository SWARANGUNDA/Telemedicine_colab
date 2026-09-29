"""
mapper.py — Feature Mapping Module (Module 3).

Maps extracted raw key-value dictionary items and aliases into canonical
TeleMed feature schema fields across Clinical, Wearable, and Gut modalities.
"""

import logging
import re
from typing import Any, Dict, Tuple
from . import config

logger = logging.getLogger("imdie.mapper")


def clean_key(key: str) -> str:
    """Normalize extracted key string for fuzzy matching."""
    key = str(key).lower().strip()
    key = re.sub(r"[:_=\-\/\(\)]+", " ", key)
    key = " ".join(key.split())
    return key


import difflib

def map_key_to_canonical(raw_key: str) -> Tuple[str, str]:
    """Map a single raw extracted key string to its canonical TeleMed name.

    Returns:
        Tuple of (canonical_key, matched_modality) or (raw_key, 'UNKNOWN').
    """
    cleaned = clean_key(raw_key)

    # Context-Aware Disambiguation Rules
    if "glucose" in cleaned:
        if any(w in cleaned for w in ["fasting", "fbs", "fbg", "plasma glucose"]):
            return "Fasting_Blood_Glucose", "CLINICAL"
        elif any(w in cleaned for w in ["average", "cgm", "mean", "daily", "estimated"]):
            return "Average_Glucose", "WEARABLE"
        elif any(w in cleaned for w in ["variability", "cv", "sd"]):
            return "Glucose_Variability", "WEARABLE"

    if any(w in cleaned for w in ["heart rate", "resting hr", "pulse"]):
        return "Resting_Heart_Rate", "WEARABLE"

    if any(w in cleaned for w in ["steps", "step count"]):
        return "Average_Daily_Steps", "WEARABLE"

    # 1. Exact match in FEATURE_ALIASES
    if cleaned in config.FEATURE_ALIASES:
        canonical = config.FEATURE_ALIASES[cleaned]
        return canonical, get_feature_modality(canonical)

    # 2. Match exact canonical names (case-insensitive)
    all_canonicals = set(config.CLINICAL_FEATURES + config.WEARABLE_FEATURES + config.GUT_FEATURES)
    for canonical in all_canonicals:
        if clean_key(canonical) == cleaned:
            return canonical, get_feature_modality(canonical)

    # 3. Partial alias match with word boundary check
    for alias, canonical in config.FEATURE_ALIASES.items():
        if len(alias) >= 4 and f" {alias} " in f" {cleaned} ":
            return canonical, get_feature_modality(canonical)

    # 4. Fuzzy Levenshtein match for OCR noise errors
    aliases_list = list(config.FEATURE_ALIASES.keys())
    close_matches = difflib.get_close_matches(cleaned, aliases_list, n=1, cutoff=0.78)
    if close_matches:
        best_alias = close_matches[0]
        canonical = config.FEATURE_ALIASES[best_alias]
        return canonical, get_feature_modality(canonical)

    return raw_key, "UNKNOWN"


def get_feature_modality(canonical_key: str) -> str:
    """Determine which modality a canonical key belongs to."""
    if canonical_key in config.CLINICAL_FEATURES:
        return "CLINICAL"
    elif canonical_key in config.WEARABLE_FEATURES:
        return "WEARABLE"
    elif canonical_key in config.GUT_FEATURES:
        return "GUT_MICROBIOME"
    return "UNKNOWN"


def map_extracted_features(extracted_dict: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Map an entire extracted key-value dictionary into canonical feature schemas.

    Args:
        extracted_dict: Raw extracted key-value dictionary.

    Returns:
        Nested dict with keys 'CLINICAL', 'WEARABLE', 'GUT_MICROBIOME', 'UNMAPPED'.
    """
    mapped: Dict[str, Dict[str, Any]] = {
        "CLINICAL": {},
        "WEARABLE": {},
        "GUT_MICROBIOME": {},
        "UNMAPPED": {}
    }

    for raw_key, value in extracted_dict.items():
        canonical, modality = map_key_to_canonical(raw_key)

        # Special Handling for Blood Pressure (Splits "128/82 mmHg" into Systolic_BP: 128 and Diastolic_BP: 82)
        if canonical == "Blood_Pressure" or clean_key(raw_key) in ["blood pressure", "bp", "blood pressure reading", "repeat blood pressure"]:
            val_str = str(value["raw_value"] if isinstance(value, dict) and "raw_value" in value else value).strip()
            bp_match = re.search(r"(\d{2,3})\s*[\/\-]\s*(\d{2,3})", val_str)
            if bp_match:
                sys_val = int(bp_match.group(1))
                dia_val = int(bp_match.group(2))
                mapped["CLINICAL"]["Systolic_BP"] = sys_val
                mapped["CLINICAL"]["Diastolic_BP"] = dia_val
                continue

        if modality in mapped:
            mapped[modality][canonical] = value
        else:
            mapped["UNMAPPED"][raw_key] = value

    return mapped
