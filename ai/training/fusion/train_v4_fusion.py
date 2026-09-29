"""
train_v4_fusion.py — Sprint 24 V4 Multimodal Fusion Engine & Stacking Experiments

Builds, tunes, benchmarks, and evaluates Multimodal Stacking Fusion models across 7 modality combinations 
and 5 target diseases on the validated V4 cohort (N=100,000) using frozen expert models.

Protocol & Leakage Prevention:
1. Out-of-Fold (OOF) Expert Predictions generated for Train split (70k) via 5-Fold Stratified CV.
2. Meta-learner candidate evaluation (LogisticRegression, LightGBM, XGBoost) on Validation split (15k).
3. Final evaluation of frozen winning fusion models on untouched Test split (15k) with 95% Bootstrap CIs.
4. Stepwise Ablation Study (C -> C+W -> C+G -> C+W+G).
5. Paired Statistical Significance Testing (Clinical vs C+W+G Fusion).
6. Explainability & Relative Modality Contribution Weights.
7. Persistence into fusion_engine/v4_artifacts/v4_multimodal_fusion_payload.joblib.
"""

import sys
import os
import json
import math
import time
import hashlib
import platform
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score, average_precision_score, accuracy_score, precision_score,
    recall_score, f1_score, brier_score_loss, confusion_matrix
)
from sklearn.model_selection import StratifiedKFold
from sklearn.inspection import permutation_importance
import lightgbm as lgb
from lightgbm import LGBMClassifier
import xgboost as xgb
from xgboost import XGBClassifier
import catboost as cb
from catboost import CatBoostClassifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("train_v4_fusion")

DATA_DIR = Path("ai/datasets/final")
EXPERT_DIR = Path("expert_models/v4_artifacts")
SAVE_DIR = Path("fusion_engine/v4_artifacts")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

SEED = 20260808
np.random.seed(SEED)

DISEASES = ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]

COMBINATIONS = [
    ("Clinical_Only", ["Clinical"]),
    ("Wearable_Only", ["Wearable"]),
    ("Gut_Only", ["Gut"]),
    ("Clinical_Wearable", ["Clinical", "Wearable"]),
    ("Clinical_Gut", ["Clinical", "Gut"]),
    ("Wearable_Gut", ["Wearable", "Gut"]),
    ("Full_Multimodal_Fusion", ["Clinical", "Wearable", "Gut"])
]

def compute_bootstrap_ci(y_true, y_prob, n_bootstraps=500, confidence=0.95):
    """Computes 95% Bootstrap Confidence Interval for ROC-AUC and PR-AUC on Test Set."""
    boot_aucroc, boot_aucpr = [], []
    n = len(y_true)
    rng = np.random.default_rng(SEED)

    for _ in range(n_bootstraps):
        idx = rng.choice(n, size=n, replace=True)
        if len(np.unique(y_true[idx])) < 2:
            continue
        boot_aucroc.append(roc_auc_score(y_true[idx], y_prob[idx]))
        boot_aucpr.append(average_precision_score(y_true[idx], y_prob[idx]))

    alpha = (1.0 - confidence) / 2.0
    roc_low = float(np.percentile(boot_aucroc, alpha * 100))
    roc_high = float(np.percentile(boot_aucroc, (1.0 - alpha) * 100))

    pr_low = float(np.percentile(boot_aucpr, alpha * 100))
    pr_high = float(np.percentile(boot_aucpr, (1.0 - alpha) * 100))

    return (roc_low, roc_high), (pr_low, pr_high)

def paired_bootstrap_test(y_true, probs_baseline, probs_fusion, n_bootstraps=1000):
    """Performs paired bootstrap hypothesis test to check if Fusion AUROC improvement is statistically significant."""
    n = len(y_true)
    rng = np.random.default_rng(SEED)
    diffs = []
    
    auc_base = roc_auc_score(y_true, probs_baseline)
    auc_fuse = roc_auc_score(y_true, probs_fusion)
    obs_diff = auc_fuse - auc_base

    for _ in range(n_bootstraps):
        idx = rng.choice(n, size=n, replace=True)
        if len(np.unique(y_true[idx])) < 2:
            continue
        b_base = roc_auc_score(y_true[idx], probs_baseline[idx])
        b_fuse = roc_auc_score(y_true[idx], probs_fusion[idx])
        diffs.append(b_fuse - b_base)

    diffs = np.array(diffs)
    # Two-tailed p-value
    p_value = float(np.mean(np.abs(diffs - np.mean(diffs)) >= np.abs(obs_diff)))
    return obs_diff, float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5)), max(1e-4, p_value)

def generate_oof_expert_predictions(expert_payload, mod_df, meta_df, lbl_df):
    """Generates Out-Of-Fold (OOF) predictions for Train split and standard predictions for Val and Test."""
    tr_mask  = (meta_df["Split"] == "Train").values
    val_mask = (meta_df["Split"] == "Val").values
    te_mask  = (meta_df["Split"] == "Test").values

    feats = expert_payload["features"]
    medians = pd.Series(expert_payload["medians"])
    scaler = expert_payload["scalers"]

    X_tr_raw  = mod_df.loc[tr_mask, feats].copy()
    X_val_raw = mod_df.loc[val_mask, feats].copy()
    X_te_raw  = mod_df.loc[te_mask, feats].copy()

    X_tr_imp  = X_tr_raw.fillna(medians)
    X_val_imp = X_val_raw.fillna(medians)
    X_te_imp  = X_te_raw.fillna(medians)

    X_tr_scaled  = pd.DataFrame(scaler.transform(X_tr_imp), columns=feats)
    X_val_scaled = pd.DataFrame(scaler.transform(X_val_imp), columns=feats)
    X_te_scaled  = pd.DataFrame(scaler.transform(X_te_imp), columns=feats)

    oof_preds = {d: np.zeros(tr_mask.sum()) for d in DISEASES}
    val_preds = {d: np.zeros(val_mask.sum()) for d in DISEASES}
    te_preds  = {d: np.zeros(te_mask.sum()) for d in DISEASES}

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

    for d in DISEASES:
        clf_trained = expert_payload["models"][d]
        clf_type = type(clf_trained).__name__

        # Val & Test predictions using pre-trained expert model
        X_val_in = X_val_scaled if clf_type == "LogisticRegression" else X_val_imp
        X_te_in  = X_te_scaled if clf_type == "LogisticRegression" else X_te_imp

        val_preds[d] = clf_trained.predict_proba(X_val_in)[:, 1]
        te_preds[d]  = clf_trained.predict_proba(X_te_in)[:, 1]

        # OOF Predictions on Train fold
        y_tr = lbl_df.loc[tr_mask, d].values
        for tr_idx, fold_val_idx in skf.split(X_tr_imp, y_tr):
            # Re-fit clone model on 4/5 of train split
            if clf_type == "LogisticRegression":
                clf_clone = LogisticRegression(max_iter=500, C=0.5, class_weight="balanced", random_state=SEED)
                clf_clone.fit(X_tr_scaled.iloc[tr_idx], y_tr[tr_idx])
                oof_preds[d][fold_val_idx] = clf_clone.predict_proba(X_tr_scaled.iloc[fold_val_idx])[:, 1]
            elif clf_type == "XGBClassifier":
                pos_w = (len(tr_idx) - y_tr[tr_idx].sum()) / max(1, y_tr[tr_idx].sum())
                clf_clone = XGBClassifier(n_estimators=50, learning_rate=0.05, max_depth=4, subsample=0.85, colsample_bytree=0.85, scale_pos_weight=pos_w, random_state=SEED, n_jobs=-1, eval_metric="logloss")
                clf_clone.fit(X_tr_imp.iloc[tr_idx], y_tr[tr_idx])
                oof_preds[d][fold_val_idx] = clf_clone.predict_proba(X_tr_imp.iloc[fold_val_idx])[:, 1]
            elif clf_type == "CatBoostClassifier":
                pos_w = (len(tr_idx) - y_tr[tr_idx].sum()) / max(1, y_tr[tr_idx].sum())
                clf_clone = CatBoostClassifier(iterations=50, learning_rate=0.05, depth=4, scale_pos_weight=pos_w, random_seed=SEED, verbose=0, thread_count=-1)
                clf_clone.fit(X_tr_imp.iloc[tr_idx], y_tr[tr_idx])
                oof_preds[d][fold_val_idx] = clf_clone.predict_proba(X_tr_imp.iloc[fold_val_idx])[:, 1]

    return oof_preds, val_preds, te_preds

def train_and_evaluate_v4_fusion():
    logger.info("==================================================================")
    logger.info(" SPRINT 24 — V4 MULTIMODAL FUSION ENGINE & EXPERIMENTAL BENCHMARK ")
    logger.info("==================================================================")

    # 1. Load Data & Expert Payloads
    logger.info("[1/7] Loading V4 Datasets and Frozen Expert Payloads...")
    clin_df = pd.read_csv(DATA_DIR / "clinical_v4.csv")
    wear_df = pd.read_csv(DATA_DIR / "wearable_v4.csv")
    gut_df  = pd.read_csv(DATA_DIR / "gut_v4.csv")
    lbl_df  = pd.read_csv(DATA_DIR / "labels_v4.csv")
    meta_df = pd.read_csv(DATA_DIR / "patient_metadata_v4.csv")

    clin_payload = joblib.load(EXPERT_DIR / "clinical_v4_expert_payload.joblib")
    wear_payload = joblib.load(EXPERT_DIR / "wearable_v4_expert_payload.joblib")
    gut_payload  = joblib.load(EXPERT_DIR / "gut_v4_expert_payload.joblib")

    tr_mask  = (meta_df["Split"] == "Train").values
    val_mask = (meta_df["Split"] == "Val").values
    te_mask  = (meta_df["Split"] == "Test").values

    # 2. Generate Leakage-Free OOF & Test Expert Prediction Vectors
    logger.info("[2/7] Generating Out-Of-Fold (OOF) Leakage-Free Expert Probability Matrices...")
    clin_oof, clin_val, clin_te = generate_oof_expert_predictions(clin_payload, clin_df, meta_df, lbl_df)
    wear_oof, wear_val, wear_te = generate_oof_expert_predictions(wear_payload, wear_df, meta_df, lbl_df)
    gut_oof,  gut_val,  gut_te  = generate_oof_expert_predictions(gut_payload,  gut_df,  meta_df, lbl_df)

    expert_preds = {
        "Clinical": {"oof": clin_oof, "val": clin_val, "test": clin_te},
        "Wearable": {"oof": wear_oof, "val": wear_val, "test": wear_te},
        "Gut":      {"oof": gut_oof,  "val": gut_val,  "test": gut_te}
    }

    meta_comparison_records = []
    final_test_records = []
    winning_fusion_payload = {"meta_models": {}, "scalers": {}, "thresholds": {}, "disease_metrics": {}}
    modality_weights_summary = {}
    ablation_records = []
    stat_test_records = []

    logger.info("\n==================================================================")
    logger.info("   TRAINING & BENCHMARKING FUSION META-LEARNERS (7 COMBINATIONS)  ")
    logger.info("==================================================================")

    for d in DISEASES:
        logger.info(f"\n==================================================================")
        logger.info(f"             TARGET DISEASE: {d.upper()}                          ")
        logger.info(f"==================================================================")

        y_tr  = lbl_df.loc[tr_mask, d].values
        y_val = lbl_df.loc[val_mask, d].values
        y_te  = lbl_df.loc[te_mask, d].values

        best_full_fusion_test_probs = None
        clinical_only_test_probs = None

        for comb_name, mods in COMBINATIONS:
            # Construct Meta-Feature DataFrames from Expert Probabilities
            X_meta_tr  = pd.DataFrame({m: expert_preds[m]["oof"][d]  for m in mods})
            X_meta_val = pd.DataFrame({m: expert_preds[m]["val"][d]  for m in mods})
            X_meta_te  = pd.DataFrame({m: expert_preds[m]["test"][d] for m in mods})

            # Meta-feature Scaler
            scaler_meta = StandardScaler()
            X_meta_tr_s  = pd.DataFrame(scaler_meta.fit_transform(X_meta_tr), columns=mods)
            X_meta_val_s = pd.DataFrame(scaler_meta.transform(X_meta_val), columns=mods)
            X_meta_te_s  = pd.DataFrame(scaler_meta.transform(X_meta_te), columns=mods)

            pos_w = float((len(y_tr) - y_tr.sum()) / max(1, y_tr.sum()))

            # Define Candidate Meta-Learners
            candidate_meta_learners = {
                "LogisticRegression": LogisticRegression(max_iter=500, C=1.0, class_weight="balanced", random_state=SEED),
                "LightGBM": LGBMClassifier(n_estimators=40, learning_rate=0.05, max_depth=3, scale_pos_weight=pos_w, random_state=SEED, n_jobs=-1, verbose=-1),
                "XGBoost": XGBClassifier(n_estimators=40, learning_rate=0.05, max_depth=3, scale_pos_weight=pos_w, random_state=SEED, n_jobs=-1, eval_metric="logloss")
            }

            best_meta_score = -1.0
            best_meta_name  = None
            best_meta_obj   = None
            best_meta_val_metrics = {}

            # Evaluate Candidate Meta-Learners on Validation Set
            for ml_name, ml_clf in candidate_meta_learners.items():
                start_t = time.time()
                X_tr_in  = X_meta_tr_s if ml_name == "LogisticRegression" else X_meta_tr
                X_val_in = X_meta_val_s if ml_name == "LogisticRegression" else X_meta_val

                ml_clf.fit(X_tr_in, y_tr)
                val_probs = ml_clf.predict_proba(X_val_in)[:, 1]

                val_aucroc = float(roc_auc_score(y_val, val_probs))
                val_aucpr  = float(average_precision_score(y_val, val_probs))
                val_score  = 0.50 * val_aucroc + 0.50 * val_aucpr
                fit_time   = round(time.time() - start_t, 2)

                meta_comparison_records.append({
                    "Disease_Target": d,
                    "Combination": comb_name,
                    "Meta_Learner": ml_name,
                    "Val_AUROC": round(val_aucroc, 4),
                    "Val_AUPRC": round(val_aucpr, 4),
                    "Val_Selection_Score": round(val_score, 4),
                    "Fit_Time_Sec": fit_time
                })

                if val_score > best_meta_score:
                    best_meta_score   = val_score
                    best_meta_name    = ml_name
                    best_meta_obj     = ml_clf
                    best_meta_val_metrics = {"val_aucroc": val_aucroc, "val_aucpr": val_aucpr, "selection_score": val_score}

            # ----------------------------------------------------------
            # TEST EVALUATION ON UNTOUCHED TEST SET (15,000 Patients)
            # ----------------------------------------------------------
            X_te_in = X_meta_te_s if best_meta_name == "LogisticRegression" else X_meta_te
            test_probs = best_meta_obj.predict_proba(X_te_in)[:, 1]

            if comb_name == "Clinical_Only":
                clinical_only_test_probs = test_probs
            elif comb_name == "Full_Multimodal_Fusion":
                best_full_fusion_test_probs = test_probs
                winning_fusion_payload["meta_models"][d] = best_meta_obj
                winning_fusion_payload["scalers"][d] = scaler_meta

            # Optimal Decision Threshold on Val set
            X_val_in = X_meta_val_s if best_meta_name == "LogisticRegression" else X_meta_val
            val_preds_raw = best_meta_obj.predict_proba(X_val_in)[:, 1]
            best_t = 0.50
            best_f1_val = 0.0
            for thresh in np.linspace(0.15, 0.85, 71):
                f1_t = f1_score(y_val, (val_preds_raw >= thresh).astype(int), zero_division=0)
                if f1_t > best_f1_val:
                    best_f1_val = f1_t
                    best_t = thresh

            if comb_name == "Full_Multimodal_Fusion":
                winning_fusion_payload["thresholds"][d] = float(best_t)

            test_preds_binary = (test_probs >= best_t).astype(int)

            test_aucroc = float(roc_auc_score(y_te, test_probs))
            test_aucpr  = float(average_precision_score(y_te, test_probs))
            test_acc    = float(accuracy_score(y_te, test_preds_binary))
            test_prec   = float(precision_score(y_te, test_preds_binary, zero_division=0))
            test_rec    = float(recall_score(y_te, test_preds_binary, zero_division=0))
            test_f1     = float(f1_score(y_te, test_preds_binary, zero_division=0))
            test_brier  = float(brier_score_loss(y_te, test_probs))

            cm = confusion_matrix(y_te, test_preds_binary)
            tn, fp, fn, tp = cm.ravel()
            spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0

            (roc_ci_low, roc_ci_high), (pr_ci_low, pr_ci_high) = compute_bootstrap_ci(y_te, test_probs)

            final_test_records.append({
                "Disease_Target": d,
                "Combination": comb_name,
                "Winning_Meta_Learner": best_meta_name,
                "Optimal_Threshold": round(float(best_t), 4),
                "Test_AUROC": round(test_aucroc, 4),
                "Test_AUROC_95CI": f"[{roc_ci_low:.4f}, {roc_ci_high:.4f}]",
                "Test_AUPRC": round(test_aucpr, 4),
                "Test_AUPRC_95CI": f"[{pr_ci_low:.4f}, {pr_ci_high:.4f}]",
                "Test_Accuracy": round(test_acc, 4),
                "Test_Precision": round(test_prec, 4),
                "Test_Sensitivity": round(test_rec, 4),
                "Test_Specificity": round(spec, 4),
                "Test_F1_Score": round(test_f1, 4),
                "Test_Brier_Score": round(test_brier, 4)
            })

            logger.info(f"  {comb_name:24s} ({best_meta_name:18s}) -> Test AUROC: {test_aucroc:.4f} [{roc_ci_low:.4f}, {roc_ci_high:.4f}] | F1: {test_f1:.4f}")

            # Record Ablation Step
            if comb_name in ["Clinical_Only", "Clinical_Wearable", "Clinical_Gut", "Full_Multimodal_Fusion"]:
                ablation_records.append({
                    "Disease_Target": d,
                    "Modality_Step": comb_name,
                    "Test_AUROC": round(test_aucroc, 4),
                    "Test_AUPRC": round(test_aucpr, 4)
                })

        # Relative Modality Importance Weights for Full Multimodal Fusion
        full_meta_model = winning_fusion_payload["meta_models"][d]
        if hasattr(full_meta_model, "coef_"):
            weights_raw = np.abs(full_meta_model.coef_[0])
        elif hasattr(full_meta_model, "feature_importances_"):
            weights_raw = full_meta_model.feature_importances_
        else:
            weights_raw = np.array([0.333, 0.333, 0.334])

        weights_norm = weights_raw / np.sum(weights_raw)
        modality_weights_summary[d] = {
            "Clinical": round(float(weights_norm[0]), 4),
            "Wearable": round(float(weights_norm[1]), 4),
            "Gut":      round(float(weights_norm[2]), 4)
        }

        # Paired Statistical Significance Test: Clinical vs Full Fusion
        obs_diff, ci_low, ci_high, p_val = paired_bootstrap_test(y_te, clinical_only_test_probs, best_full_fusion_test_probs)
        stat_test_records.append({
            "Disease_Target": d,
            "Clinical_AUROC": round(float(roc_auc_score(y_te, clinical_only_test_probs)), 4),
            "Full_Fusion_AUROC": round(float(roc_auc_score(y_te, best_full_fusion_test_probs)), 4),
            "Absolute_AUROC_Gain": round(float(obs_diff), 4),
            "Gain_95CI": f"[{ci_low:.4f}, {ci_high:.4f}]",
            "p_value": round(p_val, 4),
            "Is_Statistically_Significant": "YES (p < 0.05)" if p_val < 0.05 else "NO (p >= 0.05)"
        })

    # ------------------------------------------------------------------
    # SAVE FUSION ARTIFACTS
    # ------------------------------------------------------------------
    logger.info("\n[6/7] Exporting Multimodal Fusion Models & Benchmark Reports...")
    payload_file = SAVE_DIR / "v4_multimodal_fusion_payload.joblib"
    joblib.dump(winning_fusion_payload, payload_file)
    logger.info(f"  Saved payload: {payload_file}")

    pd.DataFrame(meta_comparison_records).to_csv(SAVE_DIR / "v4_fusion_meta_learner_comparison.csv", index=False)
    pd.DataFrame(final_test_records).to_csv(SAVE_DIR / "v4_fusion_test_metrics_with_95ci.csv", index=False)
    pd.DataFrame(ablation_records).to_csv(SAVE_DIR / "v4_fusion_ablation_study.csv", index=False)
    pd.DataFrame(stat_test_records).to_csv(SAVE_DIR / "v4_fusion_statistical_significance.csv", index=False)

    with open(SAVE_DIR / "v4_fusion_modality_weights.json", "w") as f:
        json.dump(modality_weights_summary, f, indent=2)

    logger.info("[7/7] Sprint 24 Multimodal Fusion Training & Validation Complete!")
    return winning_fusion_payload, final_test_records, stat_test_records

if __name__ == "__main__":
    train_and_evaluate_v4_fusion()
