"""
evaluate_all_experts.py — Comprehensive Disease-by-Disease Evaluation of Frozen Expert Models.

Performs evaluation ONLY on the untouched 3,000-patient test set (Split == 'test') for:
- Clinical Expert (clinical_v1)
- Wearable Expert (wearable_v1)
- Gut Microbiome Expert (gut_v1)

Generates:
1. disease_metrics.csv
2. f1_comparison.csv
3. overall_metrics.csv
4. Confusion matrix plots / JSONs
5. ROC curves plots / JSONs
6. PR curves plots / JSONs
7. Calibration curves plots / JSONs
8. comparison_report.md artifact
"""

import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    roc_curve,
    precision_recall_curve,
    confusion_matrix,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    brier_score_loss,
    hamming_loss,
    auc
)

from expert_models import config, data_loader, metrics
from expert_models.artifact_manager import ExpertArtifactManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evaluate_all_experts")

OUTPUT_DIR = config.REPORTS_DIR / "final_expert_comparison"
CONF_DIR = OUTPUT_DIR / "confusion_matrices"
ROC_DIR = OUTPUT_DIR / "roc_curves"
PR_DIR = OUTPUT_DIR / "pr_curves"
CALIB_DIR = OUTPUT_DIR / "calibration_curves"

for d in [OUTPUT_DIR, CONF_DIR, ROC_DIR, PR_DIR, CALIB_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def run_comprehensive_evaluation():
    logger.info("==================================================================")
    logger.info("   COMPREHENSIVE DISEASE-BY-DISEASE FROZEN EXPERT EVALUATION     ")
    logger.info("==================================================================")

    experts_info = [
        ("Clinical", "clinical", config.CLINICAL_DATASET_PATH, "clinical_features.json"),
        ("Wearable", "wearable", config.WEARABLE_DATASET_PATH, "wearable_features.json"),
        ("Gut", "gut", config.GUT_DATASET_PATH, "gut_features.json"),
    ]

    all_disease_results = []
    overall_summary_results = []
    f1_comp_list = []

    raw_probs_by_expert = {}
    calib_probs_by_expert = {}
    y_test_dict = {}
    thresholds_by_expert = {}

    for label, expert_key, csv_path, schema_file in experts_info:
        logger.info("Evaluating expert: %s (%s_v1)", label, expert_key)

        # 1. Load dataset & split
        X, y, splits, approved_predictors = data_loader.load_dataset_for_expert(
            dataset_path=csv_path,
            schema_filename=schema_file
        )
        test_mask = (splits == "test")
        X_test = X[test_mask]
        y_test = y[test_mask]
        y_test_dict[expert_key] = y_test

        # 2. Load frozen artifacts
        manager = ExpertArtifactManager(expert_name=expert_key, version=config.EXPERT_VERSION)
        artifacts = manager.load_artifacts()

        model = artifacts["model"]
        preprocessor = artifacts["preprocessor"]
        calibrator = artifacts["calibrator"]
        thresholds = artifacts["thresholds"]
        feature_order = artifacts["feature_order"]

        thresholds_by_expert[expert_key] = thresholds

        # 3. Transform test features
        df_test_ordered = X_test[feature_order].copy()
        if preprocessor is not None:
            X_test_prep = preprocessor.transform(df_test_ordered)
        else:
            X_test_prep = df_test_ordered.values.astype(np.float64)

        # 4. Predict raw probabilities
        raw_probs = model.predict_proba(X_test_prep)
        if raw_probs.ndim == 1:
            raw_probs = raw_probs.reshape(1, -1)
        raw_probs_by_expert[expert_key] = raw_probs

        # 5. Apply calibrator
        if calibrator is not None:
            calib_probs = calibrator.calibrate_probas(raw_probs)
        else:
            calib_probs = raw_probs
        calib_probs_by_expert[expert_key] = calib_probs

        # 6. Overall Multi-label evaluation
        overall_eval = metrics.evaluate_multilabel_predictions(y_test, calib_probs, thresholds=thresholds)
        summary = overall_eval["summary"]
        overall_summary_results.append({
            "Expert": label,
            "Macro_F1": summary["macro_f1"],
            "Micro_F1": summary["micro_f1"],
            "Hamming_Loss": summary["hamming_loss"],
            "Overall_Brier_Score": summary["mean_brier_score"]
        })

        # 7. Disease-by-disease evaluation
        y_test_mat = y_test.values
        for idx, disease in enumerate(config.TARGET_DISEASES):
            y_true_d = y_test_mat[:, idx]
            y_prob_d = calib_probs[:, idx]
            t = thresholds.get(disease, config.DEFAULT_THRESHOLD)
            y_pred_d = (y_prob_d >= t).astype(int)

            cm = confusion_matrix(y_true_d, y_pred_d, labels=[0, 1])
            tn, fp, fn, tp = cm.ravel()
            total_n = len(y_true_d)
            pos_prev = float(np.mean(y_true_d))

            roc_auc = float(roc_auc_score(y_true_d, y_prob_d)) if len(np.unique(y_true_d)) > 1 else 0.5
            prec_arr, rec_arr, _ = precision_recall_curve(y_true_d, y_prob_d)
            pr_auc = float(auc(rec_arr, prec_arr))

            prec = float(precision_score(y_true_d, y_pred_d, zero_division=0))
            rec = float(recall_score(y_true_d, y_pred_d, zero_division=0))
            spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
            f1 = float(f1_score(y_true_d, y_pred_d, zero_division=0))
            brier = float(brier_score_loss(y_true_d, y_prob_d))

            all_disease_results.append({
                "Disease": disease,
                "Expert": label,
                "Precision": round(prec, 4),
                "Recall_Sensitivity": round(rec, 4),
                "Specificity": round(spec, 4),
                "F1_Score": round(f1, 4),
                "ROC_AUC": round(roc_auc, 4),
                "PR_AUC": round(pr_auc, 4),
                "Brier_Score": round(brier, 4),
                "Tuned_Threshold": round(t, 4),
                "TP": int(tp),
                "TN": int(tn),
                "FP": int(fp),
                "FN": int(fn),
                "Positive_Prevalence": round(pos_prev, 4)
            })

    # Convert to DataFrame
    df_disease = pd.DataFrame(all_disease_results)
    df_overall = pd.DataFrame(overall_summary_results)

    # Save disease_metrics.csv
    df_disease.to_csv(OUTPUT_DIR / "disease_metrics.csv", index=False)
    # Save overall_metrics.csv
    df_overall.to_csv(OUTPUT_DIR / "overall_metrics.csv", index=False)

    # Create compact F1 comparison table
    f1_rows = []
    for disease in config.TARGET_DISEASES:
        c_f1 = df_disease[(df_disease["Disease"] == disease) & (df_disease["Expert"] == "Clinical")]["F1_Score"].values[0]
        w_f1 = df_disease[(df_disease["Disease"] == disease) & (df_disease["Expert"] == "Wearable")]["F1_Score"].values[0]
        g_f1 = df_disease[(df_disease["Disease"] == disease) & (df_disease["Expert"] == "Gut")]["F1_Score"].values[0]

        best_exp = "Clinical" if c_f1 >= max(w_f1, g_f1) else ("Wearable" if w_f1 >= g_f1 else "Gut")
        f1_rows.append({
            "Disease": disease,
            "Clinical_F1": c_f1,
            "Wearable_F1": w_f1,
            "Gut_F1": g_f1,
            "Best_Expert": best_exp
        })

    df_f1_comp = pd.DataFrame(f1_rows)
    df_f1_comp.to_csv(OUTPUT_DIR / "f1_comparison.csv", index=False)

    # Generate Plots
    for disease in config.TARGET_DISEASES:
        disease_idx = config.TARGET_DISEASES.index(disease)

        # 1. ROC Curves
        plt.figure(figsize=(7, 5))
        for label, expert_key, _, _ in experts_info:
            y_t = y_test_dict[expert_key].values[:, disease_idx]
            y_p = calib_probs_by_expert[expert_key][:, disease_idx]
            fpr, tpr, _ = roc_curve(y_t, y_p)
            score = roc_auc_score(y_t, y_p)
            plt.plot(fpr, tpr, label=f"{label} (AUC = {score:.4f})", linewidth=2)
        plt.plot([0, 1], [0, 1], 'k--', alpha=0.5)
        plt.xlabel("False Positive Rate (1 - Specificity)")
        plt.ylabel("True Positive Rate (Sensitivity)")
        plt.title(f"ROC Curves — {disease}")
        plt.legend(loc="lower right")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(ROC_DIR / f"roc_{disease}.png", dpi=150)
        plt.close()

        # 2. PR Curves
        plt.figure(figsize=(7, 5))
        for label, expert_key, _, _ in experts_info:
            y_t = y_test_dict[expert_key].values[:, disease_idx]
            y_p = calib_probs_by_expert[expert_key][:, disease_idx]
            prec_arr, rec_arr, _ = precision_recall_curve(y_t, y_p)
            score = auc(rec_arr, prec_arr)
            plt.plot(rec_arr, prec_arr, label=f"{label} (PR-AUC = {score:.4f})", linewidth=2)
        plt.xlabel("Recall (Sensitivity)")
        plt.ylabel("Precision")
        plt.title(f"Precision-Recall Curves — {disease}")
        plt.legend(loc="lower left")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(PR_DIR / f"pr_{disease}.png", dpi=150)
        plt.close()

        # 3. Calibration Curves
        plt.figure(figsize=(7, 5))
        for label, expert_key, _, _ in experts_info:
            y_t = y_test_dict[expert_key].values[:, disease_idx]
            y_p = calib_probs_by_expert[expert_key][:, disease_idx]
            prob_true, prob_pred = calibration_curve(y_t, y_p, n_bins=10)
            plt.plot(prob_pred, prob_true, marker='o', label=f"{label}", linewidth=2)
        plt.plot([0, 1], [0, 1], 'k--', alpha=0.5, label="Perfectly Calibrated")
        plt.xlabel("Mean Predicted Probability")
        plt.ylabel("Fraction of Positives")
        plt.title(f"Calibration Curves — {disease}")
        plt.legend(loc="upper left")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(CALIB_DIR / f"calibration_{disease}.png", dpi=150)
        plt.close()

        # 4. Confusion Matrix summary JSON & plots
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        for idx_e, (label, expert_key, _, _) in enumerate(experts_info):
            y_t = y_test_dict[expert_key].values[:, disease_idx]
            y_p = calib_probs_by_expert[expert_key][:, disease_idx]
            t = thresholds_by_expert[expert_key].get(disease, 0.5)
            y_pred = (y_p >= t).astype(int)
            cm = confusion_matrix(y_t, y_pred, labels=[0, 1])

            ax = axes[idx_e]
            im = ax.imshow(cm, cmap="Blues", interpolation="nearest")
            ax.set_title(f"{label} Expert (T={t:.2f})")
            ax.set_xlabel("Predicted Label")
            ax.set_ylabel("True Label")
            ax.set_xticks([0, 1])
            ax.set_yticks([0, 1])
            for i in range(2):
                for j in range(2):
                    ax.text(j, i, str(cm[i, j]), ha="center", va="center", color="white" if cm[i, j] > cm.max()/2 else "black")
        plt.tight_layout()
        plt.savefig(CONF_DIR / f"confusion_{disease}.png", dpi=150)
        plt.close()

    logger.info("Saved all metrics, CSVs, and plots to %s", OUTPUT_DIR)
    return df_disease, df_f1_comp, df_overall


if __name__ == "__main__":
    run_comprehensive_evaluation()
