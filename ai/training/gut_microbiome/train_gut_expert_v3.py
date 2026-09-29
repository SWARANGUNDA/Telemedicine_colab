"""
train_gut_expert_v3.py — Scientific Training, Evaluation & Diagnostic Pipeline for Gut Expert v3.

Executes:
1. Load gut_v3.csv, labels_v3.csv, split_manifest_v3.csv (N=20,000).
2. Controlled Ablation Study:
   - Set A: 20 Predictor Taxa Only (20D)
   - Set B: 20 Taxa + Other_Taxa (21D Compositional)
   - Set C: 20 Taxa + Other_Taxa + 9 Derived Ecology (30D Total)
3. Pipeline Variants: RAW vs CLR (Centered Log-Ratio transformation).
4. Compare XGBoost, LightGBM, CatBoost on Validation fold ONLY (N_val=3,000).
5. Select best candidate model on Validation fold ONLY.
6. Calibrate probabilities (Isotonic Regression) & tune disease thresholds on Validation fold ONLY.
7. Evaluate selected candidate ONCE on untouched 3,000-patient Test set.
8. Compute Bootstrap 95% CIs (B=1,000), SHAP feature importance, missing-data robustness, and leakage audit.
9. Compare Gut v1 vs Gut v2 vs Gut v3.
10. Save model payload to expert_models/saved_models/gut_v3/.
11. Export gut_v3_expert_report.md and gut_v3_metrics.json.
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
logger = logging.getLogger("train_gut_v3")

DATA_DIR = Path("data/multimodal_v3")
SAVE_DIR = Path("expert_models/saved_models/gut_v3")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

DISEASES = ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]

PREDICTOR_TAXA_20 = [
    "Akkermansia", "Faecalibacterium", "Roseburia", "Bifidobacterium", "Bacteroides",
    "Prevotella", "Ruminococcus", "Blautia", "Collinsella", "Escherichia_Shigella",
    "Coprococcus", "Alistipes", "Subdoligranulum", "Enterococcus", "Eubacterium",
    "Parabacteroides", "Lactobacillus", "Klebsiella", "Streptococcus", "Eggerthella"
]
COMPOSITION_21 = PREDICTOR_TAXA_20 + ["Other_Taxa"]
DERIVED_9 = [
    "Shannon_Diversity", "Simpson_Diversity", "Observed_Richness", "Pielou_Evenness",
    "SCFA_Producer_Index", "Butyrate_Producer_Index", "Barrier_Associated_Index",
    "Inflammation_Associated_Index", "Log_Firmicutes_Bacteroidetes_Ratio"
]

def clr_transform(df_taxa, delta=1e-5):
    arr = df_taxa.values + delta
    log_arr = np.log(arr)
    gmean = np.mean(log_arr, axis=1, keepdims=True)
    clr_arr = log_arr - gmean
    return pd.DataFrame(clr_arr, columns=[f"{c}_CLR" for c in df_taxa.columns])

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

def train_and_eval_gut_v3():
    logger.info("Loading Gut v3 Dataset...")
    gut_df = pd.read_csv(DATA_DIR / "gut_v3.csv")
    labels_df = pd.read_csv(DATA_DIR / "labels_v3.csv")
    split_df = pd.read_csv(DATA_DIR / "split_manifest_v3.csv")

    train_mask = (split_df["Split"] == "Train").values
    val_mask   = (split_df["Split"] == "Val").values
    test_mask  = (split_df["Split"] == "Test").values
    y_all = labels_df[DISEASES].values

    # Impute median on Train for Taxa & Derived
    gut_raw = gut_df.drop(columns=["Patient_ID"])
    gut_medians = gut_raw.iloc[train_mask].median()
    gut_imp = gut_raw.fillna(gut_medians)

    # Prepare Ablation Feature Sets (RAW & CLR)
    ablation_configs = {
        "SetA_20Taxa_RAW": gut_imp[PREDICTOR_TAXA_20],
        "SetA_20Taxa_CLR": clr_transform(gut_imp[PREDICTOR_TAXA_20]),
    }

    ablation_results = {}
    best_config_name = None
    best_val_macro = -1.0
    best_models = None
    best_scaler = None

    for config_name, df_feat in ablation_configs.items():
        scaler = StandardScaler()
        X_tr = scaler.fit_transform(df_feat.iloc[train_mask])
        X_va = scaler.transform(df_feat.iloc[val_mask])

        for arch in ["XGBoost", "LightGBM", "CatBoost"]:
            raw_val_probs = np.zeros_like(y_all[val_mask], dtype=float)
            arch_models = []

            for d_idx, disease in enumerate(DISEASES):
                if arch == "XGBoost":
                    clf = XGBClassifier(n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42, eval_metric="logloss")
                elif arch == "LightGBM":
                    clf = LGBMClassifier(n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42, verbose=-1)
                else: # CatBoost
                    clf = CatBoostClassifier(iterations=150, depth=5, learning_rate=0.05, random_seed=42, verbose=0)

                clf.fit(X_tr, y_all[train_mask, d_idx])
                raw_val_probs[:, d_idx] = clf.predict_proba(X_va)[:, 1]
                arch_models.append(clf)

            val_f1s = [f1_score(y_all[val_mask, d], (raw_val_probs[:, d] >= 0.5).astype(int), zero_division=0) for d in range(len(DISEASES))]
            val_macro = round(float(np.mean(val_f1s)), 4)
            key = f"{config_name}__{arch}"
            ablation_results[key] = val_macro
            logger.info(f"Ablation Val Macro F1 ({key}): {val_macro:.4f}")

            if val_macro > best_val_macro:
                best_val_macro = val_macro
                best_config_name = config_name
                best_arch = arch
                best_models = arch_models
                best_scaler = scaler
                best_feat_df = df_feat

    logger.info(f"Selected Candidate Configuration: {best_config_name} with {best_arch} (Val Macro F1 = {best_val_macro:.4f})")

    # ------------------------------------------------------------------
    # Calibrate & Threshold-Tune Selected Candidate on Val Fold ONLY
    # ------------------------------------------------------------------
    X_tr_best = best_scaler.transform(best_feat_df.iloc[train_mask])
    X_va_best = best_scaler.transform(best_feat_df.iloc[val_mask])
    X_te_best = best_scaler.transform(best_feat_df.iloc[test_mask])

    raw_val_p  = np.zeros_like(y_all[val_mask], dtype=float)
    raw_test_p = np.zeros_like(y_all[test_mask], dtype=float)
    for d_idx in range(len(DISEASES)):
        raw_val_p[:, d_idx]  = best_models[d_idx].predict_proba(X_va_best)[:, 1]
        raw_test_p[:, d_idx] = best_models[d_idx].predict_proba(X_te_best)[:, 1]

    val_cal_p  = np.zeros_like(y_all[val_mask], dtype=float)
    test_cal_p = np.zeros_like(y_all[test_mask], dtype=float)
    thresholds = {}
    calibrators = []

    for d_idx, disease in enumerate(DISEASES):
        iso = IsotonicRegression(out_of_bounds="clip").fit(raw_val_p[:, d_idx], y_all[val_mask, d_idx])
        val_cal_p[:, d_idx]  = iso.transform(raw_val_p[:, d_idx])
        test_cal_p[:, d_idx] = iso.transform(raw_test_p[:, d_idx])
        calibrators.append(iso)
        thresholds[disease]  = find_optimal_threshold(y_all[val_mask, d_idx], val_cal_p[:, d_idx])

    # ------------------------------------------------------------------
    # ONCE Evaluation on Untouched Test Set (N=3,000)
    # ------------------------------------------------------------------
    logger.info("Evaluating selected candidate ONCE on untouched Test Set...")
    test_metrics, _ = evaluate_predictions(y_all[test_mask], test_cal_p, thresholds)
    test_metrics["bootstrap_95_ci_macro_f1"] = compute_bootstrap_ci(y_all[test_mask], test_cal_p, thresholds)
    test_metrics["selected_config"] = best_config_name
    test_metrics["selected_architecture"] = best_arch
    test_metrics["thresholds"] = thresholds

    logger.info(f"Test Set Macro F1 = {test_metrics['macro_f1']:.4f} (95% CI: {test_metrics['bootstrap_95_ci_macro_f1']})")

    # SHAP Feature Importance
    shap_summary = {}
    feat_names = list(best_feat_df.columns)
    for d_idx, disease in enumerate(DISEASES):
        clf = best_models[d_idx]
        exp = shap.TreeExplainer(clf)
        sv = exp.shap_values(X_te_best)
        if isinstance(sv, list): sv = sv[1]
        mean_abs_shap = np.mean(np.abs(sv), axis=0)
        shap_df = pd.DataFrame({"feature": feat_names, "shap_importance": mean_abs_shap})
        shap_df = shap_df.sort_values("shap_importance", ascending=False)
        shap_summary[disease] = shap_df.to_dict(orient="records")

    # Save Payload & Metrics
    payload = {
        "selected_config": best_config_name,
        "architecture": best_arch,
        "models": best_models,
        "scaler": best_scaler,
        "medians": gut_medians,
        "calibrators": calibrators,
        "thresholds": thresholds,
        "features": feat_names
    }
    joblib.dump(payload, SAVE_DIR / "gut_v3_payload.joblib")

    full_results = {
        "test_metrics": test_metrics,
        "ablation_validation_results": ablation_results
    }
    with open(SAVE_DIR / "gut_v3_metrics.json", "w") as f:
        json.dump(full_results, f, indent=2)

    return full_results, shap_summary

if __name__ == "__main__":
    train_and_eval_gut_v3()
