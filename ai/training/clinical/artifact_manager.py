"""
artifact_manager.py — Centralized Artifact Manager for Expert Models.

Manages saving and reproducible loading of frozen expert artifacts:
- model/ (Estimator binaries)
- preprocessor.pkl (Fitted leakage-safe preprocessor)
- calibrator.pkl (Probability calibrator)
- thresholds.json (Validation-tuned classification thresholds)
- feature_schema.json (Approved predictor schema)
- feature_order.json (Enforced feature ordering)
- metrics.json (Multi-label validation & test metrics)
- training_config.json (Hyperparameters & seed)
- metadata.json (Version, timestamp, model summary)
"""

import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib

from ai.config import expert_config as config

logger = logging.getLogger("expert_models.artifact_manager")


class ExpertArtifactManager:
    """Manages serialization and deserialization of frozen expert model artifacts."""

    def __init__(self, expert_name: str, version: str = config.EXPERT_VERSION):
        self.expert_name = expert_name
        self.version = version
        archive_dir = config.BASE_DIR / "archive" / "legacy_models" / "expert_models_saved_models" / f"{expert_name}_{version}"
        active_dir = config.SAVED_MODELS_DIR / expert_name
        self.artifact_dir = archive_dir if archive_dir.exists() else active_dir

    def save_artifacts(
        self,
        model: Any,
        preprocessor: Any,
        calibrator: Any,
        thresholds: Dict[str, float],
        feature_schema: Dict[str, Any],
        feature_order: List[str],
        metrics: Dict[str, Any],
        training_config: Dict[str, Any]
    ) -> Path:
        """Save all frozen artifacts for an expert model version.

        Args:
            model: Trained model estimator or dictionary of per-disease estimators.
            preprocessor: Fitted ExpertPreprocessor object.
            calibrator: Fitted probability calibrator object/dict.
            thresholds: Dict of disease-specific tuned thresholds.
            feature_schema: Approved feature schema dictionary.
            feature_order: List of predictor names in exact required order.
            metrics: Multi-label performance metrics dict.
            training_config: Configuration & hyperparameter dict.

        Returns:
            Path to the saved artifact directory.
        """
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        model_sub_dir = self.artifact_dir / "model"
        model_sub_dir.mkdir(exist_ok=True)

        # 1. Save Model Estimator(s)
        joblib.dump(model, model_sub_dir / "estimator.joblib")

        # 2. Save Preprocessor & Calibrator
        if preprocessor is not None:
            joblib.dump(preprocessor, self.artifact_dir / "preprocessor.pkl")
        if calibrator is not None:
            joblib.dump(calibrator, self.artifact_dir / "calibrator.pkl")

        # 3. Save JSON Metadata & Configuration
        with open(self.artifact_dir / "thresholds.json", "w", encoding="utf-8") as f:
            json.dump(thresholds, f, indent=2)

        with open(self.artifact_dir / "feature_schema.json", "w", encoding="utf-8") as f:
            json.dump(feature_schema, f, indent=2)

        with open(self.artifact_dir / "feature_order.json", "w", encoding="utf-8") as f:
            json.dump(feature_order, f, indent=2)

        with open(self.artifact_dir / "metrics.json", "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

        with open(self.artifact_dir / "training_config.json", "w", encoding="utf-8") as f:
            json.dump(training_config, f, indent=2)

        metadata = {
            "expert_name": self.expert_name,
            "version": self.version,
            "saved_timestamp": datetime.datetime.now().isoformat(),
            "n_predictors": len(feature_order),
            "target_diseases": config.TARGET_DISEASES,
            "status": "FROZEN"
        }
        with open(self.artifact_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        logger.info("Successfully saved frozen artifacts for '%s' to: %s", self.expert_name, self.artifact_dir)
        return self.artifact_dir

    def load_artifacts(self) -> Dict[str, Any]:
        """Load all frozen artifacts for an expert model version.

        Returns:
            Dict containing loaded 'model', 'preprocessor', 'calibrator',
            'thresholds', 'feature_schema', 'feature_order', 'metrics', 'metadata'.
        """
        artifact_dir = self.artifact_dir
        if not artifact_dir.exists():
            raise FileNotFoundError(f"Expert artifact directory not found: {artifact_dir}")

        # Load Model
        model_path = artifact_dir / "model" / "estimator.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"Model estimator not found at: {model_path}")
        model = joblib.load(model_path)

        # Load Preprocessor & Calibrator
        prep_path = artifact_dir / "preprocessor.pkl"
        preprocessor = joblib.load(prep_path) if prep_path.exists() else None

        calib_path = artifact_dir / "calibrator.pkl"
        calibrator = joblib.load(calib_path) if calib_path.exists() else None

        # Load JSON files
        with open(artifact_dir / "thresholds.json", "r", encoding="utf-8") as f:
            thresholds = json.load(f)

        with open(artifact_dir / "feature_order.json", "r", encoding="utf-8") as f:
            feature_order = json.load(f)

        with open(artifact_dir / "feature_schema.json", "r", encoding="utf-8") as f:
            feature_schema = json.load(f)

        with open(artifact_dir / "metadata.json", "r", encoding="utf-8") as f:
            metadata = json.load(f)

        metrics = {}
        metrics_path = artifact_dir / "metrics.json"
        if metrics_path.exists():
            with open(metrics_path, "r", encoding="utf-8") as f:
                metrics = json.load(f)

        return {
            "model": model,
            "preprocessor": preprocessor,
            "calibrator": calibrator,
            "thresholds": thresholds,
            "feature_order": feature_order,
            "feature_schema": feature_schema,
            "metadata": metadata,
            "metrics": metrics
        }
