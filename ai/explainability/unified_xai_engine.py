"""
unified_xai_engine.py — Unified Explainable AI (XAI) & Attribution Layer.

Integrates:
1. Feature-level model attributions (Expert SHAP values: feature, value, shap_value, direction).
2. Reusable visualization utilities (Global bar plots & Patient waterfall plots).
3. Fusion model decision weights (LR coefficient weights / XGBoost feature importances).
4. Structured XAI payload generation for RAG ingestion (Phase 5) and Web UI (Phase 6).
"""

import math
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from ai.config import expert_config, fusion_config
    from ai.training.clinical import data_loader as expert_data_loader
    from ai.training.clinical.artifact_manager import ExpertArtifactManager
    from ai.explainability.expert_explainer import ExpertExplainer
    from ai.inference.expert_inference import ExpertInferenceEngine
    from ai.explainability.fusion_explainer import compute_modality_attribution
    from ai.inference.fusion_inference import FusionInferenceEngine
except (ImportError, ValueError):
    from ..config import expert_config, fusion_config
    from ..training.clinical import data_loader as expert_data_loader
    from ..training.clinical.artifact_manager import ExpertArtifactManager
    from .expert_explainer import ExpertExplainer
    from ..inference.expert_inference import ExpertInferenceEngine
    from .fusion_explainer import compute_modality_attribution
    from ..inference.fusion_inference import FusionInferenceEngine

logger = logging.getLogger("fusion_engine.unified_xai_engine")


class UnifiedXAIEngine:
    """Unified XAI Layer delivering structured attributions across Experts and Fusion."""

    def __init__(self, fusion_version: str = fusion_config.FUSION_VERSION):
        self.fusion_version = fusion_version
        self.fusion_engine = FusionInferenceEngine(fusion_version=fusion_version)
        self.expert_explainers: Dict[str, ExpertExplainer] = {}
        self.expert_artifacts: Dict[str, Dict[str, Any]] = {}
        self.is_loaded: bool = False

    def load(self) -> "UnifiedXAIEngine":
        """Load frozen fusion engine, expert artifacts, and fit SHAP explainers."""
        if not self.fusion_engine.is_loaded:
            self.fusion_engine.load()

        logger.info("Loading SHAP explainers for active expert models...")
        for mod_key in fusion_config.MODALITY_KEYS:
            mod_info = fusion_config.MODALITY_EXPERT_MAP[mod_key]
            mgr = ExpertArtifactManager(mod_info["expert_name"], mod_info["version"])
            artifacts = mgr.load_artifacts()
            self.expert_artifacts[mod_key] = artifacts

            model = artifacts["model"]
            approved = artifacts["feature_order"]

            # Load background sample for SHAP initialization
            X, _, splits, _ = expert_data_loader.load_dataset_for_expert(
                Path(mod_info["dataset_path"]), mod_info["schema_file"]
            )
            X_train_sub = X[splits == "train"][approved][:100]
            X_train_prep = artifacts["preprocessor"].transform(X_train_sub)

            explainer = ExpertExplainer(model.estimators, approved)
            explainer.fit_explainers(X_train_prep)
            self.expert_explainers[mod_key] = explainer

        self.is_loaded = True
        logger.info("UnifiedXAIEngine fully loaded and initialized.")
        return self

    def generate_patient_xai_payload(
        self,
        patient_features: Dict[str, Optional[Dict[str, Any]]],
        top_k_drivers: int = 5,
    ) -> Dict[str, Any]:
        """Generate structured patient-level XAI payload for all 5 diseases.

        Args:
            patient_features: Dict mapping modality ('clinical', 'wearable', 'gut')
                to feature dictionary (or None if missing).
            top_k_drivers: Number of top driving SHAP features to return per expert.

        Returns:
            Structured dictionary matching Phase 5 RAG contract schema.
        """
        if not self.is_loaded:
            self.load()

        # Step 1: Run Fusion Inference
        fusion_preds = self.fusion_engine.predict(patient_features)

        # Detect active & missing modalities
        active_modalities = [
            m for m in fusion_config.MODALITY_KEYS
            if patient_features.get(m) is not None and len(patient_features[m]) > 0
        ]
        missing_modalities = [m for m in fusion_config.MODALITY_KEYS if m not in active_modalities]

        pathway_key = fusion_preds[fusion_config.TARGET_DISEASES[0]]["pathway"]
        meta_learner = self.fusion_engine.pathway_models[pathway_key]
        model_type = self.fusion_engine.pathway_model_types[pathway_key]

        # Step 2: Get Fusion Decision Weights for active pathway
        fusion_weights_all = compute_modality_attribution(meta_learner, model_type, pathway_key)

        # Step 3: Compute Expert Patient-Level SHAP Attributions for active modalities
        expert_shap_results: Dict[str, Dict[str, Any]] = {}

        for mod_key in active_modalities:
            art = self.expert_artifacts[mod_key]
            explainer = self.expert_explainers[mod_key]
            features_dict = patient_features[mod_key]

            # Convert feature dict to dataframe in exact approved feature order
            df_input = pd.DataFrame([features_dict]).reindex(columns=art["feature_order"])
            X_prep = art["preprocessor"].transform(df_input)

            shap_out = explainer.explain_patient_prediction(X_prep, top_k=top_k_drivers)
            expert_shap_results[mod_key] = shap_out

        # Step 4: Assemble RAG Contract Payload
        diseases_xai = {}
        for disease in fusion_config.TARGET_DISEASES:
            fusion_d = fusion_preds[disease]

            disease_experts = {}
            for mod_key in active_modalities:
                exp_name = fusion_config.MODALITY_EXPERT_MAP[mod_key]["expert_name"]
                exp_pred = self.fusion_engine.expert_engines[exp_name].predict(patient_features[mod_key])[disease]
                raw_drivers = expert_shap_results[mod_key][disease].get("top_risk_drivers", [])

                formatted_drivers = []
                for d in raw_drivers:
                    s_val = d["shap_attribution"]
                    feat_val = d["feature_value"]
                    if feat_val is None or (isinstance(feat_val, float) and (math.isnan(feat_val) or math.isinf(feat_val))) or str(feat_val).lower() in ["nan", "none", "null", ""]:
                        val_display = "Not provided (missing-value model influence)"
                        is_missing = True
                    else:
                        val_display = feat_val
                        is_missing = False

                    formatted_drivers.append({
                        "feature": d["feature"],
                        "value": val_display,
                        "shap_attribution": s_val,
                        "direction": "increases_model_output" if s_val > 0 else "decreases_model_output",
                        "is_missing_value_influence": is_missing,
                    })

                disease_experts[mod_key] = {
                    "probability": exp_pred["probability"],
                    "prediction": exp_pred["prediction"],
                    "threshold": exp_pred["threshold"],
                    "top_drivers": formatted_drivers,
                }

            # Filter decision weights to active modalities
            raw_weights = fusion_weights_all.get(disease, {})
            active_weights = {}
            for mod_key in active_modalities:
                exp_name = fusion_config.MODALITY_EXPERT_MAP[mod_key]["expert_name"]
                for k, v in raw_weights.items():
                    if mod_key in k.lower() or exp_name.lower() in k.lower():
                        active_weights[mod_key] = v
            if not active_weights:
                active_weights = raw_weights

            diseases_xai[disease] = {
                "disease": disease,
                "final_fusion_probability": fusion_d["probability"],
                "final_prediction": fusion_d["prediction"],
                "classification_threshold": fusion_d["threshold"],
                "pathway": pathway_key,
                "experts": disease_experts,
                "fusion_decision_weights": active_weights,
                "weight_attribution_type": "LR_Decision_Weights" if model_type == "logistic_regression" else "XGB_Feature_Importances",
                "missing_modalities": missing_modalities,
            }

        return {
            "pathway": pathway_key,
            "active_modalities": active_modalities,
            "missing_modalities": missing_modalities,
            "disease_outcomes": diseases_xai,
            "disclaimer": (
                "Feature-level attributions use SHAP TreeExplainer. Fusion decision weights reflect "
                "meta-learner boundary weights. Predictions and explanations do NOT constitute clinical diagnoses."
            ),
        }

    def generate_shap_visualizations(
        self,
        modality_key: str,
        disease: str,
        patient_features_dict: Dict[str, Any],
        output_dir: Path,
    ) -> Dict[str, Path]:
        """Generate reusable Global Bar plot and Patient-Level Waterfall plot PNGs.

        Args:
            modality_key: 'clinical', 'wearable', or 'gut'.
            disease: Target disease string.
            patient_features_dict: Single patient raw feature dictionary.
            output_dir: Directory to save generated plot PNGs.

        Returns:
            Dict with paths to 'global_plot' and 'waterfall_plot'.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        art = self.expert_artifacts[modality_key]
        explainer = self.expert_explainers[modality_key].explainers[disease]
        approved = art["feature_order"]

        df_input = pd.DataFrame([patient_features_dict]).reindex(columns=approved)
        X_prep = art["preprocessor"].transform(df_input)

        # Compute SHAP values
        shap_vals = explainer.shap_values(X_prep)
        if isinstance(shap_vals, list):
            shap_vals = shap_vals[1]

        # 1. Generate Patient Bar/Waterfall Plot
        fig, ax = plt.subplots(figsize=(8, 4))
        values = shap_vals[0]
        sorted_indices = np.argsort(np.abs(values))[-8:]  # Top 8
        top_names = [approved[i] for i in sorted_indices]
        top_vals = values[sorted_indices]
        colors = ["#e74c3c" if v > 0 else "#2ecc71" for v in top_vals]

        ax.barh(top_names, top_vals, color=colors)
        ax.axvline(0, color="black", linestyle="--", alpha=0.6)
        ax.set_xlabel("SHAP Feature Attribution (Impact on Model Output)")
        ax.set_title(f"{modality_key.upper()} Expert — SHAP Drivers for {disease}")
        plt.tight_layout()

        waterfall_path = output_dir / f"{modality_key}_{disease}_patient_shap.png"
        plt.savefig(waterfall_path, dpi=150)
        plt.close()

        return {
            "patient_plot": waterfall_path,
        }
