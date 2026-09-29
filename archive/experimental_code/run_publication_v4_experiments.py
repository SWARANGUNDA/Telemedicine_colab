"""
run_publication_v4_experiments.py — Reproducible Publication Experiment Runner for TeleMed V4.
Evaluates all 3 individual experts and 7 multimodal pathways across all 5 disease targets
using frozen V4 artifacts without modifying any dataset or model files.
"""

import sys
import os
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, auc, accuracy_score,
    precision_score, recall_score, f1_score, confusion_matrix, brier_score_loss
)

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from expert_models.v3_inference_engine import V3InferenceEngine
from fusion_engine.v3_scientific_router import V3ScientificRouter
from multimodal_data_intake_engine.v3_schema_validator import V3SchemaValidator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("publication_v4_runner")

DISEASES = ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]
PATHWAYS = ["C", "W", "G", "C+W", "C+G", "W+G", "C+W+G"]

def compute_detailed_metrics(y_true, y_prob, threshold=0.5):
    """Compute complete metric suite for a single disease binary target."""
    y_pred = (y_prob >= threshold).astype(int)
    roc_auc = float(roc_auc_score(y_true, y_prob))
    
    prec_arr, rec_arr, _ = precision_recall_curve(y_true, y_prob)
    pr_auc = float(auc(rec_arr, prec_arr))
    
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    sensitivity = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    brier = float(brier_score_loss(y_true, y_prob))
    
    return {
        "ROC_AUC": round(roc_auc, 4),
        "PR_AUC": round(pr_auc, 4),
        "Accuracy": round(acc, 4),
        "Precision": round(prec, 4),
        "Recall": round(rec, 4),
        "F1_Score": round(f1, 4),
        "Sensitivity": round(sensitivity, 4),
        "Specificity": round(specificity, 4),
        "Brier_Score": round(brier, 4),
        "TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)
    }

def run_publication_evaluation(split="validation", n_samples=1000):
    logger.info(f"Starting Publication V4 Evaluation Framework on split '{split}' (samples={n_samples})...")
    
    data_dir = REPO_ROOT / "data" / "multimodal_v4"
    reports_dir = REPO_ROOT / "expert_models" / "reports" / "publication_v4"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Load Split IDs
    if split == "validation":
        split_ids = pd.read_csv(data_dir / "val_ids_v4.csv")["Patient_ID"].tolist()[:n_samples]
    elif split == "test":
        split_ids = pd.read_csv(data_dir / "test_ids_v4.csv")["Patient_ID"].tolist()[:n_samples]
    else:
        split_ids = pd.read_csv(data_dir / "train_ids_v4.csv")["Patient_ID"].tolist()[:n_samples]

    split_set = set(split_ids)

    # Load Dataframes filtered by split
    clin_df = pd.read_csv(data_dir / "clinical_v4.csv")
    clin_df = clin_df[clin_df["Patient_ID"].isin(split_set)].set_index("Patient_ID")

    wear_df = pd.read_csv(data_dir / "wearable_v4.csv")
    wear_df = wear_df[wear_df["Patient_ID"].isin(split_set)].set_index("Patient_ID")

    gut_df = pd.read_csv(data_dir / "gut_v4.csv")
    gut_df = gut_df[gut_df["Patient_ID"].isin(split_set)].set_index("Patient_ID")

    labels_df = pd.read_csv(data_dir / "labels_v4.csv")
    labels_df = labels_df[labels_df["Patient_ID"].isin(split_set)].set_index("Patient_ID")

    engine = V3InferenceEngine()
    router = V3ScientificRouter(engine)

    results_matrix = {}

    for pathway in PATHWAYS:
        logger.info(f"Evaluating Pathway [{pathway}] across all 5 disease targets...")
        y_true_dict = {d: [] for d in DISEASES}
        y_prob_dict = {d: [] for d in DISEASES}

        for pid in split_ids:
            if pid not in labels_df.index:
                continue
            
            raw_payload = {"patient_id": pid}
            if "C" in pathway:
                raw_payload["clinical_data"] = clin_df.loc[pid].to_dict()
            if "W" in pathway:
                raw_payload["wearable_data"] = wear_df.loc[pid].to_dict()
            if "G" in pathway:
                raw_payload["gut_data"] = gut_df.loc[pid].to_dict()

            v_intake = V3SchemaValidator.validate_and_inspect_payload(raw_payload)
            pred_out = router.route_and_predict(v_intake)

            for d in DISEASES:
                y_true_dict[d].append(labels_df.loc[pid, d])
                y_prob_dict[d].append(pred_out["predictions"][d]["calibrated_probability"])

        pathway_metrics = {}
        for d in DISEASES:
            m = compute_detailed_metrics(np.array(y_true_dict[d]), np.array(y_prob_dict[d]))
            pathway_metrics[d] = m

        results_matrix[pathway] = pathway_metrics

    # Output report
    output_report = reports_dir / f"publication_v4_{split}_metrics_summary.json"
    with open(output_report, "w") as f:
        json.dump(results_matrix, f, indent=2)

    logger.info(f"Evaluation finished cleanly. Summary saved to '{output_report}'.")
    return results_matrix

if __name__ == "__main__":
    run_publication_evaluation(split="validation", n_samples=100)
