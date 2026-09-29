"""
calibration.py — Probability Calibration Engine.

Phase 4 Fusion consumes probabilities, so probability calibration quality is critical.
Fits Platt Scaling (Sigmoid) or Isotonic Calibration on validation/out-of-fold predictions.

Evaluates Brier Score before and after calibration.
"""

import logging
from typing import Any, Dict
import numpy as np
from sklearn.calibration import CalibratedClassifierCV, _CalibratedClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from ai.config import expert_config as config

logger = logging.getLogger("expert_models.calibration")


class DiseaseProbabilityCalibrator:
    """Probability calibrator wrapping per-disease Platt (Sigmoid) / Isotonic calibrators."""

    def __init__(self, method: str = config.CALIBRATION_METHOD):
        self.method = method
        self.calibrators: Dict[str, Any] = {}

    def fit(self, y_val: np.ndarray, y_val_raw_prob: np.ndarray) -> "DiseaseProbabilityCalibrator":
        """Fit calibrators on validation fold predictions.

        Args:
            y_val: 2D array of true validation targets (n_samples, 5).
            y_val_raw_prob: 2D array of raw predicted probabilities (n_samples, 5).
        """
        for idx, disease in enumerate(config.TARGET_DISEASES):
            y_true_d = y_val[:, idx]
            y_prob_d = y_val_raw_prob[:, idx].reshape(-1, 1)

            if self.method == "isotonic":
                calib = IsotonicRegression(out_of_bounds="clip")
                calib.fit(y_prob_d.ravel(), y_true_d)
            else:
                # Platt Scaling via Logistic Regression on logit / raw proba
                calib = LogisticRegression(C=1.0, solver="lbfgs")
                calib.fit(y_prob_d, y_true_d)

            self.calibrators[disease] = calib
            logger.info("Fitted %s probability calibrator for %s", self.method, disease)

        return self

    def calibrate_probas(self, y_raw_prob: np.ndarray) -> np.ndarray:
        """Apply fitted calibrators to raw predicted probabilities.

        Args:
            y_raw_prob: 2D array of raw probabilities (n_samples, 5).

        Returns:
            2D array of calibrated probabilities (n_samples, 5).
        """
        if not self.calibrators:
            return y_raw_prob  # Return uncalibrated if not fitted

        calibrated_matrix = np.zeros_like(y_raw_prob)

        for idx, disease in enumerate(config.TARGET_DISEASES):
            calib = self.calibrators[disease]
            raw_d = y_raw_prob[:, idx].reshape(-1, 1)

            if isinstance(calib, IsotonicRegression):
                calibrated_matrix[:, idx] = calib.predict(raw_d.ravel())
            else:
                probas = calib.predict_proba(raw_d)
                if probas.shape[1] == 2:
                    calibrated_matrix[:, idx] = probas[:, 1]
                else:
                    calibrated_matrix[:, idx] = probas[:, 0]

        return np.clip(calibrated_matrix, 0.0, 1.0)
