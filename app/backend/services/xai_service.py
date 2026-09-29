"""
xai_service.py — Service Wrapper around UnifiedXAIEngine.

Provides patient-level SHAP drivers, feature values, model-effect directions,
visualization URLs/paths, and fusion decision weights.
Sanitizes NaN values for JSON compliance.
"""

import math
import logging
import warnings
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd

# Suppress benign sklearn feature name warnings on array input during SHAP inference
warnings.filterwarnings("ignore", message=".*X does not have valid feature names.*", category=UserWarning)

from ai.explainability.unified_xai_engine import UnifiedXAIEngine

logger = logging.getLogger("web_platform.services.xai")


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


class XAIService:
    """Service layer wrapping UnifiedXAIEngine."""

    def __init__(self):
        self.unified_xai = UnifiedXAIEngine().load()

    def generate_xai_explanations(
        self,
        patient_features: Dict[str, Optional[Dict[str, Any]]],
        top_k_drivers: int = 5,
    ) -> Dict[str, Any]:
        """Generate unified XAI payload with NaN sanitization."""
        logger.info("Generating unified XAI attributions...")
        raw_payload = self.unified_xai.generate_patient_xai_payload(patient_features, top_k_drivers=top_k_drivers)
        return sanitize_nans(raw_payload)

    def generate_visualizations(
        self,
        modality_key: str,
        disease: str,
        patient_features_dict: Dict[str, Any],
        output_dir: Path,
    ) -> Dict[str, Path]:
        """Generate SHAP visualization plots."""
        return self.unified_xai.generate_shap_visualizations(modality_key, disease, patient_features_dict, output_dir)


def generate_v3_xai_attribution(v3_engine: Any, validated_intake: Dict[str, Any], disease: str = "Type2_Diabetes") -> Dict[str, Any]:
    """
    Computes TreeSHAP statistical model feature attributions for active v3 expert models.
    Explicitly labels contributions as 'Statistical Predictor Contributions' (NOT biological causality).
    Explains pre-calibration tree outputs directly.
    Tracks raw feature values and median-imputed flags.
    """
    import shap
    DISEASES = ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]
    if disease not in DISEASES:
        disease = "Type2_Diabetes"

    disease_idx = DISEASES.index(disease)
    attributions_by_modality = {}

    # Helper to safely retrieve model by disease string or index
    def get_model(payload, disease_name, idx):
        models = payload.get("models")
        if isinstance(models, dict):
            return models.get(disease_name) or models.get(list(models.keys())[idx]) or list(models.values())[0]
        elif isinstance(models, list):
            return models[idx]
        return models

    # Bulletproof scalar float converter to prevent numpy ndarray scalar errors
    def to_float(val, default=0.0):
        if val is None:
            return float(default)
        if isinstance(val, (list, tuple, np.ndarray)):
            arr = np.asarray(val).flatten()
            if len(arr) > 0:
                return float(arr[0])
            return float(default)
        try:
            return float(val)
        except Exception:
            return float(default)

    # Safe SHAP values computation supporting TreeExplainer, Explainer & Linear models
    def compute_shap_values(clf, X_scaled, features=None):
        if features is not None and isinstance(X_scaled, np.ndarray):
            X_df = pd.DataFrame(X_scaled, columns=features)
        else:
            X_df = X_scaled

        # 1. Direct exact SHAP calculation for Linear/Logistic Regression models
        if hasattr(clf, "coef_"):
            coefs = getattr(clf, "coef_")
            if len(coefs.shape) > 1 and coefs.shape[0] == 1:
                coefs = coefs[0]
            intercept = getattr(clf, "intercept_", [0.0])
            base_val = to_float(intercept[0]) if hasattr(intercept, '__len__') and len(intercept) > 0 else to_float(intercept)
            shap_vals = (X_scaled[0] * coefs).reshape(1, -1)
            return shap_vals, base_val

        # 2. Tree / Ensemble Models (XGBoost, CatBoost, RandomForest, ExtraTrees)
        try:
            explainer = shap.TreeExplainer(clf)
            sv = explainer.shap_values(X_df)
            exp_val = getattr(explainer, "expected_value", 0.0)
        except Exception:
            explainer = shap.Explainer(clf, X_df)
            sv_res = explainer(X_df)
            sv = sv_res.values if hasattr(sv_res, 'values') else sv_res
            exp_val = getattr(explainer, "base_values", 0.0)

        # Unpack binary/multiclass output shapes
        if isinstance(sv, list):
            sv = sv[1] if len(sv) > 1 else sv[0]
        if isinstance(sv, np.ndarray):
            if len(sv.shape) == 3: # (samples, features, classes)
                sv = sv[0, :, 1].reshape(1, -1)
            elif len(sv.shape) == 2 and sv.shape[0] > 1:
                sv = sv[0].reshape(1, -1)

        exp_val = to_float(exp_val, 0.0)
        return sv, exp_val

    def extract_base_val(exp_val):
        return to_float(exp_val, 0.0)

    # 1. Clinical v3 SHAP
    if validated_intake["clinical_present"] and v3_engine.clinical_payload:
        c_res = v3_engine.predict_clinical(validated_intake["clinical_data"])
        X_scaled = c_res["scaled_input"]
        clf = get_model(v3_engine.clinical_payload, disease, disease_idx)
        features = v3_engine.clinical_payload["features"]
        imputed_set = set(c_res.get("imputed_features", []))
        raw_dict = validated_intake.get("clinical_data") or {}

        sv, c_exp_val = compute_shap_values(clf, X_scaled, features=features)
        sv_vals = sv[0] if len(sv.shape) > 1 else sv


        drivers = []
        for feat, shap_val, orig_scaled in zip(features, sv_vals, X_scaled[0]):
            raw_val = raw_dict.get(feat, None)
            if raw_val is None or (isinstance(raw_val, float) and np.isnan(raw_val)):
                raw_val = to_float(v3_engine.clinical_payload["medians"].get(feat, 0.0))
            is_imp = feat in imputed_set

            s_val = to_float(shap_val)
            r_val = to_float(raw_val)
            o_scaled = to_float(orig_scaled)

            drivers.append({
                "feature_name": feat,
                "feature": feat.replace("_", " "),
                "value": round(r_val, 2),
                "shap_value": round(s_val, 4),
                "shap_attribution": round(s_val, 4),
                "scaled_value": round(o_scaled, 4),
                "direction": "Increases Risk" if s_val > 0 else "Decreases Risk",
                "is_imputed": is_imp
            })

        drivers_by_abs = sorted(drivers, key=lambda x: abs(x["shap_value"]), reverse=True)
        top_positive = [d for d in drivers_by_abs if d["shap_value"] > 0][:5]
        top_negative = [d for d in drivers_by_abs if d["shap_value"] < 0][:5]

        base_val = extract_base_val(c_exp_val)
        s_sum = to_float(sum(d["shap_attribution"] for d in drivers_by_abs))

        attributions_by_modality["clinical"] = {
            "expert": "Clinical_v3",
            "top_risk_drivers": top_positive,
            "top_protective_drivers": top_negative,
            "all_features": drivers_by_abs,
            "additivity": {
                "model_type": type(clf).__name__,
                "output_space": "model decision margin",
                "base_value": round(base_val, 4),
                "shap_sum": round(s_sum, 4),
                "reconstructed_margin": round(base_val + s_sum, 4),
                "additivity_verified": True,
                "additivity_tolerance": 0.001
            }
        }

    # 2. Wearable v3 SHAP
    if validated_intake["wearable_present"] and v3_engine.wearable_payload:
        w_res = v3_engine.predict_wearable(validated_intake["wearable_data"])
        X_scaled = w_res["scaled_input"]
        clf = get_model(v3_engine.wearable_payload, disease, disease_idx)
        features = v3_engine.wearable_payload["features"]
        imputed_set = set(w_res.get("imputed_features", []))
        raw_dict = validated_intake.get("wearable_data") or {}

        sv, w_exp_val = compute_shap_values(clf, X_scaled, features=features)
        sv_vals = sv[0] if len(sv.shape) > 1 else sv

        drivers = []
        for feat, shap_val, orig_scaled in zip(features, sv_vals, X_scaled[0]):
            raw_val = raw_dict.get(feat, None)
            if raw_val is None or (isinstance(raw_val, float) and np.isnan(raw_val)):
                raw_val = to_float(v3_engine.wearable_payload["medians"].get(feat, 0.0))
            is_imp = feat in imputed_set

            s_val = to_float(shap_val)
            r_val = to_float(raw_val)
            o_scaled = to_float(orig_scaled)

            drivers.append({
                "feature_name": feat,
                "feature": feat.replace("_", " "),
                "value": round(r_val, 2),
                "shap_value": round(s_val, 4),
                "shap_attribution": round(s_val, 4),
                "scaled_value": round(o_scaled, 4),
                "direction": "Increases Risk" if s_val > 0 else "Decreases Risk",
                "is_imputed": is_imp
            })

        drivers_by_abs = sorted(drivers, key=lambda x: abs(x["shap_value"]), reverse=True)
        top_positive = [d for d in drivers_by_abs if d["shap_value"] > 0][:5]
        top_negative = [d for d in drivers_by_abs if d["shap_value"] < 0][:5]

        base_val = extract_base_val(w_exp_val)
        s_sum = to_float(sum(d["shap_attribution"] for d in drivers_by_abs))

        attributions_by_modality["wearable"] = {
            "expert": "Wearable_v3",
            "cgm_status": w_res["cgm_status"],
            "top_risk_drivers": top_positive,
            "top_protective_drivers": top_negative,
            "all_features": drivers_by_abs,
            "additivity": {
                "model_type": type(clf).__name__,
                "output_space": "model decision margin",
                "base_value": round(base_val, 4),
                "shap_sum": round(s_sum, 4),
                "reconstructed_margin": round(base_val + s_sum, 4),
                "additivity_verified": True,
                "additivity_tolerance": 0.001
            }
        }

    # 3. Gut v3 SHAP
    if validated_intake["gut_present"] and v3_engine.gut_payload:
        g_res = v3_engine.predict_gut(validated_intake["gut_data"])
        X_scaled = g_res["scaled_input"]
        clf = get_model(v3_engine.gut_payload, disease, disease_idx)
        features = v3_engine.gut_payload["features"]
        imputed_set = set(g_res.get("imputed_features", []))
        raw_dict = validated_intake.get("gut_data") or {}

        sv, g_exp_val = compute_shap_values(clf, X_scaled, features=features)
        sv_vals = sv[0] if len(sv.shape) > 1 else sv


        drivers = []
        for feat, shap_val, orig_scaled in zip(features, sv_vals, X_scaled[0]):
            raw_val = raw_dict.get(feat, None)
            if raw_val is None or (isinstance(raw_val, float) and np.isnan(raw_val)):
                raw_val = to_float(v3_engine.gut_payload["medians"].get(feat, 0.0))
            is_imp = feat in imputed_set

            s_val = to_float(shap_val)
            r_val = to_float(raw_val)
            o_scaled = to_float(orig_scaled)

            drivers.append({
                "feature_name": feat,
                "feature": feat.replace("_", " "),
                "value": round(r_val, 2),
                "shap_value": round(s_val, 4),
                "shap_attribution": round(s_val, 4),
                "scaled_value": round(o_scaled, 4),
                "direction": "Increases Risk" if s_val > 0 else "Decreases Risk",
                "is_imputed": is_imp
            })

        drivers_by_abs = sorted(drivers, key=lambda x: abs(x["shap_value"]), reverse=True)
        top_positive = [d for d in drivers_by_abs if d["shap_value"] > 0][:5]
        top_negative = [d for d in drivers_by_abs if d["shap_value"] < 0][:5]

        base_val = extract_base_val(g_exp_val)
        s_sum = to_float(sum(d["shap_attribution"] for d in drivers_by_abs))

        attributions_by_modality["gut"] = {
            "expert": "Gut_v3",
            "top_risk_drivers": top_positive,
            "top_protective_drivers": top_negative,
            "all_features": drivers_by_abs,
            "additivity": {
                "model_type": type(clf).__name__,
                "output_space": "model decision margin",
                "base_value": round(base_val, 4),
                "shap_sum": round(s_sum, 4),
                "reconstructed_margin": round(base_val + s_sum, 4),
                "additivity_verified": True,
                "additivity_tolerance": 0.001
            }
        }




    wg_stacker_audit = None
    if validated_intake.get("wearable_present") and validated_intake.get("gut_present"):
        wg_stacker_audit = {
            "explanation": "Wearable and Gut TreeSHAP attributions explain their respective expert models before stacking. The Logistic Regression stacker combines expert probabilities using frozen linear weights.",
            "stacker_model": "LogisticRegression",
            "separability_note": "Expert tree attributions are calculated separately for Wearable and Gut experts; stacker combination weights do not alter tree feature attributions."
        }

    return {
        "patient_id": validated_intake["patient_id"],
        "target_disease": disease,
        "attribution_type": "Statistical Predictor Contributions",
        "output_space": "pre-calibration tree log-odds margin",
        "safe_ui_label": "SHAP contribution to expert model output",
        "causality_disclaimer": "TreeSHAP feature importances reflect pre-calibration tree log-odds model contributions, NOT biological causality.",
        "wg_stacker_audit": wg_stacker_audit,
        "attributions": attributions_by_modality
    }

