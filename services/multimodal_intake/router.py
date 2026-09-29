"""
router.py — Feature Routing Engine Module (Module 11).

After validation and fusion, separates features into isolated, dedicated payloads:
- Clinical Features ➔ Clinical Expert
- Wearable Features ➔ Wearable Expert
- Gut Features ➔ Gut Expert

Each expert model receives only its own relevant feature schema.
"""

import logging
from typing import Any, Dict
from .fuser import PatientProfile

logger = logging.getLogger("imdie.router")


class ExpertPayloads:
    """Container for expert model input payloads."""

    def __init__(
        self,
        patient_id: str,
        clinical_payload: Dict[str, Any],
        wearable_payload: Dict[str, Any],
        gut_payload: Dict[str, Any]
    ):
        self.patient_id = patient_id
        self.clinical_payload = clinical_payload
        self.wearable_payload = wearable_payload
        self.gut_payload = gut_payload

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Patient_ID": self.patient_id,
            "clinical_expert_payload": self.clinical_payload,
            "wearable_expert_payload": self.wearable_payload,
            "gut_expert_payload": self.gut_payload
        }


def route_features_to_experts(profile: PatientProfile) -> ExpertPayloads:
    """Route fused patient profile features to isolated expert payloads.

    Args:
        profile: Fused PatientProfile.

    Returns:
        ExpertPayloads containing isolated payloads for each expert.
    """
    # Ensure Patient_ID is passed to each expert payload for tracking
    clin_payload = {"Patient_ID": profile.patient_id, **profile.clinical_features}
    wear_payload = {"Patient_ID": profile.patient_id, **profile.wearable_features}
    gut_payload = {"Patient_ID": profile.patient_id, **profile.gut_features}

    payloads = ExpertPayloads(
        patient_id=profile.patient_id,
        clinical_payload=clin_payload,
        wearable_payload=wear_payload,
        gut_payload=gut_payload
    )

    logger.info(
        "Routed features for '%s': Clinical (%d keys), Wearable (%d keys), Gut (%d keys)",
        profile.patient_id, len(clin_payload), len(wear_payload), len(gut_payload)
    )

    return payloads
