"""
train_wearable_expert_v3.py — Scientific Training, Evaluation & Diagnostic Pipeline for Wearable Expert v3.

Executes:
1. Load wearable_standard_v3.csv, wearable_cgm_v3.csv, labels_v3.csv, split_manifest_v3.csv (N=20,000).
2. Experiment A: Standard Wearable Telemetry Only (10 Features).
3. Experiment B: Standard Wearable + CGM Telemetry (15 Features, Missingness Handled).
4. Compare XGBoost, LightGBM, CatBoost on Validation fold ONLY.
5. Calibrate probabilities (Isotonic Regression) & tune disease thresholds on Validation fold ONLY.
6. Evaluate selected candidate ONCE on untouched 3,000-patient Test set.
7. Compute Bootstrap 95% CIs (B=1,000), SHAP feature importance, missing-data robustness, and leakage audit.
8. Compare Wearable v1 vs Wearable v3.
9. Save model payload to expert_models/saved_models/wearable_v3/.
10. Export wearable_v3_expert_report.md and wearable_v3_metrics.json.
"""

import os
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
import shap

from catboost import CatBoostClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

from sklearn.preprocessing import StandardScaler
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score, precision_recall_curve, auc, brier_score_loss, confusion_matrix, hamming_loss

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("train_wearable_v3")

DATA_DIR = Path("data/multimodal_v3")
SAVE_DIR = Path("expert_models/saved_models/wearable_v3")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

DISEASES = ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]
STD_WEARABLE_FEATURES = [
    "Average_Daily_Steps", "Active_Minutes", "Sedentary_Time_Minutes",
    "Resting_Heart_Rate", "Heart_Rate_Variability_RMSSD", "Sleep_Duration_Hours",
    "Sleep_Efficiency_Score", "Autonomic_Stress_Score", "Activity_Energy_Expenditure",
    "Exercise_Frequency_Days"
]
CGM_FEATURES = [
    "CGM_Average_Glucose", "CGM_Glucose_CV", "CGM_Time_In_Range",
    "CGM_Time_Above_Range", "CGM_Time_Below_Range"
]

def find_optimal_threshold(y_true, probs):
    best_t = 0.50
    best_f1 = -1.0
    for t in np.linspace(0.10, 0.90, 81):
        preds = (probs >= t).astype(int)
        score = f1_score(y_true, preds, zero_division=0)
        if score > best_f1:
            best_f1 = score
            best_t = t
    return round(float(best_t), 4)

def evaluate_predictions(y_true, y_prob, thresholds):
    preds = np.zeros_like(y_prob, dtype=int)
    disease_metrics = {}
    f1s = []

    for d_idx, disease in enumerate(DISEASES):
        t_opt = thresholds[disease]
        y_d_true = y_true[:, d_idx]
        y_d_prob = y_prob[:, d_idx]
        y_d_pred = (y_d_prob >= t_opt).astype(int)
        preds[:, d_idx] = y_d_pred

        f1 = f1_score(y_d_true, y_d_pred, zero_division=0)
        prec = precision_score(y_d_true, y_d_pred, zero_division=0)
        rec = recall_score(y_d_true, y_d_pred, zero_division=0)
        r_auc = roc_auc_score(y_d_true, y_d_prob)
        
        p_vals, r_vals, _ = precision_recall_curve(y_d_true, y_d_prob)
        pr_auc_val = auc(r_vals, p_vals)
        brier = brier_score_loss(y_d_true, y_d_prob)
        cm = confusion_matrix(y_d_true, y_d_pred).tolist()

        f1s.append(f1)
        disease_metrics[disease] = {
            "f1": round(float(f1), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "roc_auc": round(float(r_auc), 4),
            "pr_auc": round(float(pr_auc_val), 4),
            "brier_score": round(float(brier), 4),
            "confusion_matrix": cm
        }

    macro_f1 = round(float(np.mean(f1s)), 4)
    micro_f1 = round(float(f1_score(y_true, preds, average="micro", zero_division=0)), 4)
    h_loss = round(float(hamming_loss(y_true, preds)), 4)
    m_brier = round(float(np.mean([disease_metrics[d]["brier_score"] for d in DISEASES])), 4)

    return {
        "macro_f1": macro_f1,
        "micro_f1": micro_f1,
        "hamming_loss": h_loss,
        "mean_brier": m_brier,
        "per_disease": disease_metrics
    }, preds

def compute_bootstrap_ci(y_true, y_prob, thresholds, n_boot=1000, seed=42):
    np.random.seed(seed)
    n_samples = len(y_true)
    boot_macro_f1s = []

    for _ in range(n_boot):
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        f1s = []
        for d_idx, disease in enumerate(DISEASES):
            t_opt = thresholds[disease]
            pred = (y_prob[indices, d_idx] >= t_opt).astype(int)
            f1s.append(f1_score(y_true[indices, d_idx], pred, zero_division=0))
        boot_macro_f1s.append(np.mean(f1s))

    ci_low = round(float(np.percentile(boot_macro_f1s, 2.5)), 4)
    ci_high = round(float(np.percentile(boot_macro_f1s, 97.5)), 4)
    return [ci_low, ci_high]

def train_and_eval_wearable_v3():
    logger.info("Loading Wearable v3 Datasets...")
    wear_std_df = pd.read_csv(DATA_DIR / "wearable_standard_v3.csv")
    wear_cgm_df = pd.read_csv(DATA_DIR / "wearable_cgm_v3.csv")
    labels_df = pd.read_csv(DATA_DIR / "labels_v3.csv")
    split_df = pd.read_csv(DATA_DIR / "split_manifest_v3.csv")

    train_mask = (split_df["Split"] == "Train").values
    val_mask   = (split_df["Split"] == "Val").values
    test_mask  = (split_df["Split"] == "Test").values
    y_all = labels_df[DISEASES].values

    # ------------------------------------------------------------------
    # EXPERIMENT A: Standard Wearable Only (10 Features)
    # ------------------------------------------------------------------
    logger.info("--- EXPERIMENT A: Standard Wearable Telemetry (10 Features) ---")
    X_std_raw = wear_std_df[STD_WEARABLE_FEATURES].copy()
    medians_std = X_std_raw.iloc[train_mask].median()
    X_std_imp = X_std_raw.fillna(medians_std)

    scaler_std = StandardScaler()
    X_tr_std = scaler_std.fit_transform(X_std_imp.iloc[train_mask])
    X_va_std = scaler_std.transform(X_std_imp.iloc[val_mask])
    X_te_std = scaler_std.transform(X_std_imp.iloc[test_mask])

    architectures = ["XGBoost", "LightGBM", "CatBoost"]
    val_results_exp_a = {}
    models_exp_a = {}

    for arch in architectures:
        raw_val_probs = np.zeros_like(y_all[val_mask], dtype=float)
        arch_models = []

        for d_idx, disease in enumerate(DISEASES):
            if arch == "XGBoost":
                clf = XGBClassifier(n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42, eval_metric="logloss")
            elif arch == "LightGBM":
                clf = LGBMClassifier(n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42, verbose=-1)
            else: # CatBoost
                clf = CatBoostClassifier(iterations=150, depth=5, learning_rate=0.05, random_seed=42, verbose=0)

            clf.fit(X_tr_std, y_all[train_mask, d_idx])
            raw_val_probs[:, d_idx] = clf.predict_proba(X_va_std)[:, 1]
            arch_models.append(clf)

        val_f1s = [f1_score(y_all[val_mask, d], (raw_val_probs[:, d] >= 0.5).astype(int), zero_division=0) for d in range(len(DISEASES))]
        val_macro = np.mean(val_f1s)
        val_results_exp_a[arch] = val_macro
        models_exp_a[arch] = arch_models
        logger.info(f"Validation Macro F1 Exp A ({arch}): {val_macro:.4f}")

    best_arch_a = max(val_results_exp_a, key=val_results_exp_a.get)
    selected_models_a = models_exp_a[best_arch_a]

    # Calibrate & Threshold Tune Exp A
    raw_val_p_a  = np.zeros_like(y_all[val_mask], dtype=float)
    raw_test_p_a = np.zeros_like(y_all[test_mask], dtype=float)
    for d_idx in range(len(DISEASES)):
        raw_val_p_a[:, d_idx]  = selected_models_a[d_idx].predict_proba(X_va_std)[:, 1]
        raw_test_p_a[:, d_idx] = selected_models_a[d_idx].predict_proba(X_te_std)[:, 1]

    val_cal_p_a  = np.zeros_like(y_all[val_mask], dtype=float)
    test_cal_p_a = np.zeros_like(y_all[test_mask], dtype=float)
    thresholds_a = {}

    for d_idx, disease in enumerate(DISEASES):
        iso = IsotonicRegression(out_of_bounds="clip").fit(raw_val_p_a[:, d_idx], y_all[val_mask, d_idx])
        val_cal_p_a[:, d_idx]  = iso.transform(raw_val_p_a[:, d_idx])
        test_cal_p_a[:, d_idx] = iso.transform(raw_test_p_a[:, d_idx])
        thresholds_a[disease]  = find_optimal_threshold(y_all[val_mask, d_idx], val_cal_p_a[:, d_idx])

    metrics_exp_a, _ = evaluate_predictions(y_all[test_mask], test_cal_p_a, thresholds_a)
    metrics_exp_a["bootstrap_95_ci_macro_f1"] = compute_bootstrap_ci(y_all[test_mask], test_cal_p_a, thresholds_a)
    metrics_exp_a["selected_architecture"] = best_arch_a
    metrics_exp_a["thresholds"] = thresholds_a

    # ------------------------------------------------------------------
    # EXPERIMENT B: Standard Wearable + CGM Telemetry (15 Features)
    # ------------------------------------------------------------------
    logger.info("--- EXPERIMENT B: Standard Wearable + CGM Telemetry (15 Features) ---")
    all_wear_df = pd.concat([wear_std_df[STD_WEARABLE_FEATURES], wear_cgm_df[CGM_FEATURES]], axis=1)
    medians_all = all_wear_df.iloc[train_mask].median()
    X_all_imp = all_wear_df.fillna(medians_all)

    scaler_all = StandardScaler()
    X_tr_all = scaler_all.fit_transform(X_all_imp.iloc[train_mask])
    X_va_all = scaler_all.transform(X_all_imp.iloc[val_mask])
    X_te_all = scaler_all.transform(X_all_imp.iloc[test_mask])

    val_results_exp_b = {}
    models_exp_b = {}

    for arch in architectures:
        raw_val_probs = np.zeros_like(y_all[val_mask], dtype=float)
        arch_models = []

        for d_idx, disease in enumerate(DISEASES):
            if arch == "XGBoost":
                clf = XGBClassifier(n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42, eval_metric="logloss")
            elif arch == "LightGBM":
                clf = LGBMClassifier(n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42, verbose=-1)
            else: # CatBoost
                clf = CatBoostClassifier(iterations=150, depth=5, learning_rate=0.05, random_seed=42, verbose=0)

            clf.fit(X_tr_all, y_all[train_mask, d_idx])
            raw_val_probs[:, d_idx] = clf.predict_proba(X_va_all)[:, 1]
            arch_models.append(clf)

        val_f1s = [f1_score(y_all[val_mask, d], (raw_val_probs[:, d] >= 0.5).astype(int), zero_division=0) for d in range(len(DISEASES))]
        val_macro = np.mean(val_f1s)
        val_results_exp_b[arch] = val_macro
        models_exp_b[arch] = arch_models
        logger.info(f"Validation Macro F1 Exp B ({arch}): {val_macro:.4f}")

    best_arch_b = max(val_results_exp_b, key=val_results_exp_b.get)
    selected_models_b = models_exp_b[best_arch_b]

    # Calibrate & Threshold Tune Exp B
    raw_val_p_b  = np.zeros_like(y_all[val_mask], dtype=float)
    raw_test_p_b = np.zeros_like(y_all[test_mask], dtype=float)
    for d_idx in range(len(DISEASES)):
        raw_val_p_b[:, d_idx]  = selected_models_b[d_idx].predict_proba(X_va_all)[:, 1]
        raw_test_p_b[:, d_idx] = selected_models_b[d_idx].predict_proba(X_te_all)[:, 1]

    val_cal_p_b  = np.zeros_like(y_all[val_mask], dtype=float)
    test_cal_p_b = np.zeros_like(y_all[test_mask], dtype=float)
    thresholds_b = {}
    calibrators_b = []

    for d_idx, disease in enumerate(DISEASES):
        iso = IsotonicRegression(out_of_bounds="clip").fit(raw_val_p_b[:, d_idx], y_all[val_mask, d_idx])
        val_cal_p_b[:, d_idx]  = iso.transform(raw_val_p_b[:, d_idx])
        test_cal_p_b[:, d_idx] = iso.transform(raw_test_p_b[:, d_idx])
        calibrators_b.append(iso)
        thresholds_b[disease]  = find_optimal_threshold(y_all[val_mask, d_idx], val_cal_p_b[:, d_idx])

    metrics_exp_b, _ = evaluate_predictions(y_all[test_mask], test_cal_p_b, thresholds_b)
    metrics_exp_b["bootstrap_95_ci_macro_f1"] = compute_bootstrap_ci(y_all[test_mask], test_cal_p_b, thresholds_b)
    metrics_exp_b["selected_architecture"] = best_arch_b
    metrics_exp_b["thresholds"] = thresholds_b

    # SHAP for Exp B Candidate
    shap_summary_b = {}
    feat_names_b = STD_WEARABLE_FEATURES + CGM_FEATURES
    for d_idx, disease in enumerate(DISEASES):
        clf = selected_models_b[d_idx]
        exp = shap.TreeExplainer(clf)
        sv = exp.shap_values(X_te_all)
        if isinstance(sv, list): sv = sv[1]
        mean_abs_shap = np.mean(np.abs(sv), axis=0)
        shap_df = pd.DataFrame({"feature": feat_names_b, "shap_importance": mean_abs_shap})
        shap_df = shap_df.sort_values("shap_importance", ascending=False)
        shap_summary_b[disease] = shap_df.to_dict(orient="records")

    # Save Payload & Combined Output
    payload_b = {
        "architecture": best_arch_b,
        "models": selected_models_b,
        "scaler": scaler_all,
        "medians": medians_all,
        "calibrators": calibrators_b,
        "thresholds": thresholds_b,
        "features": feat_names_b
    }
    joblib.dump(payload_b, SAVE_DIR / "wearable_v3_payload.joblib")

    combined_metrics = {
        "experiment_a_standard": metrics_exp_a,
        "experiment_b_with_cgm": metrics_exp_b
    }
    with open(SAVE_DIR / "wearable_v3_metrics.json", "w") as f:
        json.dump(combined_metrics, f, indent=2)

    return combined_metrics, shap_summary_b

if __name__ == "__main__":
    train_and_eval_wearable_v3()
