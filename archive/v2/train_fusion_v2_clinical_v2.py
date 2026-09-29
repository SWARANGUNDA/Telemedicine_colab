"""
train_fusion_v2_clinical_v2.py — Experimental Multimodal Fusion v2 Pipeline.

Evaluates multimodal complementarity across:
- Cv2 (Clinical v2)
- Wv1 (Wearable v1)
- Gv2 (Gut v2 Set B)
- Cv2 + Wv1
- Cv2 + Gv2
- Wv1 + Gv2
- Cv2 + Wv1 + Gv2

Uses 5-Fold Stratified K-Fold CV OOF probabilities generated on Train (14,000),
tunes thresholds & calibrators on Validation (3,000), and evaluates untouched
Test (3,000) ONCE. Includes 100-permutation negative controls and 1,000 bootstrap CIs.
"""

import os
import json
import logging
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import (
    f1_score, precision_score, recall_score, roc_auc_score,
    precision_recall_curve, auc, brier_score_loss, hamming_loss
)
from catboost import CatBoostClassifier
from xgboost import XGBClassifier

from expert_models.preprocessing import ExpertPreprocessor
from expert_models.threshold_tuner import find_optimal_threshold_for_disease
from expert_models import config as expert_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("fusion_v2_trainer")

DISEASE_COLS = expert_config.TARGET_DISEASES

CLINICAL_V2_COLS = [
    "Age", "Gender", "Height", "Weight", "BMI", "Waist_Circumference",
    "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose", "HbA1c",
    "Triglycerides", "HDL", "LDL", "ALT", "AST",
    "Family_History_Diabetes", "Family_History_Hypertension", "Family_History_CVD"
]

WEARABLE_COLS = [
    "Average_Daily_Steps", "Active_Minutes", "Sedentary_Time_Minutes",
    "Resting_Heart_Rate", "Sleep_Duration", "Calories_Burned",
    "Average_Glucose", "Glucose_Variability", "Time_In_Range", "Time_Above_Range"
]

PREDICTOR_TAXA_20 = [
    "Akkermansia", "Faecalibacterium", "Roseburia", "Bifidobacterium", "Bacteroides",
    "Prevotella", "Ruminococcus", "Blautia", "Collinsella", "Escherichia_Shigella",
    "Coprococcus", "Alistipes", "Subdoligranulum", "Enterococcus", "Eubacterium",
    "Parabacteroides", "Lactobacillus", "Klebsiella", "Streptococcus", "Eggerthella"
]


def compute_pr_auc(y_true, y_prob):
    p, r, _ = precision_recall_curve(y_true, y_prob)
    return float(auc(r, p))


def generate_oof_predictions():
    logger.info("--- Step 1: Generating OOF Predictions on Train Fold (N=14,000) ---")
    
    clin_v2_df = pd.read_csv("Clinical_Dataset_v2.csv")
    wear_df    = pd.read_csv("Wearable_Dataset.csv")
    gut_v2_df  = pd.read_csv("Gut_Dataset_v2.csv")

    n_train = 14000
    n_val   = 3000
    n_test  = 3000

    # Fit preprocessors on Train split
    prep_c = ExpertPreprocessor(feature_order=CLINICAL_V2_COLS)
    X_clin = prep_c.fit_transform(clin_v2_df[CLINICAL_V2_COLS])

    prep_w = ExpertPreprocessor(feature_order=WEARABLE_COLS)
    X_wear = prep_w.fit_transform(wear_df[WEARABLE_COLS])

    X_gut = gut_v2_df[PREDICTOR_TAXA_20].values

    y_all = clin_v2_df[DISEASE_COLS].values

    # Train / Val / Test slices
    X_tr_c, X_va_c, X_te_c = X_clin[:n_train], X_clin[n_train:n_train+n_val], X_clin[n_train+n_val:]
    X_tr_w, X_va_w, X_te_w = X_wear[:n_train], X_wear[n_train:n_train+n_val], X_wear[n_train+n_val:]
    X_tr_g, X_va_g, X_te_g = X_gut[:n_train], X_gut[n_train:n_train+n_val], X_gut[n_train+n_val:]

    y_tr, y_va, y_te = y_all[:n_train], y_all[n_train:n_train+n_val], y_all[n_train+n_val:]

    oof_c = np.zeros((n_train, len(DISEASE_COLS)))
    oof_w = np.zeros((n_train, len(DISEASE_COLS)))
    oof_g = np.zeros((n_train, len(DISEASE_COLS)))

    val_c = np.zeros((n_val, len(DISEASE_COLS)))
    val_w = np.zeros((n_val, len(DISEASE_COLS)))
    val_g = np.zeros((n_val, len(DISEASE_COLS)))

    test_c = np.zeros((n_test, len(DISEASE_COLS)))
    test_w = np.zeros((n_test, len(DISEASE_COLS)))
    test_g = np.zeros((n_test, len(DISEASE_COLS)))

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    for d_idx, disease in enumerate(DISEASE_COLS):
        # Clinical v2: XGBoost
        # Wearable v1: CatBoost/XGBoost
        # Gut v2: CatBoost RAW
        for train_idx, val_idx_fold in skf.split(X_tr_c, y_tr[:, d_idx]):
            # Clinical v2
            m_c = XGBClassifier(n_estimators=150, max_depth=4, learning_rate=0.05, random_state=42, eval_metric="logloss")
            m_c.fit(X_tr_c[train_idx], y_tr[train_idx, d_idx])
            oof_c[val_idx_fold, d_idx] = m_c.predict_proba(X_tr_c[val_idx_fold])[:, 1]

            # Wearable v1
            m_w = XGBClassifier(n_estimators=150, max_depth=4, learning_rate=0.05, random_state=42, eval_metric="logloss")
            m_w.fit(X_tr_w[train_idx], y_tr[train_idx, d_idx])
            oof_w[val_idx_fold, d_idx] = m_w.predict_proba(X_tr_w[val_idx_fold])[:, 1]

            # Gut v2
            m_g = CatBoostClassifier(iterations=200, depth=4, learning_rate=0.05, random_seed=42, verbose=0)
            m_g.fit(X_tr_g[train_idx], y_tr[train_idx, d_idx])
            oof_g[val_idx_fold, d_idx] = m_g.predict_proba(X_tr_g[val_idx_fold])[:, 1]

        # Predict Validation & Test using full train models
        m_c_full = XGBClassifier(n_estimators=150, max_depth=4, learning_rate=0.05, random_state=42, eval_metric="logloss").fit(X_tr_c, y_tr[:, d_idx])
        val_c[:, d_idx]  = m_c_full.predict_proba(X_va_c)[:, 1]
        test_c[:, d_idx] = m_c_full.predict_proba(X_te_c)[:, 1]

        m_w_full = XGBClassifier(n_estimators=150, max_depth=4, learning_rate=0.05, random_state=42, eval_metric="logloss").fit(X_tr_w, y_tr[:, d_idx])
        val_w[:, d_idx]  = m_w_full.predict_proba(X_va_w)[:, 1]
        test_w[:, d_idx] = m_w_full.predict_proba(X_te_w)[:, 1]

        m_g_full = CatBoostClassifier(iterations=200, depth=4, learning_rate=0.05, random_seed=42, verbose=0).fit(X_tr_g, y_tr[:, d_idx])
        val_g[:, d_idx]  = m_g_full.predict_proba(X_va_g)[:, 1]
        test_g[:, d_idx] = m_g_full.predict_proba(X_te_g)[:, 1]

    return (oof_c, oof_w, oof_g), (val_c, val_w, val_g), (test_c, test_w, test_g), (y_tr, y_va, y_te)


def run_fusion_v2_experiment():
    (oof_c, oof_w, oof_g), (val_c, val_w, val_g), (test_c, test_w, test_g), (y_tr, y_va, y_te) = generate_oof_predictions()

    pathways = {
        "Cv2":          {"oof": [oof_c],                "val": [val_c],                "test": [test_c]},
        "Wv1":          {"oof": [oof_w],                "val": [val_w],                "test": [test_w]},
        "Gv2":          {"oof": [oof_g],                "val": [val_g],                "test": [test_g]},
        "Cv2_Wv1":      {"oof": [oof_c, oof_w],         "val": [val_c, val_w],         "test": [test_c, test_w]},
        "Cv2_Gv2":      {"oof": [oof_c, oof_g],         "val": [val_c, val_g],         "test": [test_c, test_g]},
        "Wv1_Gv2":      {"oof": [oof_w, oof_g],         "val": [val_w, val_g],         "test": [test_w, test_g]},
        "Cv2_Wv1_Gv2":  {"oof": [oof_c, oof_w, oof_g],  "val": [val_c, val_w, val_g],  "test": [test_c, test_w, test_g]}
    }

    pathway_results = {}
    fitted_stackers = {}

    logger.info("--- Step 2: Training Fusion Meta-Learners & Tuning Thresholds ---")

    for path_name, data_dict in pathways.items():
        oof_concat  = np.hstack(data_dict["oof"])
        val_concat  = np.hstack(data_dict["val"])
        test_concat = np.hstack(data_dict["test"])

        fitted_stackers[path_name] = {}
        val_cal_probs  = np.zeros((len(y_va), len(DISEASE_COLS)))
        test_cal_probs = np.zeros((len(y_te), len(DISEASE_COLS)))

        tuned_thresholds = {}

        for d_idx, disease in enumerate(DISEASE_COLS):
            # If single modality, use probabilities directly
            if oof_concat.shape[1] == len(DISEASE_COLS):
                raw_val_p  = val_concat[:, d_idx]
                raw_test_p = test_concat[:, d_idx]
                stacker    = None
            else:
                # Meta-learner fitted ONCE on Train OOF
                sub_oof  = oof_concat[:, d_idx::len(DISEASE_COLS)]
                sub_val  = val_concat[:, d_idx::len(DISEASE_COLS)]
                sub_test = test_concat[:, d_idx::len(DISEASE_COLS)]

                stacker = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
                stacker.fit(sub_oof, y_tr[:, d_idx])

                raw_val_p  = stacker.predict_proba(sub_val)[:, 1]
                raw_test_p = stacker.predict_proba(sub_test)[:, 1]

            # Fit Isotonic Calibrator on Validation set
            iso = IsotonicRegression(out_of_bounds="clip")
            iso.fit(raw_val_p, y_va[:, d_idx])

            val_cal_probs[:, d_idx]  = iso.transform(raw_val_p)
            test_cal_probs[:, d_idx] = iso.transform(raw_test_p)

            # Tune threshold on Validation
            t_opt = find_optimal_threshold_for_disease(y_va[:, d_idx], val_cal_probs[:, d_idx])
            tuned_thresholds[disease] = round(float(t_opt), 4)

            fitted_stackers[path_name][disease] = (stacker, iso, t_opt)

        # Apply thresholds to test
        test_preds = np.zeros_like(test_cal_probs, dtype=int)
        for d_idx, disease in enumerate(DISEASE_COLS):
            test_preds[:, d_idx] = (test_cal_probs[:, d_idx] >= tuned_thresholds[disease]).astype(int)

        # Test metrics
        macro_f1 = f1_score(y_te, test_preds, average="macro")
        micro_f1 = f1_score(y_te, test_preds, average="micro")
        h_loss   = hamming_loss(y_te, test_preds)
        m_brier  = float(np.mean([brier_score_loss(y_te[:, i], test_cal_probs[:, i]) for i in range(len(DISEASE_COLS))]))

        per_disease = {}
        for d_idx, disease in enumerate(DISEASE_COLS):
            f1    = f1_score(y_te[:, d_idx], test_preds[:, d_idx])
            prec  = precision_score(y_te[:, d_idx], test_preds[:, d_idx], zero_division=0)
            rec   = recall_score(y_te[:, d_idx], test_preds[:, d_idx], zero_division=0)
            roc   = roc_auc_score(y_te[:, d_idx], test_cal_probs[:, d_idx])
            pr    = compute_pr_auc(y_te[:, d_idx], test_cal_probs[:, d_idx])
            brier = brier_score_loss(y_te[:, d_idx], test_cal_probs[:, d_idx])

            per_disease[disease] = {
                "f1": round(float(f1), 4),
                "precision": round(float(prec), 4),
                "recall": round(float(rec), 4),
                "roc_auc": round(float(roc), 4),
                "pr_auc": round(float(pr), 4),
                "brier_score": round(float(brier), 4)
            }

        pathway_results[path_name] = {
            "macro_f1": round(float(macro_f1), 4),
            "micro_f1": round(float(micro_f1), 4),
            "hamming_loss": round(float(h_loss), 4),
            "mean_brier": round(float(m_brier), 4),
            "tuned_thresholds": tuned_thresholds,
            "per_disease": per_disease,
            "test_preds": test_preds,
            "test_cal_probs": test_cal_probs
        }

        logger.info(f"Pathway [{path_name:12s}]: Test Macro F1 = {macro_f1:.4f}, Micro F1 = {micro_f1:.4f}")

    # ── Step 3: Shuffled Permutation Controls (100 Seeds) ──
    logger.info("--- Step 3: Running 100-Permutation Shuffled Controls ---")
    shuffled_controls = {}
    rng = np.random.default_rng(42)

    shuffled_scenarios = ["Cv2_Shuffled_Wv1", "Cv2_Shuffled_Gv2", "Wv1_Shuffled_Gv2", "Cv2_Wv1_Shuffled_Gv2"]

    for sc in shuffled_scenarios:
        shuffled_macro_f1s = []
        for s in range(100):
            perm_idx = rng.permutation(len(y_te))
            if sc == "Cv2_Shuffled_Wv1":
                sub_c = test_c
                sub_w = test_w[perm_idx]
                test_in = np.hstack([sub_c, sub_w])
                base_path = "Cv2_Wv1"
            elif sc == "Cv2_Shuffled_Gv2":
                sub_c = test_c
                sub_g = test_g[perm_idx]
                test_in = np.hstack([sub_c, sub_g])
                base_path = "Cv2_Gv2"
            elif sc == "Wv1_Shuffled_Gv2":
                sub_w = test_w
                sub_g = test_g[perm_idx]
                test_in = np.hstack([sub_w, sub_g])
                base_path = "Wv1_Gv2"
            elif sc == "Cv2_Wv1_Shuffled_Gv2":
                sub_c = test_c
                sub_w = test_w
                sub_g = test_g[perm_idx]
                test_in = np.hstack([sub_c, sub_w, sub_g])
                base_path = "Cv2_Wv1_Gv2"

            s_preds = np.zeros_like(y_te, dtype=int)
            for d_idx, disease in enumerate(DISEASE_COLS):
                stacker, iso, t_opt = fitted_stackers[base_path][disease]
                sub_d = test_in[:, d_idx::len(DISEASE_COLS)]
                raw_p = stacker.predict_proba(sub_d)[:, 1]
                cal_p = iso.transform(raw_p)
                s_preds[:, d_idx] = (cal_p >= t_opt).astype(int)

            s_f1 = f1_score(y_te, s_preds, average="macro")
            shuffled_macro_f1s.append(s_f1)

        base_val = pathway_results[sc.replace("_Shuffled", "").replace("_Gv2", "").replace("_Wv1", "") if "_Shuffled" in sc else "Cv2"]["macro_f1"]
        shuffled_controls[sc] = {
            "mean_macro_f1": round(float(np.mean(shuffled_macro_f1s)), 4),
            "std_macro_f1": round(float(np.std(shuffled_macro_f1s)), 4),
            "null_delta_vs_baseline": round(float(np.mean(shuffled_macro_f1s) - base_val), 4)
        }
        logger.info(f"Shuffled Control [{sc:22s}]: Mean Macro F1 = {shuffled_controls[sc]['mean_macro_f1']:.4f}")

    # ── Step 4: Bootstrap 95% Confidence Intervals (1,000 Iterations) ──
    logger.info("--- Step 4: Computing Bootstrap 95% Confidence Intervals (B=1,000) ---")
    boot_deltas = {
        "Cv2_Wv1_minus_Cv2": [],
        "Cv2_Gv2_minus_Cv2": [],
        "Wv1_Gv2_minus_Wv1": [],
        "Cv2_Wv1_Gv2_minus_Cv2": [],
        "Cv2_Wv1_Gv2_minus_Cv2_Wv1": []
    }

    n_test_samples = len(y_te)
    for _ in range(1000):
        b_idx = rng.choice(n_test_samples, size=n_test_samples, replace=True)
        f1_c   = f1_score(y_te[b_idx], pathway_results["Cv2"]["test_preds"][b_idx], average="macro")
        f1_w   = f1_score(y_te[b_idx], pathway_results["Wv1"]["test_preds"][b_idx], average="macro")
        f1_cw  = f1_score(y_te[b_idx], pathway_results["Cv2_Wv1"]["test_preds"][b_idx], average="macro")
        f1_cg  = f1_score(y_te[b_idx], pathway_results["Cv2_Gv2"]["test_preds"][b_idx], average="macro")
        f1_wg  = f1_score(y_te[b_idx], pathway_results["Wv1_Gv2"]["test_preds"][b_idx], average="macro")
        f1_cwg = f1_score(y_te[b_idx], pathway_results["Cv2_Wv1_Gv2"]["test_preds"][b_idx], average="macro")

        boot_deltas["Cv2_Wv1_minus_Cv2"].append(f1_cw - f1_c)
        boot_deltas["Cv2_Gv2_minus_Cv2"].append(f1_cg - f1_c)
        boot_deltas["Wv1_Gv2_minus_Wv1"].append(f1_wg - f1_w)
        boot_deltas["Cv2_Wv1_Gv2_minus_Cv2"].append(f1_cwg - f1_c)
        boot_deltas["Cv2_Wv1_Gv2_minus_Cv2_Wv1"].append(f1_cwg - f1_cw)

    ci_summary = {}
    for delta_key, dist in boot_deltas.items():
        ci_summary[delta_key] = {
            "mean_delta": round(float(np.mean(dist)), 4),
            "ci_95": [round(float(np.percentile(dist, 2.5)), 4), round(float(np.percentile(dist, 97.5)), 4)]
        }

    # ── Step 5: Patient-Level Error Complementarity Analysis ──
    logger.info("--- Step 5: Patient-Level Error Complementarity Analysis ---")
    error_comp = {}

    pairs_to_analyze = [
        ("Cv2", "Cv2_Wv1"),
        ("Cv2", "Cv2_Gv2"),
        ("Wv1", "Wv1_Gv2"),
        ("Cv2", "Cv2_Wv1_Gv2"),
        ("Cv2_Wv1", "Cv2_Wv1_Gv2")
    ]

    for base_p, fused_p in pairs_to_analyze:
        base_pred  = pathway_results[base_p]["test_preds"]
        fused_pred = pathway_results[fused_p]["test_preds"]

        error_comp[f"{fused_p}_vs_{base_p}"] = {}

        total_corrected = 0
        total_corrupted = 0

        for d_idx, disease in enumerate(DISEASE_COLS):
            y_true_d = y_te[:, d_idx]
            base_err = (base_pred[:, d_idx] != y_true_d)
            fused_err = (fused_pred[:, d_idx] != y_true_d)

            corrected = np.sum(base_err & ~fused_err)
            corrupted = np.sum(~base_err & fused_err)
            net_gain  = corrected - corrupted

            total_corrected += corrected
            total_corrupted += corrupted

            error_comp[f"{fused_p}_vs_{base_p}"][disease] = {
                "corrected": int(corrected),
                "corrupted": int(corrupted),
                "net_corrected": int(net_gain)
            }

        error_comp[f"{fused_p}_vs_{base_p}"]["total_net_corrected_instances"] = int(total_corrected - total_corrupted)

    # Clean serializable dictionary for JSON
    clean_pathway_results = {}
    for k, v in pathway_results.items():
        clean_pathway_results[k] = {
            "macro_f1": v["macro_f1"],
            "micro_f1": v["micro_f1"],
            "hamming_loss": v["hamming_loss"],
            "mean_brier": v["mean_brier"],
            "tuned_thresholds": v["tuned_thresholds"],
            "per_disease": v["per_disease"]
        }

    final_payload = {
        "pathway_results": clean_pathway_results,
        "shuffled_controls": shuffled_controls,
        "bootstrap_confidence_intervals": ci_summary,
        "error_complementarity": error_comp
    }

    with open("fusion_v2_summary.json", "w") as f:
        json.dump(final_payload, f, indent=2)

    logger.info("Experimental Multimodal Fusion v2 Pipeline Complete. Saved to fusion_v2_summary.json")
    return final_payload


if __name__ == "__main__":
    run_fusion_v2_experiment()
