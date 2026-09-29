"""
availability.py — Expert Model Availability Check Module (Module 12).

Before prediction, checks whether sufficient information exists for each expert model:
- Clinical Expert: READY / PARTIAL / UNAVAILABLE
- Wearable Expert: READY / PARTIAL / UNAVAILABLE
- Gut Expert: READY / PARTIAL / UNAVAILABLE

Skips unavailable experts seamlessly.
"""

from enum import Enum
from typing import Any, Dict, Set
from . import config


class ExpertStatus(str, Enum):
    READY = "Ready"            # All mandatory & optional features present
    PARTIAL = "Partial"        # All mandatory features present; some optional missing
    UNAVAILABLE = "Unavailable"# Mandatory features missing or no data uploaded


def evaluate_expert_status(
    payload: Dict[str, Any],
    mandatory_set: Set[str],
    optional_set: Set[str]
) -> ExpertStatus:
    """Evaluate readiness status for a single expert model payload.

    Args:
        payload: Feature dictionary routed to expert.
        mandatory_set: Mandatory feature keys.
        optional_set: Optional feature keys.

    Returns:
        ExpertStatus enum value.
    """
    if not payload or len(payload) <= 1:  # Only Patient_ID present
        return ExpertStatus.UNAVAILABLE

    missing_mandatory = [
        feat for feat in mandatory_set
        if feat not in payload or payload[feat] is None
    ]

    if missing_mandatory:
        return ExpertStatus.UNAVAILABLE

    missing_optional = [
        feat for feat in optional_set
        if feat not in payload or payload[feat] is None
    ]

    if missing_optional:
        return ExpertStatus.PARTIAL

    return ExpertStatus.READY


def check_all_experts_availability(
    clinical_payload: Dict[str, Any],
    wearable_payload: Dict[str, Any],
    gut_payload: Dict[str, Any]
) -> Dict[str, ExpertStatus]:
    """Check readiness status for all 3 expert models.

    Returns:
        Dict mapping expert name ➔ ExpertStatus.
    """
    clinical_status = evaluate_expert_status(
        clinical_payload, config.CLINICAL_MANDATORY, config.CLINICAL_OPTIONAL
    )
    wearable_status = evaluate_expert_status(
        wearable_payload, config.WEARABLE_MANDATORY, config.WEARABLE_OPTIONAL
    )
    gut_status = evaluate_expert_status(
        gut_payload, config.GUT_MANDATORY, config.GUT_OPTIONAL
    )

    return {
        "Clinical Expert": clinical_status,
        "Wearable Expert": wearable_status,
        "Gut Expert": gut_status
    }
