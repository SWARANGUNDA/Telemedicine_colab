"""
rag_patient_contract.py — RAG Patient Context Contract Constructor.

Builds structured RAG patient context payloads adhering to Part B specification.
Passes feature, value, importance_rank, and model_effect_direction while
hiding raw numerical SHAP values from the LLM prompt.
"""

import logging
from typing import Any, Dict, List, Optional

try:
    from ai.explainability.unified_xai_engine import UnifiedXAIEngine
except (ImportError, ValueError):
    from ai.explainability.unified_xai_engine import UnifiedXAIEngine
from . import config

logger = logging.getLogger("services.medical_rag.patient_contract")


def build_rag_patient_context(
    patient_id: str,
    patient_features: Dict[str, Optional[Dict[str, Any]]],
    xai_engine: Optional[UnifiedXAIEngine] = None,
    predict_response: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Construct structured patient context contract object for RAG ingestion.
    Uses immutable predict_response predictions snapshot when available to ensure
    100% single-source-of-truth alignment between Report, SHAP, and Q&A modes.
    """
    if predict_response and isinstance(predict_response, dict) and "predictions" in predict_response:
        predictions = predict_response.get("predictions", {})
        routing_meta = predict_response.get("routing_metadata", {})
        active_modalities = routing_meta.get("modalities_supplied", list(patient_features.keys()))
        missing_modalities = routing_meta.get("missing_modalities", [])
        pathway_key = routing_meta.get("effective_pathway", "C")

        disease_outcomes = {}
        for disease, info in predictions.items():
            prob = float(info.get("calibrated_probability", info.get("probability", 0.0)))
            pred = int(info.get("predicted_class", info.get("prediction", 0)))
            thresh = float(info.get("threshold_used", info.get("threshold", 0.3)))
            risk_level = info.get("risk_level", "LOW")

            if pred == 1 or risk_level == "POSITIVE":
                risk_category = "High Risk / Elevated Signal"
            elif prob >= 0.35:
                risk_category = "Moderate Risk"
            else:
                risk_category = "Low Risk / Normal Signal"

            disease_outcomes[disease] = {
                "disease": disease,
                "risk_category": risk_category,
                "fusion_probability": prob,
                "prediction": pred,
                "threshold": thresh,
                "risk_level": risk_level,
                "experts": {},
            }

        return {
            "patient_id": predict_response.get("patient_id", patient_id),
            "active_modalities": active_modalities,
            "missing_modalities": missing_modalities,
            "fusion_pathway_used": pathway_key,
            "disease_risk_outcomes": disease_outcomes,
            "research_disclaimer": config.RESEARCH_DISCLAIMER,
        }

    is_empty_features = not patient_features or all(v is None or not v for v in patient_features.values())
    if is_empty_features and not predict_response:
        return {
            "patient_id": patient_id,
            "active_modalities": [],
            "missing_modalities": ["clinical", "wearable", "gut"],
            "fusion_pathway_used": "NONE",
            "disease_risk_outcomes": {},
            "research_disclaimer": config.RESEARCH_DISCLAIMER,
        }

    if xai_engine is None:
        xai_engine = UnifiedXAIEngine().load()

    raw_xai = xai_engine.generate_patient_xai_payload(patient_features, top_k_drivers=5)

    active_modalities = raw_xai["active_modalities"]
    missing_modalities = raw_xai["missing_modalities"]
    pathway_key = raw_xai["pathway"]

    disease_outcomes = {}

    for disease, d_info in raw_xai["disease_outcomes"].items():
        fusion_prob = d_info["final_fusion_probability"]
        pred = d_info["final_prediction"]
        thresh = d_info["classification_threshold"]

        if pred == 1:
            risk_category = "High Risk / Elevated Signal"
        elif fusion_prob >= 0.35:
            risk_category = "Moderate Risk"
        else:
            risk_category = "Low Risk / Normal Signal"

        expert_drivers = {}
        for mod_key, exp_data in d_info["experts"].items():
            top_drivers = exp_data.get("top_drivers", [])
            formatted_drivers = []

            for rank, dr in enumerate(top_drivers, 1):
                formatted_drivers.append({
                    "importance_rank": rank,
                    "feature": dr["feature"],
                    "value": dr["value"],
                    "model_effect_direction": dr["direction"],
                })

            expert_drivers[mod_key] = {
                "expert_probability": exp_data["probability"],
                "classification_threshold": exp_data["threshold"],
                "top_ranked_drivers": formatted_drivers,
            }

        disease_outcomes[disease] = {
            "disease": disease,
            "risk_category": risk_category,
            "fusion_probability": fusion_prob,
            "prediction": pred,
            "threshold": thresh,
            "experts": expert_drivers,
            "fusion_decision_weights": d_info.get("fusion_decision_weights", {}),
        }

    return {
        "patient_id": patient_id,
        "active_modalities": active_modalities,
        "missing_modalities": missing_modalities,
        "fusion_pathway_used": pathway_key,
        "disease_risk_outcomes": disease_outcomes,
        "research_disclaimer": config.RESEARCH_DISCLAIMER,
    }
