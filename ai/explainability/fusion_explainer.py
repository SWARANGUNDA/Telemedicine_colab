"""
fusion_explainer.py — Modality-Level Attribution Engine.

Computes relative modality importance weights for the fusion meta-learner,
showing how much each modality (Clinical, Wearable, Gut) contributes to
each disease prediction.

These are MODEL ATTRIBUTIONS, not causal biological contributions.
"""

import logging
from typing import Any, Dict, List

import numpy as np

from ai.config import fusion_config as config

logger = logging.getLogger("fusion_engine.fusion_explainer")


def compute_modality_weights_from_lr(
    meta_learner: Any,
    pathway_key: str,
) -> Dict[str, Dict[str, float]]:
    """Extract modality-level weights from Logistic Regression meta-learner coefficients.

    For each disease estimator, sums the absolute coefficients belonging to
    each modality's 5 probability features, then normalizes to percentages.

    Args:
        meta_learner: Fitted FusionMetaLearner with LR estimators.
        pathway_key: Active pathway key.

    Returns:
        Dict mapping disease -> {modality: weight_pct}.
    """
    modalities = config.PATHWAY_DEFINITIONS[pathway_key]
    n_diseases = len(config.TARGET_DISEASES)
    result = {}

    for disease in config.TARGET_DISEASES:
        estimator = meta_learner.estimators[disease]

        if hasattr(estimator, "coef_"):
            coefs = np.abs(estimator.coef_[0])
        else:
            logger.warning("Estimator for %s has no coef_; using uniform weights.", disease)
            coefs = np.ones(len(modalities) * n_diseases)

        mod_weights = {}
        for mod_idx, mod_key in enumerate(modalities):
            start = mod_idx * n_diseases
            end = start + n_diseases
            mod_weights[mod_key] = float(np.sum(coefs[start:end]))

        total = sum(mod_weights.values())
        if total > 0:
            mod_weights = {k: round(v / total * 100, 1) for k, v in mod_weights.items()}
        else:
            mod_weights = {k: round(100.0 / len(modalities), 1) for k in modalities}

        result[disease] = mod_weights

    return result


def compute_modality_weights_from_xgb(
    meta_learner: Any,
    pathway_key: str,
) -> Dict[str, Dict[str, float]]:
    """Extract modality-level weights from XGBoost feature importance.

    Sums feature importances per modality group.

    Args:
        meta_learner: Fitted FusionMetaLearner with XGBoost estimators.
        pathway_key: Active pathway key.

    Returns:
        Dict mapping disease -> {modality: weight_pct}.
    """
    modalities = config.PATHWAY_DEFINITIONS[pathway_key]
    n_diseases = len(config.TARGET_DISEASES)
    result = {}

    for disease in config.TARGET_DISEASES:
        estimator = meta_learner.estimators[disease]

        if hasattr(estimator, "feature_importances_"):
            importances = estimator.feature_importances_
        else:
            logger.warning("Estimator for %s has no feature_importances_; using uniform.", disease)
            importances = np.ones(len(modalities) * n_diseases)

        mod_weights = {}
        for mod_idx, mod_key in enumerate(modalities):
            start = mod_idx * n_diseases
            end = start + n_diseases
            mod_weights[mod_key] = float(np.sum(importances[start:end]))

        total = sum(mod_weights.values())
        if total > 0:
            mod_weights = {k: round(v / total * 100, 1) for k, v in mod_weights.items()}
        else:
            mod_weights = {k: round(100.0 / len(modalities), 1) for k in modalities}

        result[disease] = mod_weights

    return result


def compute_modality_attribution(
    meta_learner: Any,
    model_type: str,
    pathway_key: str,
) -> Dict[str, Dict[str, float]]:
    """Compute modality attribution weights using the appropriate method.

    Args:
        meta_learner: Fitted FusionMetaLearner.
        model_type: 'logistic_regression' or 'xgboost'.
        pathway_key: Active pathway key.

    Returns:
        Dict mapping disease -> {modality: weight_pct}.
    """
    if model_type == "logistic_regression":
        return compute_modality_weights_from_lr(meta_learner, pathway_key)
    elif model_type == "xgboost":
        return compute_modality_weights_from_xgb(meta_learner, pathway_key)
    else:
        logger.warning("Unknown model type %s; returning uniform weights.", model_type)
        modalities = config.PATHWAY_DEFINITIONS[pathway_key]
        uniform = {k: round(100.0 / len(modalities), 1) for k in modalities}
        return {d: uniform.copy() for d in config.TARGET_DISEASES}
