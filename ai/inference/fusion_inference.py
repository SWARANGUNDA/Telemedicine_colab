"""
inference.py — End-to-End Fusion Inference Engine.

Integrates with IMDIE and the 3 frozen ExpertInferenceEngine instances.
Accepts patient feature dictionaries, routes through active experts,
assembles probability vectors, selects the correct pathway meta-learner,
and returns calibrated 5-disease fusion predictions.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

import joblib
import numpy as np

from ai import shims

try:
    from ai.inference.expert_inference import ExpertInferenceEngine
except (ImportError, ValueError):
    from .expert_inference import ExpertInferenceEngine
from ai.config import fusion_config as config
from .adaptive_router import assemble_fusion_input, detect_available_modalities

logger = logging.getLogger("fusion_engine.inference")


class FusionInferenceEngine:
    """End-to-end fusion inference engine for multimodal disease risk prediction."""

    def __init__(self, fusion_version: str = config.FUSION_VERSION):
        self.fusion_version = fusion_version
        archive_fusion_dir = config.BASE_DIR / "archive" / "legacy_models" / "fusion_engine_saved_models" / f"fusion_{fusion_version}"
        self.fusion_dir = archive_fusion_dir if archive_fusion_dir.exists() else (config.SAVED_MODELS_DIR / f"fusion_{fusion_version}")
        self.expert_engines: Dict[str, ExpertInferenceEngine] = {}
        self.pathway_models: Dict[str, Any] = {}
        self.pathway_calibrators: Dict[str, Any] = {}
        self.pathway_thresholds: Dict[str, Dict[str, float]] = {}
        self.pathway_model_types: Dict[str, str] = {}
        self.is_loaded: bool = False

    def load(self) -> "FusionInferenceEngine":
        """Load all frozen fusion artifacts and expert engines."""
        logger.info("Loading FusionInferenceEngine (fusion_%s)", self.fusion_version)

        # Load frozen expert engines
        for mod_key in config.MODALITY_KEYS:
            mod_info = config.MODALITY_EXPERT_MAP[mod_key]
            engine = ExpertInferenceEngine(
                expert_name=mod_info["expert_name"],
                version=mod_info["version"],
            )
            engine.load()
            self.expert_engines[mod_key] = engine

        # Load pathway artifacts
        meta_dir = self.fusion_dir / "meta_learners"
        thresholds_path = self.fusion_dir / "thresholds.json"
        calibrators_path = self.fusion_dir / "calibrators.pkl"
        training_config_path = self.fusion_dir / "training_config.json"

        with open(thresholds_path, "r") as f:
            self.pathway_thresholds = json.load(f)

        self.pathway_calibrators = joblib.load(calibrators_path)

        with open(training_config_path, "r") as f:
            tcfg = json.load(f)
            self.pathway_model_types = tcfg.get("pathway_model_types", {})

        for pathway_key in config.PATHWAY_DEFINITIONS:
            model_path = meta_dir / f"{pathway_key}.joblib"
            if model_path.exists():
                self.pathway_models[pathway_key] = joblib.load(model_path)

        self.is_loaded = True
        logger.info("FusionInferenceEngine loaded successfully.")
        return self

    def predict(
        self,
        patient_features: Dict[str, Optional[Dict[str, Any]]],
    ) -> Dict[str, Dict[str, Union[float, int]]]:
        """Generate fused disease risk predictions from available modality features.

        Args:
            patient_features: Dict mapping modality key ('clinical', 'wearable', 'gut')
                to a feature dictionary (or None if that modality is unavailable).

        Returns:
            Structured prediction dict mapping disease -> {probability, prediction, threshold, pathway}.
        """
        if not self.is_loaded:
            self.load()

        # Step 1: Get expert predictions for available modalities
        expert_outputs: Dict[str, Optional[Dict]] = {}
        for mod_key in config.MODALITY_KEYS:
            features = patient_features.get(mod_key)
            if features is not None and len(features) > 0:
                expert_outputs[mod_key] = self.expert_engines[mod_key].predict(features)
            else:
                expert_outputs[mod_key] = None

        # Step 2: Detect pathway and assemble input
        pathway_key, active_mods = detect_available_modalities(expert_outputs)
        X_fusion = assemble_fusion_input(expert_outputs, active_mods)

        # Step 3: Run pathway meta-learner
        model = self.pathway_models[pathway_key]
        raw_probs = model.predict_proba(X_fusion)

        # Step 4: Calibrate
        calibrator = self.pathway_calibrators[pathway_key]
        calib_probs = calibrator.calibrate(raw_probs)

        # Step 5: Apply thresholds and build output
        thresholds = self.pathway_thresholds[pathway_key]
        results = {}
        for idx, disease in enumerate(config.TARGET_DISEASES):
            prob = round(float(calib_probs[0, idx]), 4)
            t = float(thresholds.get(disease, thresholds.get("Obesity" if disease == "High_Adiposity_Risk" else ("High_Adiposity_Risk" if disease == "Obesity" else disease), config.DEFAULT_THRESHOLD)))
            results[disease] = {
                "probability": prob,
                "prediction": int(prob >= t),
                "threshold": round(t, 4),
                "pathway": pathway_key,
            }

        return results
