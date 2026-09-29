"""
baselines.py — Baseline Models Engine.

Provides simple baseline models (Dummy Most Frequent & Logistic Regression)
to establish performance benchmark floors before complex GBDT model selection.
"""

from typing import Dict
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression

from ai.config import expert_config as config


class MultiDiseaseBaselineEstimator:
    """Baseline multi-disease classifier wrapping per-disease baseline models."""

    def __init__(self, baseline_type: str = "logistic_regression"):
        self.baseline_type = baseline_type
        self.estimators: Dict[str, Any] = {}

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> "MultiDiseaseBaselineEstimator":
        """Fit baseline estimators for each target disease on training fold."""
        for idx, disease in enumerate(config.TARGET_DISEASES):
            y_disease = y_train[:, idx]
            if self.baseline_type == "dummy":
                model = DummyClassifier(strategy="most_frequent")
            else:
                model = LogisticRegression(max_iter=500, random_state=config.RANDOM_SEED)
            model.fit(X_train, y_disease)
            self.estimators[disease] = model
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probabilities for all 5 diseases.

        Returns:
            2D numpy array of shape (n_samples, 5) with probability scores.
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
