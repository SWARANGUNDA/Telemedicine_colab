"""
inference.py — Unified Inference Layer for Expert Models.

Independent from training code.
Provides a stable, unified interface for IMDIE and downstream Fusion Engine:
- Loads frozen expert artifacts via artifact_manager
- Validates incoming IMDIE feature payload against saved schema
- Enforces saved feature ordering
- Applies saved preprocessing
- Generates 5 raw disease probabilities
- Applies saved probability calibration
- Applies validation-tuned disease thresholds
- Returns structured prediction dictionary

Conceptual Output Format:
{
  "Type2_Diabetes": {"probability": 0.82, "prediction": 1, "threshold": 0.52},
  "Prediabetes": {"probability": 0.12, "prediction": 0, "threshold": 0.48},
  "Obesity": {"probability": 0.76, "prediction": 1, "threshold": 0.50},
  "Metabolic_Syndrome": {"probability": 0.68, "prediction": 1, "threshold": 0.45},
  "NAFLD": {"probability": 0.51, "prediction": 1, "threshold": 0.40}
}
"""

import logging
from typing import Any, Dict, Union
import numpy as np
import pandas as pd

from ai import shims

from ai.config import expert_config as config
from ai.training.clinical.artifact_manager import ExpertArtifactManager

logger = logging.getLogger("expert_models.inference")


class ExpertInferenceEngine:
    """Unified inference engine for a frozen expert model version."""

    def __init__(self, expert_name: str, version: str = config.EXPERT_VERSION):
        self.expert_name = expert_name
        self.version = version
        self.manager = ExpertArtifactManager(expert_name=expert_name, version=version)
        self.artifacts: Dict[str, Any] = {}
        self.is_loaded: bool = False

    def load(self) -> "ExpertInferenceEngine":
        """Load frozen artifacts from disk."""
        logger.info("Loading frozen expert inference artifacts for '%s_%s'", self.expert_name, self.version)
        self.artifacts = self.manager.load_artifacts()
        self.is_loaded = True
        return self

    def predict(
        self,
        features_input: Union[Dict[str, Any], pd.DataFrame]
    ) -> Dict[str, Dict[str, Union[float, int]]]:
        """Generate calibrated predictions and thresholded labels for all 5 target diseases.

        Args:
            features_input: Dictionary of features from IMDIE or 1-row DataFrame.

        Returns:
            Structured prediction dict mapping disease name ➔ {probability, prediction, threshold}.
        """
        if not self.is_loaded:
            self.load()

        feature_order = self.artifacts["feature_order"]
        model = self.artifacts["model"]
        preprocessor = self.artifacts["preprocessor"]
        calibrator = self.artifacts["calibrator"]
        thresholds = self.artifacts["thresholds"]

        # Convert dictionary to 1-row DataFrame
        if isinstance(features_input, dict):
            df_in = pd.DataFrame([features_input])
        else:
            df_in = features_input.copy()

        # Enforce missing columns with NaN
        for col in feature_order:
            if col not in df_in.columns:
                df_in[col] = np.nan

        # Enforce exact feature ordering
        df_ordered = df_in[feature_order].copy()

        # Preprocess features
        if preprocessor is not None:
            X_prep = preprocessor.transform(df_ordered)
        else:
            X_prep = df_ordered.values.astype(np.float64)

        # Generate raw probabilities
        if hasattr(model, "predict_proba"):
            raw_probs = model.predict_proba(X_prep)
        else:
            raise RuntimeError("Loaded model estimator does not support predict_proba")

        # Handle 1D or 2D array output
        if raw_probs.ndim == 1:
            raw_probs = raw_probs.reshape(1, -1)

        # Apply calibration if available
        if calibrator is not None:
            calibrated_probs = calibrator.calibrate_probas(raw_probs)
        else:
            calibrated_probs = raw_probs

        # Format structured output
        results: Dict[str, Dict[str, Union[float, int]]] = {}
        sample_idx = 0  # Single patient inference

        for idx, disease in enumerate(config.TARGET_DISEASES):
            prob = round(float(calibrated_probs[sample_idx, idx]), 4)
            t = float(thresholds.get(disease, thresholds.get("Obesity" if disease == "High_Adiposity_Risk" else ("High_Adiposity_Risk" if disease == "Obesity" else disease), config.DEFAULT_THRESHOLD)))
            pred = int(prob >= t)

            results[disease] = {
                "probability": prob,
                "prediction": pred,
                "threshold": round(t, 4)
            }

        return results
