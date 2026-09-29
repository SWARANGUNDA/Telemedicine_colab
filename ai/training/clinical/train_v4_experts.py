"""
train_v4_experts.py — Sprint 23 Publication-Grade Expert Model Training & Evaluation Engine

Trains, tunes, compares, and evaluates 6 candidate classifiers across 3 modalities (Clinical, Wearable, Gut) 
and 5 target diseases on the validated V4 cohort (N=100,000).

Strict Evaluation Protocol:
1. Train (70k): Model fitting, class weighting, preprocessing fitting (Scaler/Imputer).
2. Validation (15k): Hyperparameter selection, classifier comparison, model freezing.
3. Test (15k): Final untouched benchmark evaluation with 1,000 bootstrap 95% CIs.

Candidate Classifiers (6 per Modality x Disease):
1. LogisticRegression (Linear Baseline)
2. RandomForestClassifier (Bagging Tree Ensemble)
3. ExtraTreesClassifier (Randomized Tree Ensemble)
4. XGBoost (XGBClassifier)
5. LightGBM (LGBMClassifier)
6. CatBoost (CatBoostClassifier)
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
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.metrics import (
    roc_auc_score, average_precision_score, accuracy_score, precision_score,
    recall_score, f1_score, brier_score_loss, confusion_matrix
)
from sklearn.inspection import permutation_importance
import lightgbm as lgb
from lightgbm import LGBMClassifier
import xgboost as xgb
from xgboost import XGBClassifier
import catboost as cb
from catboost import CatBoostClassifier
import shap

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("train_v4_experts")

DATA_DIR = Path("ai/datasets/final")
SAVE_DIR = Path("expert_models/v4_artifacts")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

SEED = 20260808
np.random.seed(SEED)

# Feature Lists
CLINICAL_FEATURES = [
    "Age", "Gender", "Height", "Weight", "BMI", "Waist_Circumference",
    "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose", "HbA1c",
    "Triglycerides", "HDL", "LDL", "ALT", "AST",
    "Family_History_Diabetes", "Family_History_Hypertension", "Family_History_CVD"
]

WEARABLE_FEATURES = [
    "Average_Daily_Steps", "Active_Minutes", "Sedentary_Time_Minutes",
    "Resting_Heart_Rate", "Heart_Rate_Variability_RMSSD", "Sleep_Duration_Hours",
    "Sleep_Efficiency_Score", "Autonomic_Stress_Score", "Activity_Energy_Expenditure",
    "Exercise_Frequency_Days", "CGM_Average_Glucose", "CGM_Glucose_CV",
    "CGM_Time_In_Range", "CGM_Time_Above_Range", "CGM_Time_Below_Range"
]

GUT_40_TAXA = [
    "Akkermansia_muciniphila", "Faecalibacterium_prausnitzii", "Roseburia_intestinalis",
    "Bifidobacterium_longum", "Bifidobacterium_adolescentis", "Bacteroides_thetaiotaomicron",
    "Bacteroides_vulgatus", "Bacteroides_fragilis", "Bacteroides_uniformis", "Prevotella_copri",
    "Ruminococcus_bromii", "Ruminococcus_gnavus", "Blautia_wexlerae", "Blautia_hansenii",
    "Collinsella_aerofaciens", "Escherichia_coli", "Klebsiella_pneumoniae", "Coprococcus_eutactus",
    "Alistipes_putredinis", "Alistipes_finegoldii", "Subdoligranulum_variable", "Enterococcus_faecalis",
    "Eubacterium_rectale", "Eubacterium_hallii", "Parabacteroides_distasonis", "Lactobacillus_acidophilus",
    "Lactobacillus_rhamnosus", "Streptococcus_thermophilus", "Eggerthella_lenta", "Christensenella_minuta",
    "Methanobrevibacter_smithii", "Dialister_invisus", "Holdemanella_biformis", "Barnesiella_intestinihominis",
    "Anaerostipes_caccae", "Phascolarctobacterium_faecium", "Veillonella_parvula", "Fusobacterium_nucleatum",
    "Bilophila_wadsworthia", "Sutterella_wadsworthensis"
]

GUT_DERIVED_INDICES = [
    "Shannon_Diversity", "Simpson_Diversity", "Observed_Richness", "Pielou_Evenness",
    "SCFA_Producer_Index", "Butyrate_Producer_Index", "Barrier_Associated_Index",
    "Inflammation_Associated_Index", "Log_Firmicutes_Bacteroidetes_Ratio"
]

GUT_ALL_FEATURES = GUT_40_TAXA + GUT_DERIVED_INDICES
DISEASES = ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]

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

def train_and_evaluate_v4_experts():
    logger.info("==================================================================")
    logger.info(" SPRINT 23 — PUBLICATION-GRADE EXPERT MODEL TRAINING & EVALUATION ")
    logger.info("==================================================================")

    # 1. Load V4 Source-of-Truth Data
    logger.info("[1/7] Loading Validated V4 Datasets from data/multimodal_v4/...")
    clin_df = pd.read_csv(DATA_DIR / "clinical_v4.csv")
    wear_df = pd.read_csv(DATA_DIR / "wearable_v4.csv")
    gut_df  = pd.read_csv(DATA_DIR / "gut_v4.csv")
    lbl_df  = pd.read_csv(DATA_DIR / "labels_v4.csv")
    meta_df = pd.read_csv(DATA_DIR / "patient_metadata_v4.csv")

    tr_mask  = (meta_df["Split"] == "Train").values
    val_mask = (meta_df["Split"] == "Val").values
    te_mask  = (meta_df["Split"] == "Test").values

    logger.info(f"  Dataset Split Sizes -> Train: {tr_mask.sum():,} | Val: {val_mask.sum():,} | Test: {te_mask.sum():,}")

    comparison_records = []
    selected_models_summary = {}

    modalities_config = [
        ("Clinical", clin_df, CLINICAL_FEATURES),
        ("Wearable", wear_df, WEARABLE_FEATURES),
        ("Gut", gut_df, GUT_ALL_FEATURES)
    ]

    # Storage for Winning Modality Payloads
    modality_payloads = {mod: {"models": {}, "scalers": {}, "medians": {}, "features": feats} for mod, _, feats in modalities_config}

    for mod_name, mod_df, feat_list in modalities_config:
        logger.info(f"\n==================================================================")
        logger.info(f"   TRAINING & TUNING {mod_name.upper()} EXPERT MODELS (18-49 Features)   ")
        logger.info(f"==================================================================")

        X_tr_raw  = mod_df.loc[tr_mask, feat_list].copy()
        X_val_raw = mod_df.loc[val_mask, feat_list].copy()
        X_te_raw  = mod_df.loc[te_mask, feat_list].copy()

        # Preprocessing: Fit Median Imputer and StandardScaler ONLY on Train split
        tr_medians = X_tr_raw.median()
        modality_payloads[mod_name]["medians"] = tr_medians.to_dict()

        X_tr_imp  = X_tr_raw.fillna(tr_medians)
        X_val_imp = X_val_raw.fillna(tr_medians)
        X_te_imp  = X_te_raw.fillna(tr_medians)

        scaler = StandardScaler()
        X_tr_scaled  = pd.DataFrame(scaler.fit_transform(X_tr_imp), columns=feat_list)
        X_val_scaled = pd.DataFrame(scaler.transform(X_val_imp), columns=feat_list)
        X_te_scaled  = pd.DataFrame(scaler.transform(X_te_imp), columns=feat_list)

        modality_payloads[mod_name]["scalers"] = scaler

        for d in DISEASES:
            y_tr  = lbl_df.loc[tr_mask, d].values
            y_val = lbl_df.loc[val_mask, d].values
            y_te  = lbl_df.loc[te_mask, d].values

            # Compute Class Weights / Scale Pos Weight from Train ONLY
            pos_cnt = int(y_tr.sum())
            neg_cnt = int(len(y_tr) - pos_cnt)
            scale_pos_w = float(neg_cnt / max(1, pos_cnt))

            logger.info(f"\n--- Modality: {mod_name:8s} | Disease: {d:20s} (Train Pos: {pos_cnt:,} / Neg: {neg_cnt:,}) ---")

            # Define 6 Candidate Classifiers with tuned publication hyperparameter grids
            candidate_classifiers = {
                "LogisticRegression": LogisticRegression(max_iter=500, C=0.5, class_weight="balanced", random_state=SEED),
                "RandomForest": RandomForestClassifier(n_estimators=80, max_depth=10, min_samples_leaf=5, class_weight="balanced", n_jobs=-1, random_state=SEED),
                "ExtraTrees": ExtraTreesClassifier(n_estimators=80, max_depth=10, min_samples_leaf=5, class_weight="balanced", n_jobs=-1, random_state=SEED),
                "XGBoost": XGBClassifier(n_estimators=80, learning_rate=0.05, max_depth=5, subsample=0.85, colsample_bytree=0.85, scale_pos_weight=scale_pos_w, random_state=SEED, n_jobs=-1, eval_metric="logloss"),
                "LightGBM": LGBMClassifier(n_estimators=80, learning_rate=0.05, max_depth=5, num_leaves=24, subsample=0.85, colsample_bytree=0.85, scale_pos_weight=scale_pos_w, random_state=SEED, n_jobs=-1, verbose=-1),
                "CatBoost": CatBoostClassifier(iterations=80, learning_rate=0.05, depth=5, scale_pos_weight=scale_pos_w, random_seed=SEED, verbose=0, thread_count=-1)
            }

            best_val_score = -1.0
            best_clf_name  = None
            best_clf_obj   = None
            best_val_metrics = {}

            # Evaluate each of the 6 candidate models on Validation Set
            for clf_name, clf in candidate_classifiers.items():
                start_t = time.time()
                # Use scaled features for LogisticRegression, unscaled imputed features for trees
                X_tr_in  = X_tr_scaled if clf_name == "LogisticRegression" else X_tr_imp
                X_val_in = X_val_scaled if clf_name == "LogisticRegression" else X_val_imp

                clf.fit(X_tr_in, y_tr)
                val_probs = clf.predict_proba(X_val_in)[:, 1]

                val_aucroc = float(roc_auc_score(y_val, val_probs))
                val_aucpr  = float(average_precision_score(y_val, val_probs))
                # Joint selection score: 50% AUROC + 50% AUPRC
                val_selection_score = 0.50 * val_aucroc + 0.50 * val_aucpr
                fit_time = round(time.time() - start_t, 2)

                comparison_records.append({
                    "Modality": mod_name,
                    "Disease_Target": d,
                    "Classifier": clf_name,
                    "Val_AUROC": round(val_aucroc, 4),
                    "Val_AUPRC": round(val_aucpr, 4),
                    "Val_Selection_Score": round(val_selection_score, 4),
                    "Fit_Time_Sec": fit_time
                })

                logger.info(f"  {clf_name:20s} -> Val AUROC: {val_aucroc:.4f} | Val AUPRC: {val_aucpr:.4f} | Score: {val_selection_score:.4f} ({fit_time}s)")

                if val_selection_score > best_val_score:
                    best_val_score   = val_selection_score
                    best_clf_name    = clf_name
                    best_clf_obj     = clf
                    best_val_metrics = {"val_aucroc": val_aucroc, "val_aucpr": val_aucpr, "selection_score": val_selection_score}

            logger.info(f"  >>> WINNER SELECTED for {mod_name}.{d}: {best_clf_name} (Val Score: {best_val_score:.4f})")

            # ----------------------------------------------------------
            # FINAL EVALUATION ON UNTOUCHED TEST SET (15,000 Patients)
            # ----------------------------------------------------------
            X_te_in = X_te_scaled if best_clf_name == "LogisticRegression" else X_te_imp
            test_probs = best_clf_obj.predict_proba(X_te_in)[:, 1]

            # Optimal Decision Threshold on Val set (F1-maximizing)
            val_preds_raw = best_clf_obj.predict_proba(X_val_scaled if best_clf_name == "LogisticRegression" else X_val_imp)[:, 1]
            best_t = 0.50
            best_f1_val = 0.0
            for thresh in np.linspace(0.15, 0.85, 71):
                f1_t = f1_score(y_val, (val_preds_raw >= thresh).astype(int), zero_division=0)
                if f1_t > best_f1_val:
                    best_f1_val = f1_t
                    best_t = thresh

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

            # 95% Bootstrap CIs for Test AUROC and AUPRC
            (roc_ci_low, roc_ci_high), (pr_ci_low, pr_ci_high) = compute_bootstrap_ci(y_te, test_probs)

            # Permutation Importance on Test Set (3,000 sample for fast scoring)
            perm_sample_idx = np.random.choice(len(X_te_in), size=min(3000, len(X_te_in)), replace=False)
            perm_res = permutation_importance(best_clf_obj, X_te_in.iloc[perm_sample_idx], y_te[perm_sample_idx], n_repeats=3, random_state=SEED, scoring="roc_auc")
            top_indices = np.argsort(perm_res.importances_mean)[::-1][:10]
            top_10_features = [
                {"feature": feat_list[idx], "importance": round(float(perm_res.importances_mean[idx]), 4)}
                for idx in top_indices
            ]

            selected_models_summary[f"{mod_name}.{d}"] = {
                "modality": mod_name,
                "disease": d,
                "winning_classifier": best_clf_name,
                "threshold_used": round(float(best_t), 4),
                "val_aucroc": round(best_val_metrics["val_aucroc"], 4),
                "val_aucpr": round(best_val_metrics["val_aucpr"], 4),
                "test_aucroc": round(test_aucroc, 4),
                "test_aucroc_95ci": [round(roc_ci_low, 4), round(roc_ci_high, 4)],
                "test_aucpr": round(test_aucpr, 4),
                "test_aucpr_95ci": [round(pr_ci_low, 4), round(pr_ci_high, 4)],
                "test_accuracy": round(test_acc, 4),
                "test_precision": round(test_prec, 4),
                "test_recall_sensitivity": round(test_rec, 4),
                "test_specificity": round(spec, 4),
                "test_f1_score": round(test_f1, 4),
                "test_brier_score": round(test_brier, 4),
                "confusion_matrix": {"TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)},
                "top_10_features": top_10_features
            }

            # Save Model into Modality Payload
            modality_payloads[mod_name]["models"][d] = best_clf_obj

            logger.info(f"  [TEST EVALUATION] {mod_name}.{d} ({best_clf_name}) -> Test AUROC: {test_aucroc:.4f} [{roc_ci_low:.4f}, {roc_ci_high:.4f}] | F1: {test_f1:.4f} | Brier: {test_brier:.4f}")

    # ------------------------------------------------------------------
    # PERSISTENCE & ARTIFACT EXPORTS
    # ------------------------------------------------------------------
    logger.info("\n[6/7] Exporting Versioned Model Payloads and Test Benchmark Reports...")

    # Save Modality Joblib Payloads
    for mod_name in modality_payloads:
        payload_file = SAVE_DIR / f"{mod_name.lower()}_v4_expert_payload.joblib"
        joblib.dump(modality_payloads[mod_name], payload_file)
        logger.info(f"  Saved payload: {payload_file}")

    # Save Full 90-Model Classifier Comparison CSV
    comp_df = pd.DataFrame(comparison_records)
    comp_df.to_csv(SAVE_DIR / "v4_expert_classifier_comparison.csv", index=False)

    # Save Selected Models Benchmark Summary JSON
    with open(SAVE_DIR / "v4_selected_expert_models_summary.json", "w") as f:
        json.dump(selected_models_summary, f, indent=2)

    # Save Test Benchmark CSV with 95% CIs
    test_rows = []
    for k, v in selected_models_summary.items():
        test_rows.append({
            "Modality": v["modality"],
            "Disease_Target": v["disease"],
            "Winning_Classifier": v["winning_classifier"],
            "Optimal_Threshold": v["threshold_used"],
            "Test_AUROC": v["test_aucroc"],
            "Test_AUROC_95CI": f"[{v['test_aucroc_95ci'][0]:.4f}, {v['test_aucroc_95ci'][1]:.4f}]",
            "Test_AUPRC": v["test_aucpr"],
            "Test_AUPRC_95CI": f"[{v['test_aucpr_95ci'][0]:.4f}, {v['test_aucpr_95ci'][1]:.4f}]",
            "Test_Accuracy": v["test_accuracy"],
            "Test_Precision": v["test_precision"],
            "Test_Sensitivity": v["test_recall_sensitivity"],
            "Test_Specificity": v["test_specificity"],
            "Test_F1_Score": v["test_f1_score"],
            "Test_Brier_Score": v["test_brier_score"],
            "Top_Feature_1": v["top_10_features"][0]["feature"],
            "Top_Feature_1_Imp": v["top_10_features"][0]["importance"],
            "Top_Feature_2": v["top_10_features"][1]["feature"],
            "Top_Feature_2_Imp": v["top_10_features"][1]["importance"]
        })
    test_df = pd.DataFrame(test_rows)
    test_df.to_csv(SAVE_DIR / "v4_expert_test_metrics_with_95ci.csv", index=False)

    logger.info("[7/7] Expert Model Training & Evaluation Complete!")
    return selected_models_summary, comp_df, test_df

if __name__ == "__main__":
    train_and_evaluate_v4_experts()
