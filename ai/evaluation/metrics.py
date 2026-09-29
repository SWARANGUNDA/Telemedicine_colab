"""
metrics.py — Multi-Label Evaluation Metrics Engine.

Calculates comprehensive evaluation metrics for multi-label disease prediction:
- Per-disease: ROC-AUC, PR-AUC, Precision, Recall/Sensitivity, Specificity, F1-Score, Brier Score, Confusion Matrix
- Overall multi-label metrics: Macro F1, Micro F1, Hamming Loss
"""

from typing import Any, Dict, List
import numpy as np
from sklearn.metrics import (
    brier_score_loss,
    confusion_matrix,
    f1_score,
    hamming_loss,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    auc
)

from ai.config import expert_config as config


def compute_pr_auc(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Calculate Precision-Recall AUC score."""
    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    return float(auc(recall, precision))


def compute_disease_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = config.DEFAULT_THRESHOLD
) -> Dict[str, Any]:
    """Calculate all evaluation metrics for a single disease target.

    Args:
        y_true: 1D array of ground truth binary labels (0/1).
        y_prob: 1D array of predicted probabilities [0.0, 1.0].
        threshold: Classification cutoff threshold.

    Returns:
        Dict of computed metric scores.
    """
    y_pred = (y_prob >= threshold).astype(int)

    # Confusion matrix elements (TN, FP, FN, TP)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    roc_auc = float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.5
    pr_auc = compute_pr_auc(y_true, y_prob) if len(np.unique(y_true)) > 1 else 0.0
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    brier = float(brier_score_loss(y_true, y_prob))

    return {
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "precision": round(precision, 4),
        "recall_sensitivity": round(recall, 4),
        "specificity": round(specificity, 4),
        "f1_score": round(f1, 4),
        "brier_score": round(brier, 4),
        "threshold": round(threshold, 4),
        "confusion_matrix": {
            "TN": int(tn),
            "FP": int(fp),
            "FN": int(fn),
            "TP": int(tp)
        }
    }


def evaluate_multilabel_predictions(
    y_true_df: Any,
    y_prob_matrix: np.ndarray,
    thresholds: Dict[str, float] = None
) -> Dict[str, Any]:
    """Evaluate multi-label predictions across all 5 disease targets.

    Args:
        y_true_df: DataFrame or 2D array of true binary targets.
        y_prob_matrix: 2D array of predicted probabilities (n_samples, 5).
        thresholds: Optional dict mapping disease ➔ threshold.

    Returns:
        Structured evaluation report dict.
    """
    if hasattr(y_true_df, "values"):
        y_true_mat = y_true_df.values
    else:
        y_true_mat = np.array(y_true_df)

    if thresholds is None:
        thresholds = {d: config.DEFAULT_THRESHOLD for d in config.TARGET_DISEASES}

    per_disease_reports = {}
    y_pred_matrix = np.zeros_like(y_prob_matrix, dtype=int)

    for idx, disease in enumerate(config.TARGET_DISEASES):
        t = thresholds.get(disease, config.DEFAULT_THRESHOLD)
        disease_metrics = compute_disease_metrics(y_true_mat[:, idx], y_prob_matrix[:, idx], threshold=t)
        per_disease_reports[disease] = disease_metrics
        y_pred_matrix[:, idx] = (y_prob_matrix[:, idx] >= t).astype(int)

    # Macro and Micro F1
    macro_f1 = float(np.mean([m["f1_score"] for m in per_disease_reports.values()]))
    micro_f1 = float(f1_score(y_true_mat.ravel(), y_pred_matrix.ravel(), zero_division=0))
    h_loss = float(hamming_loss(y_true_mat, y_pred_matrix))
    mean_brier = float(np.mean([m["brier_score"] for m in per_disease_reports.values()]))

    return {
        "per_disease": per_disease_reports,
        "summary": {
            "macro_f1": round(macro_f1, 4),
            "micro_f1": round(micro_f1, 4),
            "hamming_loss": round(h_loss, 4),
            "mean_brier_score": round(mean_brier, 4)
        }
    }
