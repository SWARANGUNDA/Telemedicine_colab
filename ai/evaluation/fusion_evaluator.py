"""
evaluator.py — Comprehensive 7-Pathway Comparative Evaluation Engine.

Evaluates all modality pathways (C, W, G, C+W, C+G, W+G, C+W+G) on the
untouched test set, computing per-disease metrics and overall multi-label
performance metrics.
"""

import logging
from typing import Any, Dict

import numpy as np
from sklearn.metrics import (
    auc,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    hamming_loss,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)

from ai.config import fusion_config as config

logger = logging.getLogger("fusion_engine.evaluator")


def evaluate_pathway(
    y_true: np.ndarray,
    y_probs: np.ndarray,
    thresholds: Dict[str, float],
) -> Dict[str, Any]:
    """Evaluate a single pathway's predictions across all 5 diseases.

    Args:
        y_true: Ground truth targets (n_samples, 5).
        y_probs: Calibrated predicted probabilities (n_samples, 5).
        thresholds: Dict mapping disease -> threshold.

    Returns:
        Structured evaluation report dict.
    """
    per_disease = {}
    y_pred_matrix = np.zeros_like(y_probs, dtype=int)

    for idx, disease in enumerate(config.TARGET_DISEASES):
        y_t = y_true[:, idx]
        y_p = y_probs[:, idx]
        t = thresholds.get(disease, config.DEFAULT_THRESHOLD)
        y_pred = (y_p >= t).astype(int)
        y_pred_matrix[:, idx] = y_pred

        cm = confusion_matrix(y_t, y_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()

        roc = float(roc_auc_score(y_t, y_p)) if len(np.unique(y_t)) > 1 else 0.5
        prec_arr, rec_arr, _ = precision_recall_curve(y_t, y_p)
        pr = float(auc(rec_arr, prec_arr))

        per_disease[disease] = {
            "precision": round(float(precision_score(y_t, y_pred, zero_division=0)), 4),
            "recall_sensitivity": round(float(recall_score(y_t, y_pred, zero_division=0)), 4),
            "specificity": round(float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0, 4),
            "f1_score": round(float(f1_score(y_t, y_pred, zero_division=0)), 4),
            "roc_auc": round(roc, 4),
            "pr_auc": round(pr, 4),
            "brier_score": round(float(brier_score_loss(y_t, y_p)), 4),
            "threshold": round(t, 4),
            "confusion_matrix": {"TP": int(tp), "TN": int(tn), "FP": int(fp), "FN": int(fn)},
        }

    macro_f1 = float(np.mean([m["f1_score"] for m in per_disease.values()]))
    micro_f1 = float(f1_score(y_true.ravel(), y_pred_matrix.ravel(), zero_division=0))
    h_loss = float(hamming_loss(y_true, y_pred_matrix))
    mean_brier = float(np.mean([m["brier_score"] for m in per_disease.values()]))

    return {
        "per_disease": per_disease,
        "summary": {
            "macro_f1": round(macro_f1, 4),
            "micro_f1": round(micro_f1, 4),
            "hamming_loss": round(h_loss, 4),
            "mean_brier_score": round(mean_brier, 4),
        },
    }


def evaluate_all_pathways(
    all_probs: Dict[str, Dict[str, np.ndarray]],
    y_test: np.ndarray,
    pathway_models: Dict[str, Any],
    pathway_calibrators: Dict[str, Any],
    pathway_thresholds: Dict[str, Dict[str, float]],
) -> Dict[str, Dict[str, Any]]:
    """Evaluate all 7 pathways on the test set.

    Args:
        all_probs: Dict from oof_generator (modality -> split -> array).
        y_test: Test set targets (n_samples, 5).
        pathway_models: Dict mapping pathway_key -> fitted FusionMetaLearner.
        pathway_calibrators: Dict mapping pathway_key -> PathwayCalibrator.
        pathway_thresholds: Dict mapping pathway_key -> disease thresholds dict.

    Returns:
        Dict mapping pathway_key -> evaluation report dict.
    """
    from . import fusion_data_loader

    results = {}

    for pathway_key in config.PATHWAY_DEFINITIONS:
        logger.info("Evaluating pathway: %s", pathway_key)

        X_test = fusion_data_loader.build_pathway_features(all_probs, pathway_key, "test")
        model = pathway_models[pathway_key]
        calibrator = pathway_calibrators[pathway_key]
        thresholds = pathway_thresholds[pathway_key]

        raw_probs = model.predict_proba(X_test)
        calib_probs = calibrator.calibrate(raw_probs)

        report = evaluate_pathway(y_test, calib_probs, thresholds)
        results[pathway_key] = report

        logger.info(
            "  %s Test: Macro F1=%.4f, Micro F1=%.4f, Brier=%.4f",
            pathway_key,
            report["summary"]["macro_f1"],
            report["summary"]["micro_f1"],
            report["summary"]["mean_brier_score"],
        )

    return results
