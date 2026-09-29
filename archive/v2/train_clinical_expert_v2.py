"""
train_clinical_expert_v2.py — Clinical Expert v2 Training & Phase C Experimentation Engine.

Executes Phase C:
- Trains XGBoost, LightGBM, CatBoost on Train fold (14,000)
- Selects optimal candidate on Validation fold (3,000)
- Performs Isotonic probability calibration & threshold tuning on Validation fold
- Evaluates untouched Test set (3,000) ONCE with 1,000-sample bootstrap CIs
- Executes rule-reconstruction diagnostic feature ablations
- Performs Prediabetes & Controlled T2D subgroup analysis
- Computes global & local SHAP feature importances
- Saves models to expert_models/saved_models/clinical_v2/
"""

import os
import json
import logging
import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.metrics import (
    f1_score, precision_score, recall_score, roc_auc_score,
    precision_recall_curve, auc, brier_score_loss, confusion_matrix, hamming_loss
)
from sklearn.isotonic import IsotonicRegression
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

from .preprocessing import ExpertPreprocessor
from .threshold_tuner import find_optimal_threshold_for_disease
from .calibration import DiseaseProbabilityCalibrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("clinical_v2_trainer")

PREDICTOR_COLS = [
    "Age", "Gender", "Height", "Weight", "BMI", "Waist_Circumference",
    "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose", "HbA1c",
    "Triglycerides", "HDL", "LDL", "ALT", "AST",
    "Family_History_Diabetes", "Family_History_Hypertension", "Family_History_CVD"
]

TARGET_DISEASES = ["Type2_Diabetes", "Prediabetes", "Obesity", "Metabolic_Syndrome", "NAFLD"]
SAVED_MODEL_DIR = "expert_models/saved_models/clinical_v2"


def compute_pr_auc(y_true, y_prob):
    p, r, _ = precision_recall_curve(y_true, y_prob)
    return float(auc(r, p))


def train_and_evaluate_v2():
    os.makedirs(SAVED_MODEL_DIR, exist_ok=True)
    df_v2 = pd.read_csv("Clinical_Dataset_v2.csv")

    n_total = len(df_v2)
    n_train = 14000
    n_val   = 3000
    n_test  = 3000

    train_df = df_v2.iloc[:n_train].copy()
    val_df   = df_v2.iloc[n_train:n_train+n_val].copy()
    test_df  = df_v2.iloc[n_train+n_val:].copy()

    logger.info(f"Loaded Clinical Dataset v2: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")

    # ── Step 1: Preprocessing ──
    preprocessor = ExpertPreprocessor(feature_order=PREDICTOR_COLS)
    X_train = preprocessor.fit_transform(train_df[PREDICTOR_COLS])
    X_val   = preprocessor.transform(val_df[PREDICTOR_COLS])
    X_test  = preprocessor.transform(test_df[PREDICTOR_COLS])

    y_train = train_df[TARGET_DISEASES].values
    y_val   = val_df[TARGET_DISEASES].values
    y_test  = test_df[TARGET_DISEASES].values

    # ── Step 2: Architecture Comparison on Validation Set ──
    architectures = {
        "XGBoost": lambda: XGBClassifier(n_estimators=150, max_depth=4, learning_rate=0.05, random_state=42, eval_metric="logloss"),
        "LightGBM": lambda: LGBMClassifier(n_estimators=150, max_depth=4, learning_rate=0.05, random_state=42, verbose=-1),
        "CatBoost": lambda: CatBoostClassifier(iterations=200, depth=4, learning_rate=0.05, random_seed=42, verbose=0)
    }

    arch_val_results = {}
    fitted_models = {}

    for arch_name, clf_fn in architectures.items():
        logger.info(f"Evaluating architecture: {arch_name}...")
        arch_val_results[arch_name] = {}
        fitted_models[arch_name] = {}

        val_f1s = []
        for idx, target in enumerate(TARGET_DISEASES):
            model = clf_fn()
            model.fit(X_train, y_train[:, idx])
            val_probs = model.predict_proba(X_val)[:, 1]
            val_preds = (val_probs >= 0.50).astype(int)

            f1 = f1_score(y_val[:, idx], val_preds, zero_division=0)
            roc = roc_auc_score(y_val[:, idx], val_probs)
            pr  = compute_pr_auc(y_val[:, idx], val_probs)
            brier = brier_score_loss(y_val[:, idx], val_probs)

            val_f1s.append(f1)
            arch_val_results[arch_name][target] = {
                "val_f1": round(float(f1), 4),
                "val_roc": round(float(roc), 4),
                "val_pr": round(float(pr), 4),
                "val_brier": round(float(brier), 4)
            }
            fitted_models[arch_name][target] = model

        arch_val_results[arch_name]["macro_f1"] = round(float(np.mean(val_f1s)), 4)
        logger.info(f"{arch_name} Validation Macro F1 = {arch_val_results[arch_name]['macro_f1']}")

    # Select optimal architecture based on Validation Macro F1
    best_arch = max(arch_val_results.keys(), key=lambda k: arch_val_results[k]["macro_f1"])
    logger.info(f"Selected Candidate Architecture: {best_arch} (Val Macro F1 = {arch_val_results[best_arch]['macro_f1']})")

    best_uncalibrated_models = fitted_models[best_arch]

    # ── Step 3: Calibration & Threshold Tuning on Validation Set ──
    calibrated_models = {}
    val_calibrated_probs = np.zeros((len(val_df), len(TARGET_DISEASES)))

    for idx, target in enumerate(TARGET_DISEASES):
        uncal_model = best_uncalibrated_models[target]
        raw_val_p = uncal_model.predict_proba(X_val)[:, 1]

        iso = IsotonicRegression(out_of_bounds="clip")
        iso.fit(raw_val_p, y_val[:, idx])

        calibrated_models[target] = (uncal_model, iso)
        val_calibrated_probs[:, idx] = iso.transform(raw_val_p)

    # Threshold Tuning on Calibrated Validation Probabilities
    tuned_thresholds = {}
    for idx, target in enumerate(TARGET_DISEASES):
        t_opt = find_optimal_threshold_for_disease(y_val[:, idx], val_calibrated_probs[:, idx])
        tuned_thresholds[target] = round(float(t_opt), 4)
    logger.info(f"Tuned Validation Thresholds: {tuned_thresholds}")

    # ── Step 4: Single Final Evaluation on Untouched Test Set ──
    test_calibrated_probs = np.zeros((len(test_df), len(TARGET_DISEASES)))
    test_uncal_probs = np.zeros((len(test_df), len(TARGET_DISEASES)))

    for idx, target in enumerate(TARGET_DISEASES):
        uncal_model, iso = calibrated_models[target]
        raw_test_p = uncal_model.predict_proba(X_test)[:, 1]
        test_uncal_probs[:, idx] = raw_test_p
        test_calibrated_probs[:, idx] = iso.transform(raw_test_p)

    test_preds = np.zeros_like(test_calibrated_probs, dtype=int)
    for idx, target in enumerate(TARGET_DISEASES):
        thresh = tuned_thresholds[target]
        test_preds[:, idx] = (test_calibrated_probs[:, idx] >= thresh).astype(int)

    # Compute Test Metrics
    test_metrics = {}
    macro_f1 = f1_score(y_test, test_preds, average="macro")
    micro_f1 = f1_score(y_test, test_preds, average="micro")
    h_loss   = hamming_loss(y_test, test_preds)

    brier_scores = [brier_score_loss(y_test[:, i], test_calibrated_probs[:, i]) for i in range(len(TARGET_DISEASES))]
    mean_brier = float(np.mean(brier_scores))

    test_metrics["overall"] = {
        "macro_f1": round(float(macro_f1), 4),
        "micro_f1": round(float(micro_f1), 4),
        "hamming_loss": round(float(h_loss), 4),
        "mean_brier": round(float(mean_brier), 4)
    }

    per_disease_test = {}
    for idx, target in enumerate(TARGET_DISEASES):
        f1 = f1_score(y_test[:, idx], test_preds[:, idx])
        prec = precision_score(y_test[:, idx], test_preds[:, idx], zero_division=0)
        rec = recall_score(y_test[:, idx], test_preds[:, idx], zero_division=0)
        roc = roc_auc_score(y_test[:, idx], test_calibrated_probs[:, idx])
        pr  = compute_pr_auc(y_test[:, idx], test_calibrated_probs[:, idx])
        brier = brier_scores[idx]

        tn, fp, fn, tp = confusion_matrix(y_test[:, idx], test_preds[:, idx]).ravel()

        per_disease_test[target] = {
            "f1": round(float(f1), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "roc_auc": round(float(roc), 4),
            "pr_auc": round(float(pr), 4),
            "brier_score": round(float(brier), 4),
            "confusion_matrix": {"TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)}
        }

    test_metrics["per_disease"] = per_disease_test
    logger.info(f"Untouched Test Evaluation Frozen: Macro F1 = {macro_f1:.4f}, Micro F1 = {micro_f1:.4f}")

    # Bootstrap 95% CIs for Macro F1 (B=1,000)
    boot_macro_f1s = []
    rng = np.random.default_rng(42)
    n_test_samples = len(test_df)

    for _ in range(1000):
        boot_idx = rng.choice(n_test_samples, size=n_test_samples, replace=True)
        bf1 = f1_score(y_test[boot_idx], test_preds[boot_idx], average="macro")
        boot_macro_f1s.append(bf1)

    ci_low = float(np.percentile(boot_macro_f1s, 2.5))
    ci_high = float(np.percentile(boot_macro_f1s, 97.5))
    test_metrics["bootstrap_macro_f1_95ci"] = [round(ci_low, 4), round(ci_high, 4)]
    logger.info(f"Macro F1 95% Bootstrap CI: [{ci_low:.4f}, {ci_high:.4f}]")

    # ── Step 5: Save Models & Preprocessor ──
    for idx, target in enumerate(TARGET_DISEASES):
        uncal_m, iso_m = calibrated_models[target]
        model_payload = {
            "uncalibrated_model": uncal_m,
            "calibrator": iso_m,
            "threshold": tuned_thresholds[target],
            "feature_names": PREDICTOR_COLS
        }
        joblib.dump(model_payload, os.path.join(SAVED_MODEL_DIR, f"{target}_clinical_v2.joblib"))

    joblib.dump(preprocessor, os.path.join(SAVED_MODEL_DIR, "preprocessor_clinical_v2.joblib"))

    # ── Step 6: Diagnostic Feature Ablations ──
    logger.info("Executing Rule-Reconstruction Diagnostic Feature Ablation Study...")
    ablation_results = {}

    ablation_scenarios = {
        "Glycemic": {
            "Full": PREDICTOR_COLS,
            "No_FPG": [c for c in PREDICTOR_COLS if c != "Fasting_Blood_Glucose"],
            "No_HbA1c": [c for c in PREDICTOR_COLS if c != "HbA1c"],
            "No_FPG_No_HbA1c": [c for c in PREDICTOR_COLS if c not in ["Fasting_Blood_Glucose", "HbA1c"]]
        },
        "Obesity": {
            "Full": PREDICTOR_COLS,
            "No_BMI": [c for c in PREDICTOR_COLS if c != "BMI"],
            "No_BMI_No_Weight_No_Height": [c for c in PREDICTOR_COLS if c not in ["BMI", "Weight", "Height"]],
            "No_BMI_No_Weight_No_Height_No_Waist": [c for c in PREDICTOR_COLS if c not in ["BMI", "Weight", "Height", "Waist_Circumference"]]
        },
        "Metabolic_Syndrome": {
            "Full": PREDICTOR_COLS,
            "No_ATP_III_Criteria": [c for c in PREDICTOR_COLS if c not in ["Waist_Circumference", "Triglycerides", "HDL", "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose"]]
        },
        "NAFLD": {
            "Full": PREDICTOR_COLS,
            "No_ALT_AST": [c for c in PREDICTOR_COLS if c not in ["ALT", "AST"]],
            "No_ALT_AST_TG_BMI": [c for c in PREDICTOR_COLS if c not in ["ALT", "AST", "Triglycerides", "BMI"]]
        }
    }

    for domain, scenarios in ablation_scenarios.items():
        ablation_results[domain] = {}
        for scenario_name, feat_subset in scenarios.items():
            prep_ab = ExpertPreprocessor(feature_order=feat_subset)
            X_tr_ab = prep_ab.fit_transform(train_df[feat_subset])
            X_val_ab = prep_ab.transform(val_df[feat_subset])
            X_te_ab  = prep_ab.transform(test_df[feat_subset])

            target_list = (["Type2_Diabetes", "Prediabetes"] if domain == "Glycemic" else [domain])

            f1s = []
            for target in target_list:
                idx = TARGET_DISEASES.index(target)
                clf = XGBClassifier(n_estimators=150, max_depth=4, learning_rate=0.05, random_state=42, eval_metric="logloss")
                clf.fit(X_tr_ab, y_train[:, idx])
                val_p = clf.predict_proba(X_val_ab)[:, 1]

                iso_ab = IsotonicRegression(out_of_bounds="clip")
                iso_ab.fit(val_p, y_val[:, idx])
                cal_val_p = iso_ab.transform(val_p)

                # Tune threshold on val
                t_best = 0.50
                best_val_f1 = -1
                for t_cand in np.linspace(0.10, 0.90, 81):
                    cand_f1 = f1_score(y_val[:, idx], (cal_val_p >= t_cand).astype(int), zero_division=0)
                    if cand_f1 > best_val_f1:
                        best_val_f1 = cand_f1
                        t_best = t_cand

                # Evaluate test
                raw_te_p = clf.predict_proba(X_te_ab)[:, 1]
                cal_te_p = iso_ab.transform(raw_te_p)
                te_pred  = (cal_te_p >= t_best).astype(int)

                te_f1 = float(f1_score(y_test[:, idx], te_pred))
                f1s.append(te_f1)

            mean_f1 = float(np.mean(f1s))
            ablation_results[domain][scenario_name] = round(mean_f1, 4)
            logger.info(f"Ablation [{domain} -> {scenario_name}]: Test F1 = {mean_f1:.4f}")

    # ── Step 7: Subgroup Analyses (Prediabetes & Controlled T2D) ──
    subgroup_results = {}

    # Prediabetes Subgroups on Test Set
    predia_idx = TARGET_DISEASES.index("Prediabetes")
    predia_true = (y_test[:, predia_idx] == 1)
    predia_preds = test_preds[:, predia_idx]

    fpg_test   = test_df["Fasting_Blood_Glucose"].values
    hba1c_test = test_df["HbA1c"].values

    predia_concordant = predia_true & (fpg_test >= 100) & (fpg_test <= 125) & (hba1c_test >= 5.7) & (hba1c_test <= 6.4)
    predia_fpg_disc   = predia_true & (fpg_test < 100) & (hba1c_test >= 5.7) & (hba1c_test <= 6.4)
    predia_hba1c_disc = predia_true & (fpg_test >= 100) & (fpg_test <= 125) & (hba1c_test < 5.7)
    predia_outside    = predia_true & ~((fpg_test >= 100) & (fpg_test <= 125) | (hba1c_test >= 5.7) & (hba1c_test <= 6.4))

    subgroup_results["Prediabetes"] = {
        "concordant_recall": round(float(np.mean(predia_preds[predia_concordant] == 1)), 4) if np.sum(predia_concordant) > 0 else 0,
        "fpg_discordant_recall": round(float(np.mean(predia_preds[predia_fpg_disc] == 1)), 4) if np.sum(predia_fpg_disc) > 0 else 0,
        "hba1c_discordant_recall": round(float(np.mean(predia_preds[predia_hba1c_disc] == 1)), 4) if np.sum(predia_hba1c_disc) > 0 else 0,
        "outside_range_recall": round(float(np.mean(predia_preds[predia_outside] == 1)), 4) if np.sum(predia_outside) > 0 else 0,
        "counts": {
            "concordant": int(np.sum(predia_concordant)),
            "fpg_discordant": int(np.sum(predia_fpg_disc)),
            "hba1c_discordant": int(np.sum(predia_hba1c_disc)),
            "outside_range": int(np.sum(predia_outside))
        }
    }

    # Controlled T2D Subgroups on Test Set
    t2d_idx = TARGET_DISEASES.index("Type2_Diabetes")
    t2d_true  = (y_test[:, t2d_idx] == 1)
    t2d_preds = test_preds[:, t2d_idx]

    t2d_overt            = t2d_true & (fpg_test >= 126) & (hba1c_test >= 6.5)
    t2d_fpg_controlled   = t2d_true & (fpg_test < 126) & (hba1c_test >= 6.5)
    t2d_hba1c_controlled = t2d_true & (fpg_test >= 126) & (hba1c_test < 6.5)
    t2d_fully_controlled = t2d_true & (fpg_test < 126) & (hba1c_test < 6.5)

    subgroup_results["Type2_Diabetes"] = {
        "overt_recall": round(float(np.mean(t2d_preds[t2d_overt] == 1)), 4) if np.sum(t2d_overt) > 0 else 0,
        "fpg_controlled_recall": round(float(np.mean(t2d_preds[t2d_fpg_controlled] == 1)), 4) if np.sum(t2d_fpg_controlled) > 0 else 0,
        "hba1c_controlled_recall": round(float(np.mean(t2d_preds[t2d_hba1c_controlled] == 1)), 4) if np.sum(t2d_hba1c_controlled) > 0 else 0,
        "fully_controlled_recall": round(float(np.mean(t2d_preds[t2d_fully_controlled] == 1)), 4) if np.sum(t2d_fully_controlled) > 0 else 0,
        "counts": {
            "overt": int(np.sum(t2d_overt)),
            "fpg_controlled": int(np.sum(t2d_fpg_controlled)),
            "hba1c_controlled": int(np.sum(t2d_hba1c_controlled)),
            "fully_controlled": int(np.sum(t2d_fully_controlled))
        }
    }

    # ── Step 8: SHAP Interpretability Analysis ──
    logger.info("Computing SHAP Interpretability Values...")
    shap_results = {}
    for idx, target in enumerate(TARGET_DISEASES):
        uncal_m, _ = calibrated_models[target]
        explainer = shap.TreeExplainer(uncal_m)
        shap_vals = explainer.shap_values(X_test)
        if isinstance(shap_vals, list):
            shap_vals = shap_vals[1]

        mean_abs_shap = np.mean(np.abs(shap_vals), axis=0)
        sorted_feats = sorted(zip(PREDICTOR_COLS, mean_abs_shap), key=lambda x: x[1], reverse=True)
        shap_results[target] = {feat: round(float(val), 4) for feat, val in sorted_feats}

    # Save summary payload
    final_payload = {
        "architecture_comparison": arch_val_results,
        "selected_architecture": best_arch,
        "tuned_thresholds": tuned_thresholds,
        "test_metrics": test_metrics,
        "ablation_results": ablation_results,
        "subgroup_results": subgroup_results,
        "shap_results": shap_results
    }

    with open("clinical_v2_phase_c_summary.json", "w") as f:
        json.dump(final_payload, f, indent=2)

    logger.info("Phase C Training, Calibration, Ablation & SHAP complete. Saved to clinical_v2_phase_c_summary.json")
    return final_payload


if __name__ == "__main__":
    train_and_evaluate_v2()
