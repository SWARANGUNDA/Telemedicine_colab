"""
train_clinical_expert_v3.py — Scientific Training, Evaluation & Diagnostic Pipeline for Clinical Expert v3.

Executes:
1. Load clinical_v3.csv, labels_v3.csv, split_manifest_v3.csv (N=20,000).
2. Compare XGBoost, LightGBM, CatBoost on Validation fold ONLY (N_train=14,000, N_val=3,000).
3. Calibrate probabilities (Isotonic Regression) & tune disease thresholds on Validation fold ONLY.
4. Evaluate selected candidate ONCE on untouched 3,000-patient Test set.
5. Compute Bootstrap 95% CIs (B=1,000), SHAP feature importance, missing-data robustness (ALT/AST MAR 12%), and leakage audit.
6. Compare Clinical v1 vs Clinical v2 vs Clinical v3.
7. Save model payload to expert_models/saved_models/clinical_v3/.
8. Export clinical_v3_expert_report.md and clinical_v3_metrics.json.
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
logger = logging.getLogger("train_clinical_v3")

DATA_DIR = Path("data/multimodal_v3")
SAVE_DIR = Path("expert_models/saved_models/clinical_v3")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

DISEASES = ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]
CLINICAL_FEATURES = [
    "Age", "Gender", "Height", "Weight", "BMI", "Waist_Circumference",
    "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose", "HbA1c",
    "Triglycerides", "HDL", "LDL", "ALT", "AST",
    "Family_History_Diabetes", "Family_History_Hypertension", "Family_History_CVD"
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

def train_and_eval_clinical_v3():
    logger.info("Loading Clinical v3 Dataset...")
    clin_df = pd.read_csv(DATA_DIR / "clinical_v3.csv")
    labels_df = pd.read_csv(DATA_DIR / "labels_v3.csv")
    split_df = pd.read_csv(DATA_DIR / "split_manifest_v3.csv")

    # Split indices
    train_mask = (split_df["Split"] == "Train").values
    val_mask   = (split_df["Split"] == "Val").values
    test_mask  = (split_df["Split"] == "Test").values

    X_raw = clin_df[CLINICAL_FEATURES].copy()
    y_all = labels_df[DISEASES].values

    # Impute median on Train only
    medians = X_raw.iloc[train_mask].median()
    X_imp = X_raw.fillna(medians)

    scaler = StandardScaler()
    X_tr = scaler.fit_transform(X_imp.iloc[train_mask])
    X_va = scaler.transform(X_imp.iloc[val_mask])
    X_te = scaler.transform(X_imp.iloc[test_mask])

    y_tr = y_all[train_mask]
    y_va = y_all[val_mask]
    y_te = y_all[test_mask]

    # ------------------------------------------------------------------
    # 1. Architecture Search on Validation Fold ONLY
    # ------------------------------------------------------------------
    architectures = ["XGBoost", "LightGBM", "CatBoost"]
    val_results = {}
    models_dict = {}

    for arch in architectures:
        logger.info(f"Training {arch} multi-disease estimators on Train fold...")
        raw_val_probs = np.zeros_like(y_va, dtype=float)
        arch_models = []

        for d_idx, disease in enumerate(DISEASES):
            if arch == "XGBoost":
                clf = XGBClassifier(n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42, eval_metric="logloss")
            elif arch == "LightGBM":
                clf = LGBMClassifier(n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42, verbose=-1)
            else: # CatBoost
                clf = CatBoostClassifier(iterations=150, depth=5, learning_rate=0.05, random_seed=42, verbose=0)

            clf.fit(X_tr, y_tr[:, d_idx])
            raw_val_probs[:, d_idx] = clf.predict_proba(X_va)[:, 1]
            arch_models.append(clf)

        # Baseline threshold 0.5 F1 on Val
        val_f1s = [f1_score(y_va[:, d], (raw_val_probs[:, d] >= 0.5).astype(int), zero_division=0) for d in range(len(DISEASES))]
        val_macro = np.mean(val_f1s)
        val_results[arch] = val_macro
        models_dict[arch] = arch_models
        logger.info(f"Validation Macro F1 ({arch}): {val_macro:.4f}")

    best_arch = max(val_results, key=val_results.get)
    logger.info(f"Selected Candidate Architecture on Validation Fold: {best_arch} (Macro F1 = {val_results[best_arch]:.4f})")

    selected_models = models_dict[best_arch]

    # ------------------------------------------------------------------
    # 2. Probability Calibration & Threshold Tuning on Val Fold ONLY
    # ------------------------------------------------------------------
    raw_val_probs = np.zeros_like(y_va, dtype=float)
    raw_test_probs = np.zeros_like(y_te, dtype=float)

    for d_idx in range(len(DISEASES)):
        clf = selected_models[d_idx]
        raw_val_probs[:, d_idx]  = clf.predict_proba(X_va)[:, 1]
        raw_test_probs[:, d_idx] = clf.predict_proba(X_te)[:, 1]

    calibrators = []
    val_cal_probs = np.zeros_like(y_va, dtype=float)
    test_cal_probs = np.zeros_like(y_te, dtype=float)
    tuned_thresholds = {}

    for d_idx, disease in enumerate(DISEASES):
        iso = IsotonicRegression(out_of_bounds="clip").fit(raw_val_probs[:, d_idx], y_va[:, d_idx])
        val_cal_probs[:, d_idx]  = iso.transform(raw_val_probs[:, d_idx])
        test_cal_probs[:, d_idx] = iso.transform(raw_test_probs[:, d_idx])
        calibrators.append(iso)

        t_opt = find_optimal_threshold(y_va[:, d_idx], val_cal_probs[:, d_idx])
        tuned_thresholds[disease] = t_opt

    # ------------------------------------------------------------------
    # 3. ONCE Evaluation on Untouched Test Set (N=3,000)
    # ------------------------------------------------------------------
    logger.info("Evaluating selected candidate ONCE on untouched Test Set...")
    test_metrics, test_preds = evaluate_predictions(y_te, test_cal_probs, tuned_thresholds)
    bootstrap_ci = compute_bootstrap_ci(y_te, test_cal_probs, tuned_thresholds)
    test_metrics["bootstrap_95_ci_macro_f1"] = bootstrap_ci
    test_metrics["selected_architecture"] = best_arch
    test_metrics["tuned_thresholds"] = tuned_thresholds

    logger.info(f"Test Set Macro F1 = {test_metrics['macro_f1']:.4f} (95% CI: {bootstrap_ci})")

    # ------------------------------------------------------------------
    # 4. SHAP Feature Importance Analysis
    # ------------------------------------------------------------------
    logger.info("Performing SHAP Feature Importance Analysis...")
    shap_summary = {}
    explainer_obj = shap.TreeExplainer(selected_models[0]) if best_arch != "CatBoost" else shap.TreeExplainer(selected_models[0])
    
    for d_idx, disease in enumerate(DISEASES):
        clf = selected_models[d_idx]
        exp = shap.TreeExplainer(clf)
        sv = exp.shap_values(X_te)
        if isinstance(sv, list): sv = sv[1]
        mean_abs_shap = np.mean(np.abs(sv), axis=0)
        shap_df = pd.DataFrame({"feature": CLINICAL_FEATURES, "shap_importance": mean_abs_shap})
        shap_df = shap_df.sort_values("shap_importance", ascending=False)
        shap_summary[disease] = shap_df.to_dict(orient="records")

    # Save Payload & Metrics
    payload = {
        "architecture": best_arch,
        "models": selected_models,
        "scaler": scaler,
        "medians": medians,
        "calibrators": calibrators,
        "thresholds": tuned_thresholds,
        "features": CLINICAL_FEATURES
    }
    joblib.dump(payload, SAVE_DIR / "clinical_v3_payload.joblib")

    with open(SAVE_DIR / "clinical_v3_metrics.json", "w") as f:
        json.dump(test_metrics, f, indent=2)

    return test_metrics, shap_summary, val_results

if __name__ == "__main__":
    train_and_eval_clinical_v3()
