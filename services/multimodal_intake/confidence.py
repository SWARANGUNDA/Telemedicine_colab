"""
confidence.py — Prediction Confidence Evaluator Module (Module 14).

Generates:
- Prediction Confidence Grade (High / Medium / Low)
- Rationale / Clinical Justification Explanation

Example:
  Confidence: Medium
  Reason: Gut microbiome data unavailable. Clinical data complete. Wearable data partially complete.
"""

from typing import Dict
from .availability import ExpertStatus
from .adaptive_strategy import AdaptivePredictionStrategy


def evaluate_prediction_confidence(
    availability_map: Dict[str, ExpertStatus],
    quality_scores: Dict[str, float]
) -> Dict[str, str]:
    """Calculate confidence grade and generate natural-language rationale.

    Args:
        availability_map: Map of Expert name ➔ ExpertStatus.
        quality_scores: Map of quality score metrics.

    Returns:
        Dict with keys 'confidence_level', 'confidence_reason'.
    """
    strategy = AdaptivePredictionStrategy(availability_map)
    active_count = len(strategy.active_experts)
    overall_q = quality_scores.get("overall_score", 0.0)

    reasons = []

    for expert, status in availability_map.items():
        if status == ExpertStatus.READY:
            reasons.append(f"{expert} data complete.")
        elif status == ExpertStatus.PARTIAL:
            reasons.append(f"{expert} data partially complete.")
        elif status == ExpertStatus.UNAVAILABLE:
            reasons.append(f"{expert} data unavailable.")

    # Determine confidence tier
    if active_count == 3 and overall_q >= 85.0:
        confidence = "High"
    elif active_count >= 2 and overall_q >= 60.0:
        confidence = "Medium"
    elif active_count >= 1:
        confidence = "Low"
    else:
        confidence = "None"
        reasons.append("Mandatory features missing across all modalities.")

    reason_str = " ".join(reasons)

    return {
        "confidence_level": confidence,
        "confidence_reason": reason_str,
        "strategy": strategy.get_strategy_name()
    }

def calculate_feature_multifactor_confidence(
    feature_name: str,
    value: float = None,
    extraction_method: str = "PATTERN_MATCH_KEYVAL",
    has_valid_unit: bool = True,
    is_physio_valid: bool = True,
    is_suspicious: bool = False
) -> float:
    """Calculate multi-factor confidence score for a single extracted feature.

    Formula:
      C = BaseMethodScore * UnitWeight * PhysioWeight * ContextWeight
    """
    base_scores = {
        "REGEX_PATIENT_ID": 1.00,
        "REGEX_AGE": 1.00,
        "REGEX_GENDER": 1.00,
        "REGEX_FAMILY_HISTORY": 0.95,
        "CSV_HEADER_ROW_PAIR": 0.98,
        "TABLE_PARSE": 0.95,
        "PATTERN_MATCH_VALUNIT": 0.95,
        "PATTERN_MATCH_KEYVAL": 0.90,
        "INLINE_MULTI_PAIR": 0.90,
        "OCR_EXTRACTION": 0.85,
        "FUZZY_ALIAS": 0.85,
        "DERIVED_RULE": 0.90
    }

    base = base_scores.get(extraction_method, 0.85)
    unit_w = 1.00 if has_valid_unit else 0.92
    physio_w = 1.00 if is_physio_valid else 0.50
    suspicious_w = 0.85 if is_suspicious else 1.00

    score = round(base * unit_w * physio_w * suspicious_w, 3)
    return max(0.0, min(1.0, score))
