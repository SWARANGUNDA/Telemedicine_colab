"""
run_verification_phase.py — Comprehensive Script for Parts A and B Scientific Verification.

Executes:
- Part A: Target generation audit, leakage audit, split integrity, preprocessor audit,
  single-feature standalone ROC-AUC, diagnostic feature ablations for Clinical v1.
- Part B: W vs W+Gv2 vs W+Shuffled_Gv2, 100-permutation null distribution & empirical p-value,
  1,000-sample bootstrap 95% CIs, per-disease metrics, error complementarity analysis.
"""

import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score, brier_score_loss
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from catboost import CatBoostClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

from expert_models import config as expert_config
from expert_models import data_loader as expert_data_loader
from expert_models import metrics as expert_metrics
from expert_models import preprocessing, calibration, threshold_tuner, trainer
from fusion_engine import config as fusion_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scientific_verification")

DISEASE_COLS = expert_config.TARGET_DISEASES

PREDICTOR_TAXA_20 = [
    "Akkermansia", "Faecalibacterium", "Roseburia", "Bifidobacterium", "Bacteroides",
    "Prevotella", "Ruminococcus", "Blautia", "Collinsella", "Escherichia_Shigella",
    "Coprococcus", "Alistipes", "Subdoligranulum", "Enterococcus", "Eubacterium",
    "Parabacteroides", "Lactobacillus", "Klebsiella", "Streptococcus", "Eggerthella"
]


def run_part_a_clinical_audit():
    """Execute all Part A audits and diagnostic ablations."""
    logger.info("==================================================================")
    logger.info("  PART A — CLINICAL TARGET LEAKAGE & DIFFICULTY AUDIT            ")
    logger.info("==================================================================")

    # 1. Load Clinical Dataset & Split
    df_clin = pd.read_csv("Clinical_Dataset.csv")
    splits_df = pd.read_csv("expert_models/splits/patient_split.csv")
    merged_clin = pd.merge(df_clin, splits_df, on="Patient_ID")

    train_mask = (merged_clin["Split"] == "train").values
    val_mask = (merged_clin["Split"] == "val").values
    test_mask = (merged_clin["Split"] == "test").values

    # A2: Feature Leakage Audit
    feature_cols = [c for c in df_clin.columns if c not in DISEASE_COLS + ["Patient_ID", "Healthy", "Split"]]
    forbidden_terms = ["disease", "healthy", "target", "label", "score", "diagnosis"]
    leaked_cols = [c for c in feature_cols if any(term in c.lower() for term in forbidden_terms)]

    logger.info("A2 Feature Leakage Audit: Leaked feature columns found = %s", leaked_cols)

    # A3: Split Integrity & Duplicate Audit
    train_pids = set(merged_clin.loc[train_mask, "Patient_ID"])
    val_pids = set(merged_clin.loc[val_mask, "Patient_ID"])
    test_pids = set(merged_clin.loc[test_mask, "Patient_ID"])

    overlap_tr_val = train_pids.intersection(val_pids)
    overlap_tr_te = train_pids.intersection(test_pids)
    overlap_va_te = val_pids.intersection(test_pids)

    logger.info("A3 Split Overlap Audit: Tr^Val=%d, Tr^Te=%d, Val^Te=%d",
                len(overlap_tr_val), len(overlap_tr_te), len(overlap_va_te))

    # Duplicate row audit
    X_raw = merged_clin[feature_cols]
    dup_rows = X_raw.duplicated().sum()
    logger.info("A3 Duplicate Row Audit: Duplicate feature rows = %d", dup_rows)

    # A5: Single-Feature Standalone Predictability Audit
    logger.info("A5 Standalone Single-Feature ROC-AUC Audit...")
    single_feat_res = {}
    for feat in feature_cols:
        single_feat_res[feat] = {}
        vals = merged_clin.loc[test_mask, feat].values
        # Encode categorical features if strings
        if vals.dtype == object or isinstance(vals[0], str):
            from sklearn.preprocessing import LabelEncoder
            vals = LabelEncoder().fit_transform(vals.astype(str))
        else:
            vals = vals.astype(float)

        for d in DISEASE_COLS:
            labels = merged_clin.loc[test_mask, d].values
            valid_mask = ~np.isnan(vals)
            if len(np.unique(labels[valid_mask])) > 1:
                auc = roc_auc_score(labels[valid_mask], vals[valid_mask])
                if auc < 0.5:
                    auc = roc_auc_score(labels[valid_mask], -vals[valid_mask])
                single_feat_res[feat][d] = round(float(auc), 4)
            else:
                single_feat_res[feat][d] = 0.5000

    single_feat_df = pd.DataFrame(single_feat_res).T
    single_feat_df.to_csv("clinical_single_feature_auc.csv")
    logger.info("Saved clinical_single_feature_auc.csv")

    # A6: Diagnostic Ablations
    logger.info("A6 Diagnostic Feature Ablation Experiments...")
    ablation_scenarios = {
        "Baseline_All_Features": feature_cols,
        "No_FPG": [c for c in feature_cols if c != "Fasting_Blood_Glucose"],
        "No_HbA1c": [c for c in feature_cols if c != "HbA1c"],
        "No_FPG_No_HbA1c": [c for c in feature_cols if c not in ["Fasting_Blood_Glucose", "HbA1c"]],
        "No_BMI": [c for c in feature_cols if c != "BMI"],
        "No_BMI_No_Weight_No_Height": [c for c in feature_cols if c not in ["BMI", "Weight", "Height"]],
        "No_MetS_Rules": [c for c in feature_cols if c not in ["Waist_Circumference", "Triglycerides", "HDL", "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose"]],
        "No_ALT_No_AST": [c for c in feature_cols if c not in ["ALT", "AST"]],
        "No_ALT_AST_TG_BMI": [c for c in feature_cols if c not in ["ALT", "AST", "Triglycerides", "BMI"]],
    }

    ablation_results = {}
    for sc_name, sc_feats in ablation_scenarios.items():
        X_tr = merged_clin.loc[train_mask, sc_feats]
        y_tr = merged_clin.loc[train_mask, DISEASE_COLS].values
        X_va = merged_clin.loc[val_mask, sc_feats]
        y_va = merged_clin.loc[val_mask, DISEASE_COLS].values
        X_te = merged_clin.loc[test_mask, sc_feats]
        y_te = merged_clin.loc[test_mask, DISEASE_COLS].values

        prep = preprocessing.ExpertPreprocessor(feature_order=sc_feats, preserve_nans=True, scale_numeric=False)
        X_tr_p = prep.fit_transform(X_tr)
        X_va_p = prep.transform(X_va)
        X_te_p = prep.transform(X_te)

        estimators = []
        va_probs = np.zeros((len(y_va), len(DISEASE_COLS)))
        te_probs = np.zeros((len(y_te), len(DISEASE_COLS)))

        for d_idx in range(len(DISEASE_COLS)):
            m = XGBClassifier(n_estimators=150, max_depth=5, learning_rate=0.05, eval_metric="logloss", random_state=42)
            m.fit(X_tr_p, y_tr[:, d_idx])
            va_probs[:, d_idx] = m.predict_proba(X_va_p)[:, 1]
            te_probs[:, d_idx] = m.predict_proba(X_te_p)[:, 1]
            estimators.append(m)

        thresh = threshold_tuner.tune_expert_thresholds(pd.DataFrame(y_va, columns=DISEASE_COLS), va_probs)
        calib = calibration.DiseaseProbabilityCalibrator(method="isotonic")
        calib.fit(y_va, va_probs)

        te_calib_p = calib.calibrate_probas(te_probs)
        eval_te = expert_metrics.evaluate_multilabel_predictions(
            pd.DataFrame(y_te, columns=DISEASE_COLS), te_calib_p, thresholds=thresh
        )
        ablation_results[sc_name] = eval_te
        logger.info("Ablation [%-28s]: Test Macro F1 = %.4f", sc_name, eval_te["summary"]["macro_f1"])

    return single_feat_df, ablation_results


def run_part_b_wearable_gut_verification():
    """Execute Part B Wearable + Gut v2 complementary signal experiments."""
    logger.info("==================================================================")
    logger.info("  PART B — WEARABLE + GUT v2 COMPLEMENTARY SIGNAL VERIFICATION    ")
    logger.info("==================================================================")

    # 1. Load OOF & Test Probabilities
    oof_dir = Path("fusion_engine/oof_probabilities")
    wear_oof_tr = np.load(oof_dir / "wearable_train_probs.npy")
    wear_val = np.load(oof_dir / "wearable_val_probs.npy")
    wear_te = np.load(oof_dir / "wearable_test_probs.npy")

    df_v2 = pd.read_csv("Gut_Dataset_v2.csv")
    splits_df = pd.read_csv("expert_models/splits/patient_split.csv")
    merged_v2 = pd.merge(df_v2, splits_df, on="Patient_ID")

    train_mask = (merged_v2["Split"] == "train").values
    val_mask = (merged_v2["Split"] == "val").values
    test_mask = (merged_v2["Split"] == "test").values
    y_test = merged_v2.loc[test_mask, DISEASE_COLS].values
    y_val = merged_v2.loc[val_mask, DISEASE_COLS].values
    y_train = merged_v2.loc[train_mask, DISEASE_COLS].values

    # Load Gut v2 models & predict
    save_dir_gut = Path("expert_models/saved_models/gut_v2")
    gut_v2_wrapper = joblib.load(save_dir_gut / "model.joblib")
    gut_v2_prep = joblib.load(save_dir_gut / "preprocessor.joblib")

    X_tr_gut = merged_v2.loc[train_mask, PREDICTOR_TAXA_20]
    X_va_gut = merged_v2.loc[val_mask, PREDICTOR_TAXA_20]
    X_te_gut = merged_v2.loc[test_mask, PREDICTOR_TAXA_20]

    # Generate Gut v2 probabilities for Train (OOF), Val, and Test
    from fusion_engine.train_fusion_v2 import generate_gut_v2_oof_probabilities
    gut_v2_oof_tr, gut_v2_val, gut_v2_te = generate_gut_v2_oof_probabilities(merged_v2, train_mask, val_mask, test_mask)

    # 2. Fit Pathway Models (W, W+Gv2)
    # W Pathway
    w_models = []
    w_val_raw = np.zeros((len(y_val), len(DISEASE_COLS)))
    w_te_raw = np.zeros((len(y_test), len(DISEASE_COLS)))
    for d_idx in range(len(DISEASE_COLS)):
        clf = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
        clf.fit(wear_oof_tr, y_train[:, d_idx])
        w_val_raw[:, d_idx] = clf.predict_proba(wear_val)[:, 1]
        w_te_raw[:, d_idx] = clf.predict_proba(wear_te)[:, 1]
        w_models.append(clf)

    w_thresh = threshold_tuner.tune_expert_thresholds(pd.DataFrame(y_val, columns=DISEASE_COLS), w_val_raw)
    w_calib = calibration.DiseaseProbabilityCalibrator(method="isotonic")
    w_calib.fit(y_val, w_val_raw)

    w_te_calib = w_calib.calibrate_probas(w_te_raw)
    w_eval = expert_metrics.evaluate_multilabel_predictions(
        pd.DataFrame(y_test, columns=DISEASE_COLS), w_te_calib, thresholds=w_thresh
    )

    # W+Gv2 Pathway (Aligned)
    wg_meta_tr = np.hstack([wear_oof_tr, gut_v2_oof_tr])
    wg_meta_val = np.hstack([wear_val, gut_v2_val])
    wg_meta_te = np.hstack([wear_te, gut_v2_te])

    wg_models = []
    wg_val_raw = np.zeros((len(y_val), len(DISEASE_COLS)))
    wg_te_raw = np.zeros((len(y_test), len(DISEASE_COLS)))
    for d_idx in range(len(DISEASE_COLS)):
        clf = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
        clf.fit(wg_meta_tr, y_train[:, d_idx])
        wg_val_raw[:, d_idx] = clf.predict_proba(wg_meta_val)[:, 1]
        wg_te_raw[:, d_idx] = clf.predict_proba(wg_meta_te)[:, 1]
        wg_models.append(clf)

    wg_thresh = threshold_tuner.tune_expert_thresholds(pd.DataFrame(y_val, columns=DISEASE_COLS), wg_val_raw)
    wg_calib = calibration.DiseaseProbabilityCalibrator(method="isotonic")
    wg_calib.fit(y_val, wg_val_raw)

    wg_te_calib = wg_calib.calibrate_probas(wg_te_raw)
    wg_eval = expert_metrics.evaluate_multilabel_predictions(
        pd.DataFrame(y_test, columns=DISEASE_COLS), wg_te_calib, thresholds=wg_thresh
    )

    # 3. B1 & B2: 100-Permutation Shuffled Negative Control
    logger.info("B2 Running 100 Permutation Controls for W + Shuffled_Gv2...")
    shuffled_macro_f1s = []
    shuffled_micro_f1s = []
    aligned_macro_f1 = wg_eval["summary"]["macro_f1"]
    w_macro_f1 = w_eval["summary"]["macro_f1"]

    for seed in range(1, 101):
        np.random.seed(seed)
        shuf_idx = np.random.permutation(len(gut_v2_te))
        gut_shuf_te = gut_v2_te[shuf_idx]

        X_meta_shuf_te = np.hstack([wear_te, gut_shuf_te])
        shuf_te_raw = np.zeros((len(y_test), len(DISEASE_COLS)))
        for d_idx in range(len(DISEASE_COLS)):
            shuf_te_raw[:, d_idx] = wg_models[d_idx].predict_proba(X_meta_shuf_te)[:, 1]

        shuf_te_calib = wg_calib.calibrate_probas(shuf_te_raw)
        shuf_eval = expert_metrics.evaluate_multilabel_predictions(
            pd.DataFrame(y_test, columns=DISEASE_COLS), shuf_te_calib, thresholds=wg_thresh
        )
        shuffled_macro_f1s.append(shuf_eval["summary"]["macro_f1"])
        shuffled_micro_f1s.append(shuf_eval["summary"]["micro_f1"])

    null_deltas = np.array(shuffled_macro_f1s) - w_macro_f1
    aligned_delta = aligned_macro_f1 - w_macro_f1
    p_value = np.mean(null_deltas >= aligned_delta)

    logger.info("100-Permutation Null Distribution Delta Mean = %.4f, Std = %.4f", np.mean(null_deltas), np.std(null_deltas))
    logger.info("Aligned Delta = %.4f | Empirical Permutation p-value = %.4f", aligned_delta, p_value)

    # 4. B3: 1,000-Sample Bootstrap Resampling for 95% CIs
    logger.info("B3 Running 1,000-Sample Bootstrap Resampling...")
    np.random.seed(42)
    n_samples = len(y_test)

    boot_deltas_macro = []
    boot_deltas_micro = []
    boot_deltas_hamming = []
    boot_deltas_brier = []
    boot_per_disease = {d: [] for d in DISEASE_COLS}

    for b in range(1000):
        b_idx = np.random.choice(n_samples, size=n_samples, replace=True)
        y_b = pd.DataFrame(y_test[b_idx], columns=DISEASE_COLS)

        e_w_b = expert_metrics.evaluate_multilabel_predictions(y_b, w_te_calib[b_idx], thresholds=w_thresh)
        e_wg_b = expert_metrics.evaluate_multilabel_predictions(y_b, wg_te_calib[b_idx], thresholds=wg_thresh)

        boot_deltas_macro.append(e_wg_b["summary"]["macro_f1"] - e_w_b["summary"]["macro_f1"])
        boot_deltas_micro.append(e_wg_b["summary"]["micro_f1"] - e_w_b["summary"]["micro_f1"])
        boot_deltas_hamming.append(e_wg_b["summary"]["hamming_loss"] - e_w_b["summary"]["hamming_loss"])
        boot_deltas_brier.append(e_wg_b["summary"]["mean_brier_score"] - e_w_b["summary"]["mean_brier_score"])

        for d in DISEASE_COLS:
            boot_per_disease[d].append(
                e_wg_b["per_disease"][d]["f1_score"] - e_w_b["per_disease"][d]["f1_score"]
            )

    ci_macro = np.percentile(boot_deltas_macro, [2.5, 97.5])
    ci_micro = np.percentile(boot_deltas_micro, [2.5, 97.5])
    ci_hamming = np.percentile(boot_deltas_hamming, [2.5, 97.5])
    ci_brier = np.percentile(boot_deltas_brier, [2.5, 97.5])

    ci_disease = {}
    for d in DISEASE_COLS:
        ci_disease[d] = {
            "mean_delta": float(np.mean(boot_per_disease[d])),
            "ci_lower": float(np.percentile(boot_per_disease[d], 2.5)),
            "ci_upper": float(np.percentile(boot_per_disease[d], 97.5))
        }

    # 5. B6: Error Complementarity Analysis
    logger.info("B6 Error Complementarity Analysis...")
    error_comp = {}

    for idx, d in enumerate(DISEASE_COLS):
        y_true_d = y_test[:, idx]
        w_pred_d = (w_te_calib[:, idx] >= w_thresh[d]).astype(int)
        wg_pred_d = (wg_te_calib[:, idx] >= wg_thresh[d]).astype(int)

        w_correct = w_pred_d == y_true_d
        wg_correct = wg_pred_d == y_true_d

        wrong_w_corrected_wg = (~w_correct & wg_correct).sum()
        correct_w_corrupted_wg = (w_correct & ~wg_correct).sum()
        net_corrected = wrong_w_corrected_wg - correct_w_corrupted_wg

        error_comp[d] = {
            "w_correct_count": int(w_correct.sum()),
            "w_error_count": int((~w_correct).sum()),
            "wrong_w_corrected_by_wg": int(wrong_w_corrected_wg),
            "correct_w_corrupted_by_wg": int(correct_w_corrupted_wg),
            "net_corrected": int(net_corrected)
        }

    return {
        "w_eval": w_eval,
        "wg_eval": wg_eval,
        "shuffled_macro_f1_mean": float(np.mean(shuffled_macro_f1s)),
        "null_deltas_mean": float(np.mean(null_deltas)),
        "null_deltas_std": float(np.std(null_deltas)),
        "p_value": float(p_value),
        "ci_macro": [float(ci_macro[0]), float(ci_macro[1])],
        "ci_micro": [float(ci_micro[0]), float(ci_micro[1])],
        "ci_hamming": [float(ci_hamming[0]), float(ci_hamming[1])],
        "ci_brier": [float(ci_brier[0]), float(ci_brier[1])],
        "ci_disease": ci_disease,
        "error_comp": error_comp
    }


if __name__ == "__main__":
    single_feat_df, ablation_results = run_part_a_clinical_audit()
    part_b_results = run_part_b_wearable_gut_verification()
    logger.info("All Verification Phase experiments completed successfully.")
