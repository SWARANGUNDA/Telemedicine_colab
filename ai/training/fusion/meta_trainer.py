"""
meta_trainer.py — Late-Fusion Meta-Learner Training & Selection Engine.

Trains and compares Logistic Regression and XGBoost meta-learners for each
of the 7 modality pathways. Selects the best architecture per pathway based
on validation performance.

Also handles threshold tuning and probability calibration on validation data.
"""

import logging
from typing import Any, Dict, List, Tuple

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score, average_precision_score
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression

from ai.config import fusion_config as config

logger = logging.getLogger("fusion_engine.meta_trainer")


class FusionMetaLearner:
    """Unified wrapper for per-disease meta-learner models for a single pathway."""

    def __init__(self, model_type: str = "logistic_regression"):
        self.model_type = model_type
        self.estimators: Dict[str, Any] = {}

    def _make_model(self):
        if self.model_type == "logistic_regression":
            return LogisticRegression(**config.META_LR_PARAMS)
        elif self.model_type == "xgboost":
            import xgboost as xgb
            return xgb.XGBClassifier(**config.META_XGB_PARAMS)
        else:
            raise ValueError(f"Unknown meta-learner type: {self.model_type}")

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> "FusionMetaLearner":
        """Fit one binary model per disease target."""
        for idx, disease in enumerate(config.TARGET_DISEASES):
            model = self._make_model()
            model.fit(X_train, y_train[:, idx])
            self.estimators[disease] = model
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities for all 5 diseases."""
        n = X.shape[0]
        probs = np.zeros((n, len(config.TARGET_DISEASES)))
        for idx, disease in enumerate(config.TARGET_DISEASES):
            p = self.estimators[disease].predict_proba(X)
            probs[:, idx] = p[:, 1] if p.shape[1] == 2 else p[:, 0]
        return probs


class PathwayCalibrator:
    """Per-disease probability calibrator for a single pathway."""

    def __init__(self):
        self.calibrators: Dict[str, Any] = {}

    def fit(self, y_val: np.ndarray, raw_probs: np.ndarray) -> "PathwayCalibrator":
        for idx, disease in enumerate(config.TARGET_DISEASES):
            calib = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000)
            calib.fit(raw_probs[:, idx].reshape(-1, 1), y_val[:, idx])
            self.calibrators[disease] = calib
        return self

    def calibrate(self, raw_probs: np.ndarray) -> np.ndarray:
        out = np.zeros_like(raw_probs)
        for idx, disease in enumerate(config.TARGET_DISEASES):
            calib = self.calibrators[disease]
            p = calib.predict_proba(raw_probs[:, idx].reshape(-1, 1))
            out[:, idx] = p[:, 1] if p.shape[1] == 2 else p[:, 0]
        return np.clip(out, 0.0, 1.0)


def tune_thresholds(y_val: np.ndarray, probs: np.ndarray) -> Dict[str, float]:
    """Tune per-disease classification thresholds on validation data."""
    thresholds = {}
    for idx, disease in enumerate(config.TARGET_DISEASES):
        best_t, best_f1 = config.DEFAULT_THRESHOLD, -1.0
        for t in np.arange(config.THRESHOLD_SEARCH_MIN, config.THRESHOLD_SEARCH_MAX + config.THRESHOLD_SEARCH_STEP, config.THRESHOLD_SEARCH_STEP):
            preds = (probs[:, idx] >= t).astype(int)
            f1 = f1_score(y_val[:, idx], preds, zero_division=0)
            if f1 > best_f1:
                best_f1 = f1
                best_t = round(float(t), 4)
        thresholds[disease] = best_t
        logger.info("Threshold for %s: %.4f (Val F1=%.4f)", disease, best_t, best_f1)
    return thresholds


def train_and_select_for_pathway(
    pathway_key: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
) -> Tuple[FusionMetaLearner, str, PathwayCalibrator, Dict[str, float], Dict[str, Any]]:
    """Train LR and XGBoost meta-learners, select best, calibrate, tune thresholds.

    Returns:
        (best_model, best_type, calibrator, thresholds, comparison_metrics).
    """
    logger.info("Training meta-learners for pathway: %s", pathway_key)

    candidates = {}
    for mtype in ["logistic_regression", "xgboost"]:
        model = FusionMetaLearner(model_type=mtype)
        model.fit(X_train, y_train)
        val_probs = model.predict_proba(X_val)

        # Compute selection score
        mean_roc = np.mean([
            roc_auc_score(y_val[:, i], val_probs[:, i])
            for i in range(len(config.TARGET_DISEASES))
            if len(np.unique(y_val[:, i])) > 1
        ])
        mean_pr = np.mean([
            average_precision_score(y_val[:, i], val_probs[:, i])
            for i in range(len(config.TARGET_DISEASES))
            if len(np.unique(y_val[:, i])) > 1
        ])
        score = 0.5 * mean_roc + 0.5 * mean_pr

        candidates[mtype] = {
            "model": model,
            "val_probs": val_probs,
            "selection_score": score,
            "mean_roc_auc": round(mean_roc, 4),
            "mean_pr_auc": round(mean_pr, 4),
        }
        logger.info(
            "  %s: Selection Score=%.4f (ROC-AUC=%.4f, PR-AUC=%.4f)",
            mtype.upper(), score, mean_roc, mean_pr,
        )

    # Select best
    best_type = max(candidates, key=lambda k: candidates[k]["selection_score"])
    best_info = candidates[best_type]
    best_model = best_info["model"]
    best_val_probs = best_info["val_probs"]

    logger.info("Selected %s for pathway %s", best_type.upper(), pathway_key)

    # Calibrate on validation
    calibrator = PathwayCalibrator()
    calibrator.fit(y_val, best_val_probs)
    calibrated_val = calibrator.calibrate(best_val_probs)

    # Tune thresholds on calibrated validation probabilities
    thresholds = tune_thresholds(y_val, calibrated_val)

    comparison = {
        mtype: {
            "selection_score": info["selection_score"],
            "mean_roc_auc": info["mean_roc_auc"],
            "mean_pr_auc": info["mean_pr_auc"],
        }
        for mtype, info in candidates.items()
    }

    return best_model, best_type, calibrator, thresholds, comparison
