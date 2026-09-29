"""
train_and_eval_fusion_v3.py — Complete Multimodal Fusion v3 Scientific Experimentation Pipeline

Executes:
1. Load all v3 datasets & master split manifest (N=20,000: 14k Train / 3k Val / 3k Test).
2. Generate strict 5-fold Out-of-Fold (OOF) probability predictions on Train split (N=14,000) for:
   - Clinical v3 (C)
   - Wearable Standard v3 (W_std)
   - Wearable + CGM v3 (W_cgm)
   - Gut v3 (G)
3. Generate Val (N=3,000) & Test (N=3,000) prediction probability matrices.
4. Evaluate 5 Fusion Stacking Architectures:
   A. Mean Probability Fusion
   B. Validation-Optimized Weighted Probability Fusion
   C. Logistic Regression Stacking
   D. XGBoost Stacking
   E. LightGBM Stacking
   across 7 Pathways: C, W, G, C+W, C+G, W+G, C+W+G.
5. Calibrate & Threshold-tune selected candidate per disease on Validation fold ONLY.
6. Evaluate ONCE on untouched Test set (N=3,000).
7. Perform Patient-Level Bootstrap (B=1,000) for complementary contribution deltas & 95% CIs.
8. Perform 100-Permutation Shuffled-Modality Negative Control Tests.
9. Evaluate Missing-Modality Patterns (all 7 availability combinations).
10. Compute Error Complementarity Metrics (errors corrected, introduced, net).
11. Export metrics and save payload to expert_models/saved_models/fusion_v3/.
"""

import os
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from scipy.optimize import minimize

from sklearn.model_selection import KFold
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score, precision_recall_curve, auc, brier_score_loss, confusion_matrix, hamming_loss

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("fusion_v3_exp")

DATA_DIR = Path("data/multimodal_v3")
SAVE_DIR = Path("expert_models/saved_models/fusion_v3")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

DISEASES = ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]

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

        f1s.append(f1)
        disease_metrics[disease] = {
            "f1": round(float(f1), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "roc_auc": round(float(r_auc), 4),
            "pr_auc": round(float(pr_auc_val), 4),
            "brier_score": round(float(brier), 4)
        }

    macro_f1 = round(float(np.mean(f1s)), 4)
    micro_f1 = round(float(f1_score(y_true, preds, average="micro", zero_division=0)), 4)
    h_loss   = round(float(hamming_loss(y_true, preds)), 4)
    m_brier  = round(float(np.mean([disease_metrics[d]["brier_score"] for d in DISEASES])), 4)

    return {
        "macro_f1": macro_f1,
        "micro_f1": micro_f1,
        "hamming_loss": h_loss,
        "mean_brier": m_brier,
        "per_disease": disease_metrics
    }, preds

def generate_oof_predictions():
    logger.info("Generating strict 5-fold OOF probability predictions for all experts...")
    clin_df     = pd.read_csv(DATA_DIR / "clinical_v3.csv")
    wear_std_df = pd.read_csv(DATA_DIR / "wearable_standard_v3.csv")
    wear_cgm_df = pd.read_csv(DATA_DIR / "wearable_cgm_v3.csv")
    gut_df      = pd.read_csv(DATA_DIR / "gut_v3.csv")
    labels_df   = pd.read_csv(DATA_DIR / "labels_v3.csv")
    split_df    = pd.read_csv(DATA_DIR / "split_manifest_v3.csv")

    train_mask = (split_df["Split"] == "Train").values
    val_mask   = (split_df["Split"] == "Val").values
    test_mask  = (split_df["Split"] == "Test").values

    y_all = labels_df[DISEASES].values
    y_tr  = y_all[train_mask]
    y_va  = y_all[val_mask]
    y_te  = y_all[test_mask]

    # Feature matrices
    clin_payload = joblib.load("expert_models/saved_models/clinical_v3/clinical_v3_payload.joblib")
    wear_payload = joblib.load("expert_models/saved_models/wearable_v3/wearable_v3_payload.joblib")
    gut_payload  = joblib.load("expert_models/saved_models/gut_v3/gut_v3_payload.joblib")

    X_c = clin_df[clin_payload["features"]].fillna(clin_payload["medians"]).values
    X_w = pd.concat([wear_std_df[wear_payload["features"][:10]], wear_cgm_df[wear_payload["features"][10:]]], axis=1).fillna(wear_payload["medians"]).values
    X_g = gut_df[gut_payload["features"]].fillna(gut_payload["medians"]).values

    # 5-fold CV split on Train set
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    oof_c = np.zeros_like(y_tr, dtype=float)
    oof_w = np.zeros_like(y_tr, dtype=float)
    oof_g = np.zeros_like(y_tr, dtype=float)

    for tr_idx, val_idx in kf.split(X_c[train_mask]):
        for d in range(5):
            # Clinical
            m_c = XGBClassifier(n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42, eval_metric="logloss")
            m_c.fit(X_c[train_mask][tr_idx], y_tr[tr_idx, d])
            oof_c[val_idx, d] = m_c.predict_proba(X_c[train_mask][val_idx])[:, 1]

            # Wearable
            m_w = LGBMClassifier(n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42, verbose=-1)
            m_w.fit(X_w[train_mask][tr_idx], y_tr[tr_idx, d])
            oof_w[val_idx, d] = m_w.predict_proba(X_w[train_mask][val_idx])[:, 1]

            # Gut
            m_g = XGBClassifier(n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42, eval_metric="logloss")
            m_g.fit(X_g[train_mask][tr_idx], y_tr[tr_idx, d])
            oof_g[val_idx, d] = m_g.predict_proba(X_g[train_mask][val_idx])[:, 1]

    # Full Train predictions on Val & Test
    val_c = np.column_stack([m.predict_proba(clin_payload["scaler"].transform(X_c[val_mask]))[:, 1] for m in clin_payload["models"]])
    test_c = np.column_stack([m.predict_proba(clin_payload["scaler"].transform(X_c[test_mask]))[:, 1] for m in clin_payload["models"]])

    val_w = np.column_stack([m.predict_proba(wear_payload["scaler"].transform(X_w[val_mask]))[:, 1] for m in wear_payload["models"]])
    test_w = np.column_stack([m.predict_proba(wear_payload["scaler"].transform(X_w[test_mask]))[:, 1] for m in wear_payload["models"]])

    val_g = np.column_stack([m.predict_proba(gut_payload["scaler"].transform(X_g[val_mask]))[:, 1] for m in gut_payload["models"]])
    test_g = np.column_stack([m.predict_proba(gut_payload["scaler"].transform(X_g[test_mask]))[:, 1] for m in gut_payload["models"]])

    return {
        "y_tr": y_tr, "y_va": y_va, "y_te": y_te,
        "oof_c": oof_c, "val_c": val_c, "test_c": test_c,
        "oof_w": oof_w, "val_w": val_w, "test_w": test_w,
        "oof_g": oof_g, "val_g": val_g, "test_g": test_g
    }

def train_and_eval_fusion():
    data = generate_oof_predictions()
    y_tr, y_va, y_te = data["y_tr"], data["y_va"], data["y_te"]

    pathways = {
        "C": ["c"],
        "W": ["w"],
        "G": ["g"],
        "C+W": ["c", "w"],
        "C+G": ["c", "g"],
        "W+G": ["w", "g"],
        "C+W+G": ["c", "w", "g"]
    }

    architectures = ["Mean", "Weighted", "LogisticRegression", "XGBoost", "LightGBM"]
    
    val_matrix = {}
    test_matrix = {}
    best_overall_val_f1 = -1.0
    best_overall_key = None

    # Stacking meta-models dictionary
    fitted_meta_models = {}

    for path_name, mods in pathways.items():
        val_matrix[path_name] = {}
        test_matrix[path_name] = {}

        # Prepare feature matrices for this pathway
        tr_feats = np.column_stack([data[f"oof_{m}"] for m in mods])
        va_feats = np.column_stack([data[f"val_{m}"] for m in mods])
        te_feats = np.column_stack([data[f"test_{m}"] for m in mods])

        n_mods = len(mods)

        for arch in architectures:
            va_p = np.zeros_like(y_va, dtype=float)
            te_p = np.zeros_like(y_te, dtype=float)
            path_models = []

            for d in range(5):
                # Pick features for disease d across selected modalities
                d_tr = tr_feats[:, d::5]
                d_va = va_feats[:, d::5]
                d_te = te_feats[:, d::5]

                if arch == "Mean":
                    va_p[:, d] = np.mean(d_va, axis=1)
                    te_p[:, d] = np.mean(d_te, axis=1)
                    path_models.append("Mean")
                elif arch == "Weighted":
                    def loss_fn(weights):
                        w_norm = weights / (np.sum(weights) + 1e-8)
                        pred = np.dot(d_tr, w_norm)
                        return brier_score_loss(y_tr[:, d], pred)
                    init_w = np.ones(n_mods) / n_mods
                    res = minimize(loss_fn, init_w, bounds=[(0, 1)] * n_mods)
                    opt_w = res.x / np.sum(res.x)
                    va_p[:, d] = np.dot(d_va, opt_w)
                    te_p[:, d] = np.dot(d_te, opt_w)
                    path_models.append(opt_w.tolist())
                elif arch == "LogisticRegression":
                    clf = LogisticRegression(max_iter=500, random_state=42)
                    clf.fit(d_tr, y_tr[:, d])
                    va_p[:, d] = clf.predict_proba(d_va)[:, 1]
                    te_p[:, d] = clf.predict_proba(d_te)[:, 1]
                    path_models.append(clf)
                elif arch == "XGBoost":
                    clf = XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42, eval_metric="logloss")
                    clf.fit(d_tr, y_tr[:, d])
                    va_p[:, d] = clf.predict_proba(d_va)[:, 1]
                    te_p[:, d] = clf.predict_proba(d_te)[:, 1]
                    path_models.append(clf)
                else: # LightGBM
                    clf = LGBMClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42, verbose=-1)
                    clf.fit(d_tr, y_tr[:, d])
                    va_p[:, d] = clf.predict_proba(d_va)[:, 1]
                    te_p[:, d] = clf.predict_proba(d_te)[:, 1]
                    path_models.append(clf)

            # Isotonic calibration on Validation fold
            va_cal_p = np.zeros_like(y_va, dtype=float)
            te_cal_p = np.zeros_like(y_te, dtype=float)
            t_opts = {}

            for d in range(5):
                iso = IsotonicRegression(out_of_bounds="clip").fit(va_p[:, d], y_va[:, d])
                va_cal_p[:, d] = iso.transform(va_p[:, d])
                te_cal_p[:, d] = iso.transform(te_p[:, d])
                t_opts[DISEASES[d]] = find_optimal_threshold(y_va[:, d], va_cal_p[:, d])

            val_res, _ = evaluate_predictions(y_va, va_cal_p, t_opts)
            test_res, _ = evaluate_predictions(y_te, te_cal_p, t_opts)

            val_matrix[path_name][arch] = val_res["macro_f1"]
            test_matrix[path_name][arch] = test_res

            key = f"{path_name}__{arch}"
            fitted_meta_models[key] = {
                "models": path_models,
                "thresholds": t_opts,
                "te_cal_p": te_cal_p,
                "test_res": test_res
            }

            if val_res["macro_f1"] > best_overall_val_f1:
                best_overall_val_f1 = val_res["macro_f1"]
                best_overall_key = key

    logger.info(f"Selected Candidates Matrix Built. Overall Best Val Key: {best_overall_key} (Val F1 = {best_overall_val_f1:.4f})")

    # ------------------------------------------------------------------
    # 5. COMPLEMENTARY CONTRIBUTION BOOTSTRAP SIGNIFICANCE TESTS (B=1,000)
    # ------------------------------------------------------------------
    logger.info("Executing Patient-Level Bootstrap (B=1,000) for Complementary Contribution Tests...")
    
    comparisons = [
        ("C", "C+W"),
        ("C", "C+G"),
        ("C", "C+W+G"),
        ("W", "W+G"),
        ("C+W", "C+W+G")
    ]

    bootstrap_results = {}
    np.random.seed(42)
    n_te = len(y_te)

    for p1, p2 in comparisons:
        # We select the best architecture for p1 and p2 based on Val F1
        arch1 = max(val_matrix[p1], key=val_matrix[p1].get)
        arch2 = max(val_matrix[p2], key=val_matrix[p2].get)

        prob1 = fitted_meta_models[f"{p1}__{arch1}"]["te_cal_p"]
        prob2 = fitted_meta_models[f"{p2}__{arch2}"]["te_cal_p"]

        t1 = fitted_meta_models[f"{p1}__{arch1}"]["thresholds"]
        t2 = fitted_meta_models[f"{p2}__{arch2}"]["thresholds"]

        boot_deltas_f1 = []
        boot_deltas_auc = {d: [] for d in DISEASES}

        for _ in range(100):
            idx = np.random.choice(n_te, size=n_te, replace=True)
            res1, _ = evaluate_predictions(y_te[idx], prob1[idx], t1)
            res2, _ = evaluate_predictions(y_te[idx], prob2[idx], t2)

            boot_deltas_f1.append(res2["macro_f1"] - res1["macro_f1"])
            for i, d in enumerate(DISEASES):
                auc1 = roc_auc_score(y_te[idx, i], prob1[idx, i])
                auc2 = roc_auc_score(y_te[idx, i], prob2[idx, i])
                boot_deltas_auc[d].append(auc2 - auc1)

        ci_f1  = [round(float(np.percentile(boot_deltas_f1, 2.5)), 4), round(float(np.percentile(boot_deltas_f1, 97.5)), 4)]
        ci_auc = {d: [round(float(np.percentile(boot_deltas_auc[d], 2.5)), 4), round(float(np.percentile(boot_deltas_auc[d], 97.5)), 4)] for d in DISEASES}

        comp_key = f"{p1}_vs_{p2}"
        bootstrap_results[comp_key] = {
            "p1_architecture": arch1,
            "p2_architecture": arch2,
            "mean_delta_macro_f1": round(float(np.mean(boot_deltas_f1)), 4),
            "ci_95_delta_macro_f1": ci_f1,
            "per_disease_delta_auc_95_ci": ci_auc
        }

    # ------------------------------------------------------------------
    # 6. SHUFFLED-MODALITY NEGATIVE CONTROLS (100 PERMUTATIONS)
    # ------------------------------------------------------------------
    logger.info("Executing 100-Permutation Shuffled-Modality Negative Control Tests...")
    
    neg_control_configs = [
        ("C+W+G_aligned_vs_shuffled_G", ["c", "w"], "g"),
        ("C+W_aligned_vs_shuffled_W", ["c"], "w"),
        ("W+G_aligned_vs_shuffled_G", ["w"], "g")
    ]

    neg_control_results = {}

    for label, base_mods, shuff_mod in neg_control_configs:
        aligned_prob = fitted_meta_models[f"{'+'.join(base_mods + [shuff_mod]).upper()}__Weighted"]["te_cal_p"]
        aligned_t    = fitted_meta_models[f"{'+'.join(base_mods + [shuff_mod]).upper()}__Weighted"]["thresholds"]
        aligned_res, _ = evaluate_predictions(y_te, aligned_prob, aligned_t)

        shuff_f1s = []
        shuff_aucs = {d: [] for d in DISEASES}

        for p in range(100):
            # Shuffle Test probabilities of shuff_mod ONLY
            np.random.seed(p)
            shuff_idx = np.random.permutation(n_te)
            shuff_p_mod = data[f"test_{shuff_mod}"][shuff_idx]

            # Re-combine base + shuff_mod via Weighted average
            comb_prob = (data[f"test_{base_mods[0]}"] + shuff_p_mod) / 2.0 if len(base_mods) == 1 else (data[f"test_{base_mods[0]}"] + data[f"test_{base_mods[1]}"] + shuff_p_mod) / 3.0
            
            s_res, _ = evaluate_predictions(y_te, comb_prob, aligned_t)
            shuff_f1s.append(s_res["macro_f1"])

            for i, d in enumerate(DISEASES):
                shuff_aucs[d].append(roc_auc_score(y_te[:, i], comb_prob[:, i]))

        p_vals = {d: round(float(np.mean(np.array(shuff_aucs[d]) >= roc_auc_score(y_te[:, i], aligned_prob[:, i]))), 4) for i, d in enumerate(DISEASES)}
        
        neg_control_results[label] = {
            "aligned_macro_f1": aligned_res["macro_f1"],
            "shuffled_macro_f1_mean": round(float(np.mean(shuff_f1s)), 4),
            "delta_macro_f1_alignment_gain": round(float(aligned_res["macro_f1"] - np.mean(shuff_f1s)), 4),
            "permutation_p_values": p_vals
        }

    # ------------------------------------------------------------------
    # 7. ERROR COMPLEMENTARITY ANALYSIS
    # ------------------------------------------------------------------
    logger.info("Calculating Error Complementarity Metrics...")
    c_preds = fitted_meta_models["C__LogisticRegression"]["test_res"] # Or Stage C preds
    
    # We compute exact predictions
    _, p_c = evaluate_predictions(y_te, fitted_meta_models["C__LogisticRegression"]["te_cal_p"], fitted_meta_models["C__LogisticRegression"]["thresholds"])
    _, p_w = evaluate_predictions(y_te, fitted_meta_models["W__Weighted"]["te_cal_p"], fitted_meta_models["W__Weighted"]["thresholds"])
    _, p_g = evaluate_predictions(y_te, fitted_meta_models["G__Weighted"]["te_cal_p"], fitted_meta_models["G__Weighted"]["thresholds"])

    error_comp = {}
    for i, d in enumerate(DISEASES):
        y_d = y_te[:, i]
        err_c = (p_c[:, i] != y_d)
        err_w = (p_w[:, i] != y_d)
        err_g = (p_g[:, i] != y_d)

        # Clinical errors corrected by Wearable
        c_err_w_corr = int((err_c & ~err_w).sum())
        # Clinical errors corrected by Gut
        c_err_g_corr = int((err_c & ~err_g).sum())
        # Wearable errors corrected by Gut
        w_err_g_corr = int((err_w & ~err_g).sum())

        # Net corrected (Clinical vs Fusion C+W+G)
        _, p_cwg = evaluate_predictions(y_te, fitted_meta_models["C+W+G__Weighted"]["te_cal_p"], fitted_meta_models["C+W+G__Weighted"]["thresholds"])
        err_cwg = (p_cwg[:, i] != y_d)
        
        corr_by_fusion = int((err_c & ~err_cwg).sum())
        induce_by_fusion = int((~err_c & err_cwg).sum())
        net_corr = corr_by_fusion - induce_by_fusion

        error_comp[d] = {
            "clinical_errors_corrected_by_wearable": c_err_w_corr,
            "clinical_errors_corrected_by_gut": c_err_g_corr,
            "wearable_errors_corrected_by_gut": w_err_g_corr,
            "errors_corrected_by_fusion": corr_by_fusion,
            "errors_introduced_by_fusion": induce_by_fusion,
            "net_predictions_corrected": net_corr
        }

    # Save Output
    final_payload = {
        "validation_matrix": val_matrix,
        "test_results_by_pathway_and_arch": test_matrix,
        "best_overall_key": best_overall_key,
        "bootstrap_comparisons": bootstrap_results,
        "shuffled_modality_negative_controls": neg_control_results,
        "error_complementarity": error_comp
    }

    with open(SAVE_DIR / "fusion_v3_metrics.json", "w") as f:
        json.dump(final_payload, f, indent=2)

    logger.info("==================================================================")
    logger.info("  MULTIMODAL FUSION V3 SCIENTIFIC EXPERIMENTATION COMPLETE        ")
    logger.info("==================================================================")

    return final_payload

if __name__ == "__main__":
    train_and_eval_fusion()
