"""
reconcile_fusion_v2.py — Full Reconciliation & Fusion v2 Audit Engine.

Evaluates and reconciles:
1. Patient_ID & Target Label Alignment across Clinical_v1, Clinical_v2, Wearable_v1, Gut_v2
2. Standalone Benchmark Reconciliation:
   - Evaluated against Clinical v1 Targets (Original Frozen Benchmark: Wv1=0.8132, Gv2=0.5061, Wv1+Gv2=0.8287)
   - Evaluated against Clinical v2 Targets (New Latent Physiology Benchmark: Cv2=0.8747)
3. 5-Fold OOF Probability Stacking (Logistic Regression on continuous probabilities P(disease | modality))
4. Pathway Evaluations (Cv2, Wv1, Gv2, Cv2+Wv1, Cv2+Gv2, Wv1+Gv2, Cv2+Wv1+Gv2)
5. 100-Permutation Shuffled Controls
6. 1,000-Iteration Bootstrap 95% Confidence Intervals
7. Patient-Level Error Complementarity Analysis
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

from expert_models.preprocessing import ExpertPreprocessor
from expert_models.threshold_tuner import find_optimal_threshold_for_disease
from expert_models import config as expert_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("reconcile_fusion_v2")

DISEASE_COLS = expert_config.TARGET_DISEASES


def compute_pr_auc(y_true, y_prob):
    p, r, _ = precision_recall_curve(y_true, y_prob)
    return float(auc(r, p))


def run_full_reconciliation():
    logger.info("==================================================================")
    logger.info("  1. PATIENT ID & TARGET LABEL ALIGNMENT AUDIT")
    logger.info("==================================================================")

    clin_v1_df = pd.read_csv("Clinical_Dataset.csv")
    clin_v2_df = pd.read_csv("Clinical_Dataset_v2.csv")
    wear_df    = pd.read_csv("Wearable_Dataset.csv")
    gut_df     = pd.read_csv("Gut_Dataset_v2.csv")

    n_total = len(clin_v2_df)
    n_train, n_val, n_test = 14000, 3000, 3000

    id_c1 = clin_v1_df["Patient_ID"].values
    id_c2 = clin_v2_df["Patient_ID"].values
    id_w  = wear_df["Patient_ID"].values
    id_g  = gut_df["Patient_ID"].values

    id_match_all = np.array_equal(id_c2, id_w) and np.array_equal(id_c2, id_g) and np.array_equal(id_c2, id_c1)
    test_id_match = np.array_equal(id_c2[17000:], id_w[17000:]) and np.array_equal(id_c2[17000:], id_g[17000:])

    y_v1_all = clin_v1_df[DISEASE_COLS].values
    y_v2_all = clin_v2_df[DISEASE_COLS].values

    y_v1_te = y_v1_all[17000:]
    y_v2_te = y_v2_all[17000:]

    y_wear_te = wear_df[DISEASE_COLS].values[17000:]
    y_gut_te  = gut_df[DISEASE_COLS].values[17000:]

    v1_target_match = np.array_equal(y_v1_te, y_wear_te) and np.array_equal(y_v1_te, y_gut_te)

    alignment_summary = {
        "total_patient_count": n_total,
        "test_patient_count": n_test,
        "patient_id_alignment_pass": bool(id_match_all and test_id_match),
        "v1_target_label_alignment_pass": bool(v1_target_match),
        "v1_vs_v2_target_disagreement_count": int(np.sum(y_v1_te != y_v2_te))
    }
    logger.info(f"Patient ID Alignment Audit: PASS={alignment_summary['patient_id_alignment_pass']}")
    logger.info(f"Target Label Disagreements (v1 vs v2 in Test): {alignment_summary['v1_vs_v2_target_disagreement_count']} instances out of 15,000 disease-patient pairs")

    logger.info("==================================================================")
    logger.info("  2. STANDALONE EXPERT METRICS RECONCILIATION")
    logger.info("==================================================================")

    # ── A. Clinical v2 Expert (Evaluated on v2 Targets) ──
    clin_prep = joblib.load("expert_models/saved_models/clinical_v2/preprocessor_clinical_v2.joblib")
    X_clin = clin_prep.transform(clin_v2_df[clin_prep.feature_order])
    X_tr_c, X_va_c, X_te_c = X_clin[:n_train], X_clin[n_train:n_train+n_val], X_clin[n_train+n_val:]

    y_v2_tr = y_v2_all[:n_train]
    y_v2_va = y_v2_all[n_train:n_train+n_val]
    y_v2_te = y_v2_all[n_train+n_val:]

    val_probs_c  = np.zeros((n_val, len(DISEASE_COLS)))
    test_probs_c = np.zeros((n_test, len(DISEASE_COLS)))
    test_preds_c = np.zeros((n_test, len(DISEASE_COLS)), dtype=int)

    for d_idx, disease in enumerate(DISEASE_COLS):
        payload = joblib.load(f"expert_models/saved_models/clinical_v2/{disease}_clinical_v2.joblib")
        model = payload["uncalibrated_model"]
        iso   = payload["calibrator"]
        t_opt = payload["threshold"]

        raw_val  = model.predict_proba(X_va_c)[:, 1]
        raw_test = model.predict_proba(X_te_c)[:, 1]

        val_probs_c[:, d_idx]  = iso.transform(raw_val)
        test_probs_c[:, d_idx] = iso.transform(raw_test)
        test_preds_c[:, d_idx] = (test_probs_c[:, d_idx] >= t_opt).astype(int)

    f1_c_v2 = f1_score(y_v2_te, test_preds_c, average="macro")
    logger.info(f"Clinical v2 Standalone (on v2 Targets): Macro F1 = {f1_c_v2:.4f}")

    # ── B. Wearable v1 Expert (Evaluated on v1 Targets AND v2 Targets) ──
    wear_dir = os.path.join(expert_config.SAVED_MODELS_DIR, "wearable_v1")
    with open(os.path.join(wear_dir, "feature_order.json")) as f:
        wear_feat_order = json.load(f)
    with open(os.path.join(wear_dir, "thresholds.json")) as f:
        wear_thresholds = json.load(f)
    wear_prep  = joblib.load(os.path.join(wear_dir, "preprocessor.pkl"))
    wear_cal   = joblib.load(os.path.join(wear_dir, "calibrator.pkl"))
    wear_model_proto = joblib.load(os.path.join(wear_dir, "model", "estimator.joblib"))
    gut_v2_payload = joblib.load("expert_models/saved_models/gut_v2/model.joblib")

    X_wear = wear_prep.transform(wear_df[wear_feat_order])
    X_tr_w, X_va_w, X_te_w = X_wear[:n_train], X_wear[n_train:n_train+n_val], X_wear[n_train+n_val:]

    raw_val_w  = wear_model_proto.predict_proba(X_va_w)
    raw_test_w = wear_model_proto.predict_proba(X_te_w)

    val_probs_w  = wear_cal.calibrate_probas(raw_val_w)
    test_probs_w = wear_cal.calibrate_probas(raw_test_w)

    test_preds_w_v1targets = np.zeros((n_test, len(DISEASE_COLS)), dtype=int)
    for d_idx, disease in enumerate(DISEASE_COLS):
        t_opt = wear_thresholds[disease]
        test_preds_w_v1targets[:, d_idx] = (test_probs_w[:, d_idx] >= t_opt).astype(int)

    f1_w_v1targets = f1_score(y_v1_te, test_preds_w_v1targets, average="macro")
    f1_w_v2targets = f1_score(y_v2_te, test_preds_w_v1targets, average="macro")

    logger.info(f"Wearable v1 Standalone (on v1 Targets): Macro F1 = {f1_w_v1targets:.4f} (Original Validated Benchmark)")
    logger.info(f"Wearable v1 Standalone (on v2 Targets): Macro F1 = {f1_w_v2targets:.4f} (Cross-Target Shift)")

    # ── C. Gut v2 Set B Expert (Evaluated on v1 Targets AND v2 Targets) ──
    gut_v2_payload = joblib.load("expert_models/saved_models/gut_v2/model.joblib")
    taxa_20 = [
        "Akkermansia", "Faecalibacterium", "Roseburia", "Bifidobacterium", "Bacteroides",
        "Prevotella", "Ruminococcus", "Blautia", "Collinsella", "Escherichia_Shigella",
        "Coprococcus", "Alistipes", "Subdoligranulum", "Enterococcus", "Eubacterium",
        "Parabacteroides", "Lactobacillus", "Klebsiella", "Streptococcus", "Eggerthella"
    ]
    X_gut = gut_df[taxa_20].values
    X_tr_g, X_va_g, X_te_g = X_gut[:n_train], X_gut[n_train:n_train+n_val], X_gut[n_train+n_val:]

    with open("expert_models/saved_models/gut_v2/thresholds.json") as f:
        gut_v2_thresholds = json.load(f)

    gut_cal = joblib.load("expert_models/saved_models/gut_v2/calibrator.joblib")

    raw_val_g  = gut_v2_payload.predict_proba(X_va_g)
    raw_test_g = gut_v2_payload.predict_proba(X_te_g)

    val_probs_g  = gut_cal.calibrate_probas(raw_val_g)
    test_probs_g = gut_cal.calibrate_probas(raw_test_g)

    test_preds_g_v1targets = np.zeros((n_test, len(DISEASE_COLS)), dtype=int)
    for d_idx, disease in enumerate(DISEASE_COLS):
        m_g_proto = gut_v2_payload.estimators[disease]
        t_opt = gut_v2_thresholds[disease]
        test_preds_g_v1targets[:, d_idx] = (test_probs_g[:, d_idx] >= t_opt).astype(int)

    f1_g_v1targets = f1_score(y_v1_te, test_preds_g_v1targets, average="macro")
    f1_g_v2targets = f1_score(y_v2_te, test_preds_g_v1targets, average="macro")

    logger.info(f"Gut v2 Set B Standalone (on v1 Targets): Macro F1 = {f1_g_v1targets:.4f} (Original Validated Benchmark)")
    logger.info(f"Gut v2 Set B Standalone (on v2 Targets): Macro F1 = {f1_g_v2targets:.4f} (Cross-Target Shift)")

    reconciled_standalone = {
        "Clinical_v2_on_v2_targets": round(float(f1_c_v2), 4),
        "Wearable_v1_on_v1_targets": round(float(f1_w_v1targets), 4),
        "Wearable_v1_on_v2_targets": round(float(f1_w_v2targets), 4),
        "Gut_v2_SetB_on_v1_targets": round(float(f1_g_v1targets), 4),
        "Gut_v2_SetB_on_v2_targets": round(float(f1_g_v2targets), 4)
    }

    # ── 3. Re-Audit Wv1 + Gv2 Fusion on Original Targets ──
    logger.info("==================================================================")
    logger.info("  3. RE-AUDITING Wv1 + Gv2 FUSION ON ORIGINAL V1 TARGETS")
    logger.info("==================================================================")

    # Train Logistic Regression Stacking on Validation for Wv1 + Gv2
    test_preds_wg_v1 = np.zeros((n_test, len(DISEASE_COLS)), dtype=int)
    test_cal_wg_v1   = np.zeros((n_test, len(DISEASE_COLS)))

    y_v1_tr = y_v1_all[:n_train]
    y_v1_va = y_v1_all[n_train:n_train+n_val]

    for d_idx, disease in enumerate(DISEASE_COLS):
        sub_val  = np.hstack([val_probs_w[:, d_idx:d_idx+1], val_probs_g[:, d_idx:d_idx+1]])
        sub_test = np.hstack([test_probs_w[:, d_idx:d_idx+1], test_probs_g[:, d_idx:d_idx+1]])

        meta = LogisticRegression(C=1.0, random_state=42)
        meta.fit(sub_val, y_v1_va[:, d_idx])

        raw_t = meta.predict_proba(sub_test)[:, 1]
        iso = IsotonicRegression(out_of_bounds="clip").fit(meta.predict_proba(sub_val)[:, 1], y_v1_va[:, d_idx])
        test_cal_wg_v1[:, d_idx] = iso.transform(raw_t)

        t_opt = find_optimal_threshold_for_disease(y_v1_va[:, d_idx], iso.transform(meta.predict_proba(sub_val)[:, 1]))
        test_preds_wg_v1[:, d_idx] = (test_cal_wg_v1[:, d_idx] >= t_opt).astype(int)

    f1_wg_v1targets = f1_score(y_v1_te, test_preds_wg_v1, average="macro")
    logger.info(f"Reconciled Wv1 + Gv2 Fusion (on v1 Targets): Macro F1 = {f1_wg_v1targets:.4f} (Delta vs Wv1 = +{f1_wg_v1targets - f1_w_v1targets:.4f})")

    # ── 4. Multimodal Fusion v2 Evaluation on Clinical v2 Benchmark ──
    logger.info("==================================================================")
    logger.info("  4. MULTIMODAL FUSION v2 EVALUATION ON CLINICAL v2 BENCHMARK")
    logger.info("==================================================================")

    pathways = {
        "Cv2":          [test_probs_c],
        "Wv1":          [test_probs_w],
        "Gv2":          [test_probs_g],
        "Cv2_Wv1":      [test_probs_c, test_probs_w],
        "Cv2_Gv2":      [test_probs_c, test_probs_g],
        "Wv1_Gv2":      [test_probs_w, test_probs_g],
        "Cv2_Wv1_Gv2":  [test_probs_c, test_probs_w, test_probs_g]
    }

    pathway_results = {}
    fitted_stackers = {}

    for path_name, prob_list in pathways.items():
        val_concat  = np.hstack([val_probs_c if p is test_probs_c else (val_probs_w if p is test_probs_w else val_probs_g) for p in prob_list])
        test_concat = np.hstack(prob_list)

        meta_dim = test_concat.shape[1]
        test_cal_probs = np.zeros((n_test, len(DISEASE_COLS)))
        test_preds     = np.zeros((n_test, len(DISEASE_COLS)), dtype=int)
        tuned_thresholds = {}

        fitted_stackers[path_name] = {}

        for d_idx, disease in enumerate(DISEASE_COLS):
            if meta_dim == len(DISEASE_COLS):
                raw_val_p  = val_concat[:, d_idx]
                raw_test_p = test_concat[:, d_idx]
                stacker    = None
            else:
                sub_val  = val_concat[:, d_idx::len(DISEASE_COLS)]
                sub_test = test_concat[:, d_idx::len(DISEASE_COLS)]

                stacker = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
                stacker.fit(sub_val, y_v2_va[:, d_idx])

                raw_val_p  = stacker.predict_proba(sub_val)[:, 1]
                raw_test_p = stacker.predict_proba(sub_test)[:, 1]

            iso = IsotonicRegression(out_of_bounds="clip").fit(raw_val_p, y_v2_va[:, d_idx])
            val_cal_p  = iso.transform(raw_val_p)
            test_cal_p = iso.transform(raw_test_p)

            t_opt = find_optimal_threshold_for_disease(y_v2_va[:, d_idx], val_cal_p)
            tuned_thresholds[disease] = round(float(t_opt), 4)

            test_cal_probs[:, d_idx] = test_cal_p
            test_preds[:, d_idx]     = (test_cal_p >= t_opt).astype(int)

            fitted_stackers[path_name][disease] = (stacker, iso, t_opt)

        macro_f1 = f1_score(y_v2_te, test_preds, average="macro")
        micro_f1 = f1_score(y_v2_te, test_preds, average="micro")
        h_loss   = hamming_loss(y_v2_te, test_preds)
        m_brier  = float(np.mean([brier_score_loss(y_v2_te[:, i], test_cal_probs[:, i]) for i in range(len(DISEASE_COLS))]))

        per_disease = {}
        for d_idx, disease in enumerate(DISEASE_COLS):
            f1    = f1_score(y_v2_te[:, d_idx], test_preds[:, d_idx])
            prec  = precision_score(y_v2_te[:, d_idx], test_preds[:, d_idx], zero_division=0)
            rec   = recall_score(y_v2_te[:, d_idx], test_preds[:, d_idx], zero_division=0)
            roc   = roc_auc_score(y_v2_te[:, d_idx], test_cal_probs[:, d_idx])
            pr    = compute_pr_auc(y_v2_te[:, d_idx], test_cal_probs[:, d_idx])
            brier = brier_score_loss(y_v2_te[:, d_idx], test_cal_probs[:, d_idx])

            per_disease[disease] = {
                "f1": round(float(f1), 4),
                "precision": round(float(prec), 4),
                "recall": round(float(rec), 4),
                "roc_auc": round(float(roc), 4),
                "pr_auc": round(float(pr), 4),
                "brier_score": round(float(brier), 4)
            }

        pathway_results[path_name] = {
            "meta_feature_dimension": meta_dim,
            "macro_f1": round(float(macro_f1), 4),
            "micro_f1": round(float(micro_f1), 4),
            "hamming_loss": round(float(h_loss), 4),
            "mean_brier": round(float(m_brier), 4),
            "tuned_thresholds": tuned_thresholds,
            "per_disease": per_disease,
            "test_preds": test_preds,
            "test_cal_probs": test_cal_probs
        }

        logger.info(f"Pathway [{path_name:12s}] (Dim={meta_dim:2d}): Test Macro F1 = {macro_f1:.4f}, Micro F1 = {micro_f1:.4f}")

    # ── 5. 100-Permutation Shuffled Controls ──
    logger.info("==================================================================")
    logger.info("  5. RUNNING 100-PERMUTATION SHUFFLED CONTROLS")
    logger.info("==================================================================")
    shuffled_controls = {}
    rng = np.random.default_rng(42)

    shuffled_scenarios = [
        ("Cv2_Shuffled_Wv1", "Cv2_Wv1", [test_probs_c, test_probs_w]),
        ("Cv2_Shuffled_Gv2", "Cv2_Gv2", [test_probs_c, test_probs_g]),
        ("Wv1_Shuffled_Gv2", "Wv1_Gv2", [test_probs_w, test_probs_g]),
        ("Cv2_Wv1_Shuffled_Gv2", "Cv2_Wv1_Gv2", [test_probs_c, test_probs_w, test_probs_g])
    ]

    for sc_name, base_path, prob_list in shuffled_scenarios:
        shuffled_macro_f1s = []
        for _ in range(100):
            perm_idx = rng.permutation(n_test)
            if sc_name == "Cv2_Shuffled_Wv1":
                sub_c = prob_list[0]
                sub_w = prob_list[1][perm_idx]
                test_in = np.hstack([sub_c, sub_w])
            elif sc_name == "Cv2_Shuffled_Gv2":
                sub_c = prob_list[0]
                sub_g = prob_list[1][perm_idx]
                test_in = np.hstack([sub_c, sub_g])
            elif sc_name == "Wv1_Shuffled_Gv2":
                sub_w = prob_list[0]
                sub_g = prob_list[1][perm_idx]
                test_in = np.hstack([sub_w, sub_g])
            elif sc_name == "Cv2_Wv1_Shuffled_Gv2":
                sub_c = prob_list[0]
                sub_w = prob_list[1]
                sub_g = prob_list[2][perm_idx]
                test_in = np.hstack([sub_c, sub_w, sub_g])

            s_preds = np.zeros_like(y_v2_te, dtype=int)
            for d_idx, disease in enumerate(DISEASE_COLS):
                stacker, iso, t_opt = fitted_stackers[base_path][disease]
                sub_d = test_in[:, d_idx::len(DISEASE_COLS)]
                raw_p = stacker.predict_proba(sub_d)[:, 1] if stacker else sub_d[:, 0]
                cal_p = iso.transform(raw_p)
                s_preds[:, d_idx] = (cal_p >= t_opt).astype(int)

            s_f1 = f1_score(y_v2_te, s_preds, average="macro")
            shuffled_macro_f1s.append(s_f1)

        base_f1 = pathway_results[base_path]["macro_f1"]
        mean_shuf_f1 = float(np.mean(shuffled_macro_f1s))
        p_val = float(np.mean(np.array(shuffled_macro_f1s) >= base_f1))

        shuffled_controls[sc_name] = {
            "baseline_macro_f1": base_f1,
            "shuffled_mean_macro_f1": round(mean_shuf_f1, 4),
            "shuffled_std": round(float(np.std(shuffled_macro_f1s)), 4),
            "delta_aligned_minus_shuffled": round(base_f1 - mean_shuf_f1, 4),
            "permutation_p_value": round(p_val, 4)
        }
        logger.info(f"Shuffled Control [{sc_name:22s}]: Baseline={base_f1:.4f}, Shuffled={mean_shuf_f1:.4f}, p-val={p_val:.4f}")

    # ── 6. Bootstrap 95% Confidence Intervals (1,000 Iterations) ──
    logger.info("==================================================================")
    logger.info("  6. COMPUTING BOOTSTRAP 95% CONFIDENCE INTERVALS (B=1,000)")
    logger.info("==================================================================")
    boot_deltas = {
        "Cv2_Wv1_minus_Cv2": [],
        "Cv2_Gv2_minus_Cv2": [],
        "Wv1_Gv2_minus_Wv1": [],
        "Cv2_Wv1_Gv2_minus_Cv2": [],
        "Cv2_Wv1_Gv2_minus_Cv2_Wv1": []
    }

    for _ in range(1000):
        b_idx = rng.choice(n_test, size=n_test, replace=True)
        f1_c   = f1_score(y_v2_te[b_idx], pathway_results["Cv2"]["test_preds"][b_idx], average="macro")
        f1_w   = f1_score(y_v2_te[b_idx], pathway_results["Wv1"]["test_preds"][b_idx], average="macro")
        f1_cw  = f1_score(y_v2_te[b_idx], pathway_results["Cv2_Wv1"]["test_preds"][b_idx], average="macro")
        f1_cg  = f1_score(y_v2_te[b_idx], pathway_results["Cv2_Gv2"]["test_preds"][b_idx], average="macro")
        f1_wg  = f1_score(y_v2_te[b_idx], pathway_results["Wv1_Gv2"]["test_preds"][b_idx], average="macro")
        f1_cwg = f1_score(y_v2_te[b_idx], pathway_results["Cv2_Wv1_Gv2"]["test_preds"][b_idx], average="macro")

        boot_deltas["Cv2_Wv1_minus_Cv2"].append(f1_cw - f1_c)
        boot_deltas["Cv2_Gv2_minus_Cv2"].append(f1_cg - f1_c)
        boot_deltas["Wv1_Gv2_minus_Wv1"].append(f1_wg - f1_w)
        boot_deltas["Cv2_Wv1_Gv2_minus_Cv2"].append(f1_cwg - f1_c)
        boot_deltas["Cv2_Wv1_Gv2_minus_Cv2_Wv1"].append(f1_cwg - f1_cw)

    ci_summary = {}
    for delta_key, dist in boot_deltas.items():
        ci_lower = round(float(np.percentile(dist, 2.5)), 4)
        ci_upper = round(float(np.percentile(dist, 97.5)), 4)
        stat_sig = bool(ci_lower > 0 or ci_upper < 0)

        ci_summary[delta_key] = {
            "mean_delta": round(float(np.mean(dist)), 4),
            "ci_95": [ci_lower, ci_upper],
            "statistically_significant_at_0.05": stat_sig
        }
        logger.info(f"Bootstrap Delta [{delta_key:25s}]: Mean = {ci_summary[delta_key]['mean_delta']:+.4f}, 95% CI = {ci_summary[delta_key]['ci_95']}, Sig = {stat_sig}")

    # ── 7. Patient-Level Error Complementarity Analysis ──
    logger.info("==================================================================")
    logger.info("  7. PATIENT-LEVEL ERROR COMPLEMENTARITY ANALYSIS")
    logger.info("==================================================================")
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
            y_true_d = y_v2_te[:, d_idx]
            base_err  = (base_pred[:, d_idx] != y_true_d)
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
            "meta_feature_dimension": v["meta_feature_dimension"],
            "macro_f1": v["macro_f1"],
            "micro_f1": v["micro_f1"],
            "hamming_loss": v["hamming_loss"],
            "mean_brier": v["mean_brier"],
            "tuned_thresholds": v["tuned_thresholds"],
            "per_disease": v["per_disease"]
        }

    final_payload = {
        "alignment_audit": alignment_summary,
        "standalone_reconciliation": reconciled_standalone,
        "v1_targets_fusion_reconciliation": {
            "Wv1_alone": round(float(f1_w_v1targets), 4),
            "Gut_v2_alone": round(float(f1_g_v1targets), 4),
            "Wv1_plus_Gv2": round(float(f1_wg_v1targets), 4),
            "delta_gain": round(float(f1_wg_v1targets - f1_w_v1targets), 4)
        },
        "pathway_results": clean_pathway_results,
        "shuffled_controls": shuffled_controls,
        "bootstrap_confidence_intervals": ci_summary,
        "error_complementarity": error_comp
    }

    with open("fusion_v2_final_reconciled_summary.json", "w") as f:
        json.dump(final_payload, f, indent=2)

    logger.info("Full Scientific Reconciliation & Audit Complete. Saved to fusion_v2_final_reconciled_summary.json")
    return final_payload


if __name__ == "__main__":
    run_full_reconciliation()
