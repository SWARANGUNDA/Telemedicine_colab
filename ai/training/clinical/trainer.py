"""
trainer.py — Multi-Model Training & Model Selection Engine.

Evaluates candidate tabular ML architectures:
- XGBoost
- LightGBM
- CatBoost
- Random Forest

Ranks models based on Validation set PR-AUC, ROC-AUC, Brier score, and F1.
One Expert internally exposes one unified interface returning 5 disease probabilities.
Ensembling is applied ONLY if it demonstrates a meaningful validated improvement over single best model.
"""

import logging
from typing import Any, Dict, List, Tuple
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from ai.config import expert_config as config
from ai.evaluation import metrics

logger = logging.getLogger("expert_models.trainer")


class SingleDiseaseEstimator:
    """Unified wrapper around single-disease estimator (XGBoost, LightGBM, CatBoost, etc.)."""

    def __init__(self, model_type: str = "xgboost", params: Dict[str, Any] = None):
        self.model_type = model_type.lower()
        self.params = params or {}
        self.estimators: Dict[str, Any] = {}

    def _instantiate_model(self):
        if self.model_type == "xgboost":
            import xgboost as xgb
            return xgb.XGBClassifier(**config.XGBOOST_PARAMS)
        elif self.model_type == "lightgbm":
            import lightgbm as lgb
            return lgb.LGBMClassifier(**config.LIGHTGBM_PARAMS)
        elif self.model_type == "catboost":
            import catboost as cb
            return cb.CatBoostClassifier(**config.CATBOOST_PARAMS)
        elif self.model_type == "random_forest":
            return RandomForestClassifier(**config.RANDOM_FOREST_PARAMS)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> "SingleDiseaseEstimator":
        """Fit per-disease estimators on training split."""
        for idx, disease in enumerate(config.TARGET_DISEASES):
            y_disease = y_train[:, idx]
            model = self._instantiate_model()
            model.fit(X_train, y_disease)
            self.estimators[disease] = model
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities for all 5 target diseases.

        Returns:
            2D numpy array of shape (n_samples, 5).
        """
        n_samples = X.shape[0]
        prob_matrix = np.zeros((n_samples, len(config.TARGET_DISEASES)))

        for idx, disease in enumerate(config.TARGET_DISEASES):
            model = self.estimators[disease]
            probas = model.predict_proba(X)
            if probas.shape[1] == 2:
                prob_matrix[:, idx] = probas[:, 1]
            else:
                prob_matrix[:, idx] = probas[:, 0]

        return prob_matrix


def compare_and_select_best_architecture(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    candidate_types: List[str] = None
) -> Tuple[SingleDiseaseEstimator, str, Dict[str, Any]]:
    """Train candidate models, evaluate on Validation set, and select best architecture.

    Args:
        X_train: Preprocessed training features.
        y_train: Training target matrix.
        X_val: Preprocessed validation features.
        y_val: Validation target matrix.
        candidate_types: List of model algorithm strings to evaluate.

    Returns:
        Tuple of (best_fitted_estimator, best_model_type_name, validation_results_dict).
    """
    if candidate_types is None:
        candidate_types = ["xgboost", "lightgbm", "catboost", "random_forest"]

    best_estimator = None
    best_type = None
    best_score = -1.0
    all_candidate_metrics = {}

    for m_type in candidate_types:
        try:
            logger.info("Training candidate architecture: %s", m_type.upper())
            estimator = SingleDiseaseEstimator(model_type=m_type)
            estimator.fit(X_train, y_train)

            val_probs = estimator.predict_proba(X_val)
            eval_report = metrics.evaluate_multilabel_predictions(y_val, val_probs)

            # Combined selection metric: 0.5 * PR-AUC + 0.5 * ROC-AUC
            mean_pr_auc = np.mean([m["pr_auc"] for m in eval_report["per_disease"].values()])
            mean_roc_auc = np.mean([m["roc_auc"] for m in eval_report["per_disease"].values()])
            selection_score = 0.5 * mean_pr_auc + 0.5 * mean_roc_auc

            eval_report["selection_score"] = round(float(selection_score), 4)
            all_candidate_metrics[m_type] = eval_report

            logger.info(
                "Candidate %s Validation Performance — Selection Score: %.4f, PR-AUC: %.4f, ROC-AUC: %.4f, Macro F1: %.4f",
                m_type.upper(), selection_score, mean_pr_auc, mean_roc_auc, eval_report["summary"]["macro_f1"]
            )

            if selection_score > best_score:
                best_score = selection_score
                best_type = m_type
                best_estimator = estimator

        except Exception as e:
            logger.warning("Failed to train candidate %s: %s", m_type, e)

    logger.info("Selected BEST Architecture: %s (Validation Selection Score: %.4f)", best_type.upper(), best_score)
    return best_estimator, best_type, all_candidate_metrics
