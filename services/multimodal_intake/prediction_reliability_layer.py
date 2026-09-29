"""
prediction_reliability_layer.py — Prediction Confidence & Reliability Evaluator Layer (Phase 2).

Wraps prediction outputs with non-intrusive metadata evaluating:
1. Overall, Modality-level, and Feature-level Confidence Scores
2. Modality Reliability Ratings (Clinical, Wearables, Gut)
3. Missing Feature Impact Analysis
4. Clinical Consistency Validation (contradiction warnings)
5. Structured Prediction Audit Trail

Strict Guardrail: Does NOT modify disease probabilities, ML models, SHAP values, or RAG outputs.
"""

import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("imdie.prediction_reliability")

MODEL_VERSION = "3.2.0-v3_unified"


class PredictionReliabilityLayer:
    """Intelligent Multimodal Prediction Reliability Engine."""

    def __init__(self):
        pass

    def evaluate_reliability(
        self,
        patient_profile: Dict[str, Any],
        quality_scores: Dict[str, Any],
        prediction_output: Optional[Dict[str, Any]] = None,
        effective_pathway: str = "C+W+G"
    ) -> Dict[str, Any]:
        """Compute structured reliability report metadata.

        Args:
            patient_profile: Dict containing clinical_features, wearable_features, gut_features.
            quality_scores: Dict containing data quality metrics and score breakdowns.
            prediction_output: Dict containing disease predictions/probabilities (unmodified).
            effective_pathway: Active prediction pathway string (e.g. 'C', 'W', 'G', 'C+W', 'C+W+G').

        Returns:
            Structured JSON payload containing reliability metadata.
        """
        clin_feats = patient_profile.get("clinical_features", {}) or {}
        wear_feats = patient_profile.get("wearable_features", {}) or {}
        gut_feats = patient_profile.get("gut_features", {}) or {}

        # 1. Modality Completeness & Reliability Assessment
        clin_rel = self._assess_modality_reliability("CLINICAL", clin_feats, ["HbA1c", "Fasting_Blood_Glucose", "Systolic_BP", "LDL", "ALT"])
        wear_rel = self._assess_modality_reliability("WEARABLE", wear_feats, ["Average_Daily_Steps", "Active_Minutes", "Resting_Heart_Rate", "Sleep_Duration"])
        gut_rel = self._assess_modality_reliability("GUT_MICROBIOME", gut_feats, ["Akkermansia", "Faecalibacterium", "Bifidobacterium", "Roseburia"])

        # 2. Overall Prediction Confidence Calculation
        overall_q = float(quality_scores.get("overall_quality_score", quality_scores.get("overall_score", 70.0)))
        pathway_mod_count = len(effective_pathway.split("+")) if effective_pathway else 1
        modality_weight = min(1.0, pathway_mod_count / 3.0)

        # Multi-factor prediction confidence score (0.0 to 100.0)
        overall_conf = round(0.50 * overall_q + 0.30 * (modality_weight * 100.0) + 0.20 * clin_rel["completeness_pct"], 1)

        conf_grade = "High" if overall_conf >= 82.0 else ("Medium" if overall_conf >= 60.0 else "Low")

        # 3. Missing Feature Impact Analysis
        missing_impacts = self._analyze_missing_feature_impacts(clin_feats, wear_feats, gut_feats)

        # 4. Consistency Validation (Contradiction Check)
        consistency_warnings = self._validate_prediction_consistency(clin_feats, prediction_output)

        # 5. Feature-Level Confidence Mapping
        feature_confidences = self._build_feature_confidence_map(clin_feats, wear_feats, gut_feats)

        # 6. Structured Audit Trail
        all_provided_keys = list(clin_feats.keys()) + list(wear_feats.keys()) + list(gut_feats.keys())
        audit_trail = {
            "prediction_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "model_version": MODEL_VERSION,
            "active_pathway": effective_pathway,
            "active_models": [f"Expert_{m}" for m in effective_pathway.split("+")],
            "features_used": [k for k in all_provided_keys if k not in ("Patient_ID", "Gender")],
            "features_ignored": quality_scores.get("score_breakdown", {}).get("unmapped_keys", []),
            "missing_critical_features": missing_impacts["missing_critical"],
            "overall_confidence_score": overall_conf,
            "confidence_grade": conf_grade
        }

        return {
            "overall_confidence": overall_conf,
            "confidence_grade": conf_grade,
            "modality_reliability": {
                "clinical": clin_rel,
                "wearable": wear_rel,
                "gut": gut_rel
            },
            "missing_feature_impact_analysis": missing_impacts,
            "consistency_warnings": consistency_warnings,
            "feature_confidences": feature_confidences,
            "prediction_audit_trail": audit_trail,
            "prediction_limitations": self._generate_limitations_summary(clin_rel, wear_rel, gut_rel, missing_impacts)
        }

    def _assess_modality_reliability(
        self,
        modality_name: str,
        features: Dict[str, Any],
        mandatory_keys: List[str]
    ) -> Dict[str, Any]:
        """Evaluate a single modality's completeness and reliability."""
        if not features:
            return {
                "status": "UNAVAILABLE",
                "completeness_pct": 0.0,
                "reliability_rating": "None",
                "provided_count": 0,
                "missing_mandatory": mandatory_keys
            }

        present_keys = [k for k in features.keys() if k not in ("Patient_ID", "Gender")]
        missing_mand = [k for k in mandatory_keys if k not in features]

        mand_present = len(mandatory_keys) - len(missing_mand)
        comp_pct = round((mand_present / len(mandatory_keys)) * 100.0, 1)

        rating = "High" if comp_pct >= 80.0 else ("Medium" if comp_pct >= 40.0 else "Low")
        status = "COMPLETE" if comp_pct >= 80.0 else "PARTIAL"

        return {
            "status": status,
            "completeness_pct": comp_pct,
            "reliability_rating": rating,
            "provided_count": len(present_keys),
            "missing_mandatory": missing_mand
        }

    def _analyze_missing_feature_impacts(
        self,
        clin: Dict[str, Any],
        wear: Dict[str, Any],
        gut: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify missing biomarkers and compute impact on prediction confidence."""
        missing_critical = []
        impact_details = []

        critical_biomarkers = [
            ("HbA1c", "Clinical", "Essential for Diabetes diagnostic subtyping"),
            ("Fasting_Blood_Glucose", "Clinical", "Key marker for metabolic glycemia assessment"),
            ("Systolic_BP", "Clinical", "Primary indicator for Hypertension risk evaluation"),
            ("LDL", "Clinical", "Core biomarker for Lipid & Cardiovascular risk estimation"),
            ("ALT", "Clinical", "Essential liver enzyme for Liver Health screening"),
            ("Average_Daily_Steps", "Wearable", "Primary metric for physical activity & metabolic risk"),
            ("Resting_Heart_Rate", "Wearable", "Key telemetry marker for autonomic cardiovascular risk"),
            ("Akkermansia", "Gut", "Key anti-inflammatory gut bacterium for metabolic homeostasis")
        ]

        for b_name, b_mod, rationale in critical_biomarkers:
            target_dict = clin if b_mod == "Clinical" else (wear if b_mod == "Wearable" else gut)
            if b_name not in target_dict:
                missing_critical.append(b_name)
                impact_details.append({
                    "feature": b_name,
                    "modality": b_mod,
                    "impact": f"Missing {b_name} reduces {b_mod} confidence grade.",
                    "rationale": rationale
                })

        return {
            "missing_critical_count": len(missing_critical),
            "missing_critical": missing_critical,
            "impact_details": impact_details,
            "summary_explanation": f"{len(missing_critical)} critical biomarker(s) missing; median imputation applied downstream without altering predictions."
        }

    def _validate_prediction_consistency(
        self,
        clin_feats: Dict[str, Any],
        prediction_output: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect internal contradictions between clinical features and predicted disease risks."""
        warnings: List[Dict[str, Any]] = []
        if not prediction_output or "predictions" not in prediction_output:
            return warnings

        preds = prediction_output.get("predictions", {})

        # Extract values
        hba1c = self._extract_num(clin_feats.get("HbA1c"))
        fbg = self._extract_num(clin_feats.get("Fasting_Blood_Glucose"))
        sbp = self._extract_num(clin_feats.get("Systolic_BP"))

        t2d_prob = preds.get("Type2_Diabetes", {}).get("calibrated_probability") or preds.get("Type2_Diabetes", {}).get("probability") or preds.get("Diabetes", {}).get("probability") or preds.get("Diabetes", {}).get("risk_score")
        metsyn_prob = preds.get("Metabolic_Syndrome", {}).get("calibrated_probability") or preds.get("Metabolic_Syndrome", {}).get("probability") or preds.get("Hypertension", {}).get("probability") or preds.get("Hypertension", {}).get("risk_score")

        # 1. Diabetes Contradiction: Normal HbA1c < 5.7% & FBG < 100 mg/dL but predicted risk > 85%
        if hba1c is not None and fbg is not None and t2d_prob is not None:
            if hba1c < 5.7 and fbg < 100.0 and float(t2d_prob) > 0.85:
                warnings.append({
                    "disease": "Type2_Diabetes",
                    "type": "CLINICAL_CONTRADICTION",
                    "message": f"Contradiction: HbA1c ({hba1c}%) and Fasting Glucose ({fbg} mg/dL) are in normal range, but predicted Type 2 Diabetes risk is high ({round(float(t2d_prob)*100, 1)}%). Verify inputs."
                })

        # 2. Blood Pressure / Metabolic Syndrome Contradiction: Normal BP < 120 mmHg but predicted risk > 85%
        if sbp is not None and metsyn_prob is not None:
            if sbp < 120.0 and float(metsyn_prob) > 0.85:
                warnings.append({
                    "disease": "Metabolic_Syndrome",
                    "type": "CLINICAL_CONTRADICTION",
                    "message": f"Contradiction: Systolic BP ({sbp} mmHg) is in normal range, but predicted Metabolic Syndrome risk is high ({round(float(metsyn_prob)*100, 1)}%). Verify inputs."
                })

        return warnings

    def _build_feature_confidence_map(
        self,
        clin: Dict[str, Any],
        wear: Dict[str, Any],
        gut: Dict[str, Any]
    ) -> Dict[str, float]:
        """Build feature-level extraction confidence lookup dictionary."""
        conf_map = {}
        for mod_dict in [clin, wear, gut]:
            for k, v in mod_dict.items():
                if k in ("Patient_ID", "Gender"):
                    continue
                conf = 0.90
                if isinstance(v, dict):
                    conf = float(v.get("extraction_confidence", v.get("confidence", 0.90)))
                conf_map[k] = round(conf, 3)
        return conf_map

    def _generate_limitations_summary(self, clin_rel, wear_rel, gut_rel, missing_impacts) -> List[str]:
        """Generate human-readable prediction limitations summary."""
        limitations = []
        if clin_rel["status"] != "COMPLETE":
            limitations.append("Clinical data is incomplete; key lab biomarkers rely on median imputation.")
        if wear_rel["status"] == "UNAVAILABLE":
            limitations.append("Wearable telemetry data unavailable; physiological activity dynamics excluded.")
        if gut_rel["status"] == "UNAVAILABLE":
            limitations.append("Gut microbiome data unavailable; microbial dysbiosis signals excluded.")
        if missing_impacts["missing_critical_count"] > 0:
            limitations.append(f"{missing_impacts['missing_critical_count']} critical biomarker(s) missing from input data.")
        if not limitations:
            limitations.append("Full multimodal data provided across Clinical, Wearable, and Gut modalities.")
        return limitations

    def _extract_num(self, val_item: Any) -> Optional[float]:
        """Safely extract float from raw or dict item."""
        if val_item is None:
            return None
        if isinstance(val_item, dict):
            val_item = val_item.get("raw_value", val_item.get("value"))
        try:
            return float(val_item)
        except (ValueError, TypeError):
            return None
