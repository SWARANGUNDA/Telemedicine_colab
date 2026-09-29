"""
prediction_orchestrator.py — Central Prediction Orchestrator & Explainability Layer (Phase 2).

Manages end-to-end prediction workflow tracking, model contribution summaries,
missing feature impact analyses, prediction audit logging, and clinical consistency checks.

Strict Guardrail: Does NOT modify disease probabilities, ML model weights, SHAP values, or RAG outputs.
"""

import datetime
import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("imdie.prediction_orchestrator")

MODEL_VERSION = "3.3.0-v3_unified_orchestrator"


class StageTimer:
    """Context manager for tracking stage execution times in milliseconds."""

    def __init__(self):
        self.stage_durations: Dict[str, float] = {}
        self._start_times: Dict[str, float] = {}

    def start_stage(self, stage_name: str):
        self._start_times[stage_name] = time.perf_counter()

    def stop_stage(self, stage_name: str):
        if stage_name in self._start_times:
            elapsed_ms = round((time.perf_counter() - self._start_times[stage_name]) * 1000.0, 2)
            self.stage_durations[stage_name] = elapsed_ms


class PredictionOrchestrator:
    """Central Prediction Workflow Orchestrator & Explainability Tracker."""

    def __init__(self):
        self.timer = StageTimer()

    def compute_model_contributions(self, effective_pathway: str) -> Dict[str, float]:
        """Compute relative percentage model contributions based on active scientific pathway.

        Args:
            effective_pathway: Active prediction pathway (e.g. 'C', 'W', 'G', 'C+W', 'C+W+G').

        Returns:
            Dict containing relative model contribution percentages (must sum to 100%).
        """
        path = (effective_pathway or "C+W+G").upper()

        if path == "C":
            return {"Clinical_Expert_v3": 100.0, "Wearable_Expert_v3": 0.0, "Gut_Expert_v3": 0.0, "Fusion_Engine": 0.0}
        elif path == "W":
            return {"Clinical_Expert_v3": 0.0, "Wearable_Expert_v3": 100.0, "Gut_Expert_v3": 0.0, "Fusion_Engine": 0.0}
        elif path == "G":
            return {"Clinical_Expert_v3": 0.0, "Wearable_Expert_v3": 0.0, "Gut_Expert_v3": 100.0, "Fusion_Engine": 0.0}
        elif path == "C+W":
            return {"Clinical_Expert_v3": 80.0, "Wearable_Expert_v3": 20.0, "Gut_Expert_v3": 0.0, "Fusion_Engine": 0.0}
        elif path == "C+G":
            return {"Clinical_Expert_v3": 80.0, "Wearable_Expert_v3": 0.0, "Gut_Expert_v3": 20.0, "Fusion_Engine": 0.0}
        elif path == "W+G":
            return {"Clinical_Expert_v3": 0.0, "Wearable_Expert_v3": 45.0, "Gut_Expert_v3": 40.0, "Fusion_Engine": 15.0}
        else:  # C+W+G
            return {"Clinical_Expert_v3": 70.0, "Wearable_Expert_v3": 15.0, "Gut_Expert_v3": 15.0, "Fusion_Engine": 0.0}

    def analyze_missing_feature_impacts(
        self,
        missing_features: List[str]
    ) -> Dict[str, Any]:
        """Analyze affected disease models and estimate confidence reduction for missing features."""
        disease_map = {
            "HbA1c": ["Type2_Diabetes", "Prediabetes", "Metabolic_Syndrome"],
            "Fasting_Blood_Glucose": ["Type2_Diabetes", "Prediabetes", "Metabolic_Syndrome"],
            "Systolic_BP": ["Hypertension", "Metabolic_Syndrome"],
            "Diastolic_BP": ["Hypertension", "Metabolic_Syndrome"],
            "LDL": ["Metabolic_Syndrome", "NAFLD"],
            "HDL": ["Metabolic_Syndrome", "NAFLD"],
            "Triglycerides": ["Metabolic_Syndrome", "NAFLD"],
            "ALT": ["NAFLD"],
            "AST": ["NAFLD"],
            "Average_Daily_Steps": ["High_Adiposity_Risk", "Metabolic_Syndrome"],
            "Resting_Heart_Rate": ["Metabolic_Syndrome"],
            "Akkermansia": ["Metabolic_Syndrome", "NAFLD"]
        }

        affected_diseases = set()
        impact_details = []

        for feat in missing_features:
            diseases = disease_map.get(feat, ["General_Health"])
            affected_diseases.update(diseases)
            impact_details.append({
                "missing_feature": feat,
                "affected_diseases": diseases,
                "confidence_reduction_pct": 5.0 if feat in ["HbA1c", "Fasting_Blood_Glucose", "Systolic_BP"] else 2.5,
                "recommendation": f"Upload recent lab test report containing '{feat}' to boost prediction confidence."
            })

        return {
            "total_missing_count": len(missing_features),
            "affected_diseases": sorted(list(affected_diseases)),
            "estimated_total_confidence_reduction_pct": min(40.0, len(missing_features) * 3.5),
            "impact_details": impact_details
        }

    def validate_consistency(
        self,
        patient_profile: Dict[str, Any],
        effective_pathway: str,
        predictions: Optional[Dict[str, Any]] = None,
        shap_available: bool = True,
        rag_available: bool = True
    ) -> List[Dict[str, Any]]:
        """Verify workflow, pathway, SHAP/RAG availability, and prediction consistency."""
        warnings: List[Dict[str, Any]] = []

        # 1. Pathway consistency check
        clin_present = bool(patient_profile.get("clinical_features"))
        wear_present = bool(patient_profile.get("wearable_features"))
        gut_present = bool(patient_profile.get("gut_features"))

        expected_pathway = f"C{'+W' if wear_present else ''}{'+G' if gut_present else ''}"
        if not clin_present:
            if wear_present and gut_present:
                expected_pathway = "W+G"
            elif wear_present:
                expected_pathway = "W"
            elif gut_present:
                expected_pathway = "G"

        if effective_pathway != expected_pathway:
            warnings.append({
                "type": "PATHWAY_MISMATCH",
                "message": f"Effective pathway '{effective_pathway}' differs from expected modality mask pathway '{expected_pathway}'."
            })

        # 2. SHAP & RAG availability check
        if not shap_available:
            warnings.append({"type": "SHAP_UNAVAILABLE", "message": "SHAP tree explainability engine unavailable; falling back to feature importance rankings."})
        if not rag_available:
            warnings.append({"type": "RAG_UNAVAILABLE", "message": "Medical RAG vector knowledge base unavailable; falling back to static clinical guidelines."})

        # 3. Probability integrity check
        if predictions:
            pred_dict = predictions.get("predictions", predictions)
            for d_name, d_val in pred_dict.items():
                if isinstance(d_val, dict):
                    prob = d_val.get("probability", d_val.get("risk_score"))
                    if prob is not None and (prob < 0.0 or prob > 1.0):
                        warnings.append({
                            "type": "PROBABILITY_OUT_OF_BOUNDS",
                            "message": f"Probability for disease '{d_name}' ({prob}) is outside valid [0, 1] range."
                        })

        return warnings

    def build_orchestration_metadata(
        self,
        patient_profile: Dict[str, Any],
        quality_scores: Dict[str, Any],
        effective_pathway: str,
        predictions: Optional[Dict[str, Any]] = None,
        shap_available: bool = True,
        rag_available: bool = True,
        stage_durations: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Build structured orchestration and explainability metadata payload."""
        stage_durations = stage_durations or self.timer.stage_durations

        contributions = self.compute_model_contributions(effective_pathway)

        clin_feats = patient_profile.get("clinical_features", {}) or {}
        wear_feats = patient_profile.get("wearable_features", {}) or {}
        gut_feats = patient_profile.get("gut_features", {}) or {}

        missing_critical = quality_scores.get("score_breakdown", {}).get("missing_features", [])
        if not missing_critical:
            all_known = ["HbA1c", "Fasting_Blood_Glucose", "Systolic_BP", "Diastolic_BP", "LDL", "HDL", "Triglycerides", "ALT", "AST"]
            missing_critical = [k for k in all_known if k not in clin_feats]

        missing_impacts = self.analyze_missing_feature_impacts(missing_critical)
        warnings = self.validate_consistency(patient_profile, effective_pathway, predictions, shap_available, rag_available)

        all_provided_keys = list(clin_feats.keys()) + list(wear_feats.keys()) + list(gut_feats.keys())

        fusion_rel = "High" if "W+G" in effective_pathway or "C+W+G" in effective_pathway else ("N/A (Single Modality)" if len(effective_pathway) == 1 else "Medium")

        audit_log = {
            "input_summary": {
                "provided_feature_count": len([k for k in all_provided_keys if k not in ("Patient_ID", "Gender")]),
                "clinical_count": len([k for k in clin_feats.keys() if k not in ("Patient_ID", "Gender")]),
                "wearable_count": len(wear_feats),
                "gut_count": len(gut_feats)
            },
            "validation_summary": {
                "quality_score": quality_scores.get("overall_quality_score", 70.0),
                "verify_flags_count": len(quality_scores.get("verify_flags", {}))
            },
            "active_pathway": effective_pathway,
            "active_experts": list(contributions.keys()),
            "reliability_summary": {
                "overall_confidence": quality_scores.get("overall_quality_score", 70.0),
                "fusion_reliability": fusion_rel
            },
            "shap_availability": "AVAILABLE" if shap_available else "UNAVAILABLE",
            "rag_availability": "AVAILABLE" if rag_available else "UNAVAILABLE",
            "final_prediction_metadata": {
                "model_version": MODEL_VERSION,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        }

        return {
            "pipeline_execution_metadata": {
                "pipeline_version": "v3.3",
                "model_version": MODEL_VERSION,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "active_pathway": effective_pathway,
                "active_models": list(contributions.keys()),
                "feature_counts_per_modality": {
                    "clinical_count": len([k for k in clin_feats.keys() if k not in ("Patient_ID", "Gender")]),
                    "wearable_count": len(wear_feats),
                    "gut_count": len(gut_feats)
                },
                "missing_features": missing_critical,
                "data_quality_score": quality_scores.get("overall_quality_score", 70.0),
                "stage_durations_ms": stage_durations,
                "total_pipeline_latency_ms": round(sum(stage_durations.values()), 2)
            },
            "model_contributions": contributions,
            "missing_feature_impact_analysis": missing_impacts,
            "prediction_audit_log": audit_log,
            "consistency_warnings": warnings,
            "fusion_reliability": fusion_rel,
            "system_availability": {
                "shap_engine": "AVAILABLE" if shap_available else "UNAVAILABLE",
                "rag_engine": "AVAILABLE" if rag_available else "UNAVAILABLE"
            }
        }
