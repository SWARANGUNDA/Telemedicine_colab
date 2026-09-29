"""
threshold_tuner.py — Validation-Only Classification Threshold Tuner.

Tunes disease-specific classification thresholds using VALIDATION DATA ONLY.

Never uses Test data for threshold selection.
Saves optimal thresholds into model artifact package (thresholds.json).
"""

import logging
from typing import Any, Dict
import numpy as np
from sklearn.metrics import f1_score

from ai.config import expert_config as config

logger = logging.getLogger("expert_models.threshold_tuner")


def find_optimal_threshold_for_disease(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    min_t: float = config.THRESHOLD_SEARCH_MIN,
    max_t: float = config.THRESHOLD_SEARCH_MAX,
    step: float = config.THRESHOLD_SEARCH_STEP
) -> float:
    """Find optimal classification threshold for a single disease on Validation fold.

    Maximizes F1-score across candidate threshold values.

    Args:
        y_true: Ground truth binary array for validation fold.
        y_prob: Predicted probability array for validation fold.
        min_t: Minimum search bound (0.10).
        max_t: Maximum search bound (0.90).
        step: Search step resolution (0.01).

    Returns:
        Optimal threshold float.
    """
    best_t = config.DEFAULT_THRESHOLD
    best_f1 = -1.0

    threshold_grid = np.arange(min_t, max_t + step, step)
    for t in threshold_grid:
        y_pred = (y_prob >= t).astype(int)
        score = f1_score(y_true, y_pred, zero_division=0)
        if score > best_f1:
            best_f1 = score
            best_t = round(float(t), 4)

    return best_t


def tune_expert_thresholds(
    y_val_df: Any,
    y_val_prob_matrix: np.ndarray
) -> Dict[str, float]:
    """Tune optimal thresholds for all 5 target diseases on Validation fold.

    Args:
        y_val_df: Validation set target DataFrame or 2D array.
        y_val_prob_matrix: Validation set predicted probability matrix.

    Returns:
        Dict mapping disease name ➔ optimal threshold value.
    """
    if hasattr(y_val_df, "values"):
        y_val_mat = y_val_df.values
    else:
        y_val_mat = np.array(y_val_df)

    optimal_thresholds: Dict[str, float] = {}

    for idx, disease in enumerate(config.TARGET_DISEASES):
        opt_t = find_optimal_threshold_for_disease(y_val_mat[:, idx], y_val_prob_matrix[:, idx])
        optimal_thresholds[disease] = opt_t
        logger.info("Validation tuned threshold for %s: %.4f", disease, opt_t)

    return optimal_thresholds
