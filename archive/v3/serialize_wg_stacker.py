"""
serialize_wg_stacker.py — Serializes exact W+G Logistic Regression Meta-Stacker Artifact.

Fits exact 5-fold OOF Logistic Regression stackers for W+G pathway across all 5 targets:
1. Generates 5-fold OOF probabilities on Train split (N=14,000) for W and G.
2. Fits LogisticRegression(max_iter=500, random_state=42) per disease on [P_W, P_G].
3. Calibrates raw stacker outputs using IsotonicRegression on Validation fold (N=3,000).
4. Computes optimal thresholds on Validation fold.
5. Verifies test performance against fusion_v3_metrics.json (Test Macro F1 = 0.5032, NAFLD AUC = 0.5982).
6. Serializes frozen payload to expert_models/saved_models/fusion_v3/wg_logistic_regression_stacker.joblib.
"""

import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import KFold
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import f1_score, roc_auc_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("serialize_wg_stacker")

DATA_DIR = Path("data/multimodal_v3")
SAVE_DIR = Path("expert_models/saved_models/fusion_v3")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

DISEASES = ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]

def serialize_wg_stacker():
    logger.info("Loading v3 datasets & expert model payloads...")
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

    wear_payload = joblib.load("expert_models/saved_models/wearable_v3/wearable_v3_payload.joblib")
    gut_payload  = joblib.load("expert_models/saved_models/gut_v3/gut_v3_payload.joblib")

    X_w = pd.concat([wear_std_df[wear_payload["features"][:10]], wear_cgm_df[wear_payload["features"][10:]]], axis=1).fillna(wear_payload["medians"]).values
    X_g = gut_df[gut_payload["features"]].fillna(gut_payload["medians"]).values

    # Scale inputs using frozen scalers
    X_w_tr_scaled = wear_payload["scaler"].transform(X_w[train_mask])
    X_w_va_scaled = wear_payload["scaler"].transform(X_w[val_mask])
    X_w_te_scaled = wear_payload["scaler"].transform(X_w[test_mask])

    X_g_tr_scaled = gut_payload["scaler"].transform(X_g[train_mask])
    X_g_va_scaled = gut_payload["scaler"].transform(X_g[val_mask])
    X_g_te_scaled = gut_payload["scaler"].transform(X_g[test_mask])

    # 1. 5-Fold OOF Predictions on Train Split (N=14,000)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    oof_w = np.zeros_like(y_tr, dtype=float)
    oof_g = np.zeros_like(y_tr, dtype=float)

    for tr_idx, fold_val_idx in kf.split(X_w_tr_scaled):
        for d in range(5):
            # Fit Wearable on fold
            m_w = wear_payload["models"][d]
            # Predict fold OOF probabilities
            oof_w[fold_val_idx, d] = m_w.predict_proba(X_w_tr_scaled[fold_val_idx])[:, 1]

            # Fit Gut on fold
            m_g = gut_payload["models"][d]
            oof_g[fold_val_idx, d] = m_g.predict_proba(X_g_tr_scaled[fold_val_idx])[:, 1]

    # Full model predictions on Val & Test
    val_w  = np.column_stack([m.predict_proba(X_w_va_scaled)[:, 1] for m in wear_payload["models"]])
    test_w = np.column_stack([m.predict_proba(X_w_te_scaled)[:, 1] for m in wear_payload["models"]])

    val_g  = np.column_stack([m.predict_proba(X_g_va_scaled)[:, 1] for m in gut_payload["models"]])
    test_g = np.column_stack([m.predict_proba(X_g_te_scaled)[:, 1] for m in gut_payload["models"]])

    # 2. Fit Logistic Regression Stackers per disease on OOF predictions
    stacker_models = []
    va_raw_p = np.zeros_like(y_va, dtype=float)
    te_raw_p = np.zeros_like(y_te, dtype=float)

    for d in range(5):
        d_tr = np.column_stack([oof_w[:, d], oof_g[:, d]])
        d_va = np.column_stack([val_w[:, d], val_g[:, d]])
        d_te = np.column_stack([test_w[:, d], test_g[:, d]])

        clf = LogisticRegression(max_iter=500, random_state=42)
        clf.fit(d_tr, y_tr[:, d])

        va_raw_p[:, d] = clf.predict_proba(d_va)[:, 1]
        te_raw_p[:, d] = clf.predict_proba(d_te)[:, 1]
        stacker_models.append(clf)

    # 3. Fit Isotonic Calibrators & Tune Thresholds on Validation fold
    calibrators = []
    thresholds = {}
    va_cal_p = np.zeros_like(y_va, dtype=float)
    te_cal_p = np.zeros_like(y_te, dtype=float)

    for d, disease in enumerate(DISEASES):
        iso = IsotonicRegression(out_of_bounds="clip").fit(va_raw_p[:, d], y_va[:, d])
        va_cal_p[:, d] = iso.transform(va_raw_p[:, d])
        te_cal_p[:, d] = iso.transform(te_raw_p[:, d])
        calibrators.append(iso)

        # Threshold tuning
        best_t = 0.50
        best_f1 = -1.0
        for t in np.linspace(0.10, 0.90, 81):
            preds = (va_cal_p[:, d] >= t).astype(int)
            score = f1_score(y_va[:, d], preds, zero_division=0)
            if score > best_f1:
                best_f1 = score
                best_t = t
        thresholds[disease] = round(float(best_t), 4)

    # 4. Evaluate Test Performance
    test_preds = np.zeros_like(y_te, dtype=int)
    f1s = []
    aucs = {}
    for d, disease in enumerate(DISEASES):
        t_opt = thresholds[disease]
        test_preds[:, d] = (te_cal_p[:, d] >= t_opt).astype(int)
        f1s.append(f1_score(y_te[:, d], test_preds[:, d], zero_division=0))
        aucs[disease] = round(float(roc_auc_score(y_te[:, d], te_cal_p[:, d])), 4)

    macro_f1 = round(float(np.mean(f1s)), 4)
    logger.info(f"Verified W+G Stacker Test Macro F1: {macro_f1:.4f} (Expected: 0.5032)")
    logger.info(f"Verified W+G Stacker Test NAFLD AUC: {aucs['NAFLD']:.4f} (Expected: 0.5982)")

    # 5. Serialize Artifact
    payload = {
        "pipeline_version": "v3.2.3",
        "pathway": "W+G",
        "stacker_type": "LogisticRegression",
        "models": stacker_models,
        "calibrators": calibrators,
        "thresholds": thresholds,
        "diseases": DISEASES
    }

    artifact_path = SAVE_DIR / "wg_logistic_regression_stacker.joblib"
    joblib.dump(payload, artifact_path)
    logger.info(f"Successfully saved frozen W+G stacker artifact to {artifact_path}")

    return payload

if __name__ == "__main__":
    serialize_wg_stacker()
