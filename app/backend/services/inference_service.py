"""
inference_service.py — Service Wrapper around FusionInferenceEngine & ExpertInferenceEngine.

Wraps the frozen Phase 3 experts and Phase 4 Fusion Engine across all
7 adaptive modality pathways.
Sanitizes NaN values for JSON compliance.
"""

import math
import logging
from typing import Any, Dict, Optional
import numpy as np

from ai.inference.fusion_inference import FusionInferenceEngine

logger = logging.getLogger("web_platform.services.inference")


def sanitize_nans(obj: Any) -> Any:
    """Recursively convert NaN/Inf float values to None for JSON compliance."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: sanitize_nans(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_nans(item) for item in obj]
    return obj


class InferenceService:
    """Service layer wrapping FusionInferenceEngine."""

    def __init__(self):
        self.fusion_engine = FusionInferenceEngine().load()

    def run_prediction(
        self,
        patient_features: Dict[str, Optional[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Pass confirmed patient feature dictionaries to FusionInferenceEngine.

        Args:
            patient_features: Dict mapping modality ('clinical', 'wearable', 'gut')
                to feature dictionary (or None if missing).

        Returns:
            Structured prediction output dict.
        """
        logger.info("Executing Fusion Engine inference...")
        predictions = self.fusion_engine.predict(patient_features)
        pathway_used = predictions[list(predictions.keys())[0]]["pathway"]
        logger.info("Fusion Inference complete using pathway: %s", pathway_used)

        raw_res = {
            "pathway_used": pathway_used,
            "disease_outcomes": predictions,
        }
        return sanitize_nans(raw_res)
