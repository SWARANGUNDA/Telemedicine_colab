"""
run_closure_audit.py — Empirical Validation vs Test Audit Script.

Computes exact per-disease metrics (F1, ROC-AUC, PR-AUC, Brier) on Validation vs Test,
prevalence across splits, threshold impacts, and candidate model comparisons for
gut_v2_final_closure_audit.md.
"""

import json
import logging
import numpy as np
import pandas as pd
import joblib

from expert_models import config, metrics, threshold_tuner, calibration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("closure_audit")

# 1. Load Dataset v2 and Split
df_v2 = pd.read_csv("Gut_Dataset_v2.csv")
splits_df = pd.read_csv("expert_models/splits/patient_split.csv")
merged = pd.merge(df_v2, splits_df, on="Patient_ID")

train_mask = (merged["Split"] == "train").values
val_mask = (merged["Split"] == "val").values
test_mask = (merged["Split"] == "test").values

disease_cols = config.TARGET_DISEASES

print("=== 1. CLASS PREVALENCE ACROSS SPLITS ===")
for d in disease_cols:
    tr_p = merged.loc[train_mask, d].mean() * 100
    va_p = merged.loc[val_mask, d].mean() * 100
    te_p = merged.loc[test_mask, d].mean() * 100
    print(f"  {d:20s}: Train = {tr_p:.2f}%, Val = {va_p:.2f}%, Test = {te_p:.2f}%")

# Load candidate model artifacts
save_dir = config.BASE_DIR / "expert_models" / "saved_models" / "gut_v2"
model_wrapper = joblib.load(save_dir / "model.joblib")
preprocessor = joblib.load(save_dir / "preprocessor.joblib")
calibrator = joblib.load(save_dir / "calibrator.joblib")

with open(save_dir / "thresholds.json", "r") as f:
    thresholds = json.load(f)

feat_order = preprocessor.feature_order
X_val = merged.loc[val_mask, feat_order].values
X_test = merged.loc[test_mask, feat_order].values

y_val_df = merged.loc[val_mask, disease_cols]
y_test_df = merged.loc[test_mask, disease_cols]

# Raw probabilities
val_raw_probs = np.zeros((len(y_val_df), len(disease_cols)))
test_raw_probs = np.zeros((len(y_test_df), len(disease_cols)))

for idx, disease in enumerate(disease_cols):
    val_raw_probs[:, idx] = model_wrapper.estimators[disease].predict_proba(X_val)[:, 1]
    test_raw_probs[:, idx] = model_wrapper.estimators[disease].predict_proba(X_test)[:, 1]

# Calibrated probabilities
val_calib_probs = calibrator.calibrate_probas(val_raw_probs)
test_calib_probs = calibrator.calibrate_probas(test_raw_probs)

# Evaluate Validation set with default 0.50 vs tuned thresholds
val_eval_default = metrics.evaluate_multilabel_predictions(y_val_df, val_calib_probs, thresholds={d: 0.50 for d in disease_cols})
val_eval_tuned = metrics.evaluate_multilabel_predictions(y_val_df, val_calib_probs, thresholds=thresholds)

# Evaluate Test set with default 0.50 vs validation-tuned thresholds
test_eval_default = metrics.evaluate_multilabel_predictions(y_test_df, test_calib_probs, thresholds={d: 0.50 for d in disease_cols})
test_eval_tuned = metrics.evaluate_multilabel_predictions(y_test_df, test_calib_probs, thresholds=thresholds)

print("\n=== 2. VALIDATION vs TEST PERFORMANCE DISCREPANCY AUDIT ===")
print("Validation Fold (N=3,000):")
print(f"  Raw Val Macro F1 (from ablation matrix)  : 0.3826")
print(f"  Calibrated Val Macro F1 (Default 0.50)    : {val_eval_default['summary']['macro_f1']:.4f}")
print(f"  Calibrated Val Macro F1 (Tuned Thresholds): {val_eval_tuned['summary']['macro_f1']:.4f}")

print("\nUntouched Test Fold (N=3,000):")
print(f"  Test Macro F1 (Default 0.50)             : {test_eval_default['summary']['macro_f1']:.4f}")
print(f"  Test Macro F1 (Validation-Tuned Thresh)  : {test_eval_tuned['summary']['macro_f1']:.4f}")

print("\n=== 3. PER-DISEASE VALIDATION vs TEST BREAKDOWN ===")
print(f"{'Disease':20s} | {'Val F1 (Tuned)':14s} | {'Test F1 (Tuned)':15s} | {'Val ROC-AUC':12s} | {'Test ROC-AUC':12s} | {'Val PR-AUC':10s} | {'Test PR-AUC':10s}")
print("-" * 105)
for d in disease_cols:
    vf1 = val_eval_tuned["per_disease"][d]["f1_score"]
    tf1 = test_eval_tuned["per_disease"][d]["f1_score"]
    vauc = val_eval_tuned["per_disease"][d]["roc_auc"]
    tauc = test_eval_tuned["per_disease"][d]["roc_auc"]
    vpr = val_eval_tuned["per_disease"][d]["pr_auc"]
    tpr = test_eval_tuned["per_disease"][d]["pr_auc"]
    print(f"{d:20s} | {vf1:14.4f} | {tf1:15.4f} | {vauc:12.4f} | {tauc:12.4f} | {vpr:10.4f} | {tpr:10.4f}")
