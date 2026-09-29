"""
sprint_25_1_freeze_audit.py — Publication Experiment Freeze & Reproducibility Setup Audit.
Performs SHA-256 hash recording, split size verification, leakage audit, and experiment registry setup for Sprint 25.1.
"""

import sys
import os
import json
import hashlib
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from multimodal_data_intake_engine.config import (
    CLINICAL_FEATURES, WEARABLE_FEATURES, GUT_TAXA_40, GUT_INDICES_9, GUT_FEATURES
)
from expert_models.v3_inference_engine import V3InferenceEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("sprint_25_1_audit")

def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def run_sprint_25_1_audit():
    print("=" * 80)
    print("      SPRINT 25.1 — PUBLICATION EXPERIMENT FREEZE & REPRODUCIBILITY SETUP      ")
    print("=" * 80)

    evidence = {}

    # --------------------------------------------------------------------------
    # 1. Dataset & Model Artifact Hashes
    # --------------------------------------------------------------------------
    print("\n[STEP 1] Verifying & Recording Hashes for Frozen V4 Datasets & Model Artifacts...")
    data_dir = REPO_ROOT / "data" / "multimodal_v4"
    expert_artifacts_dir = REPO_ROOT / "expert_models" / "v4_artifacts"
    fusion_artifacts_dir = REPO_ROOT / "fusion_engine" / "v4_artifacts"

    dataset_files = [
        "clinical_v4.csv",
        "wearable_v4.csv",
        "gut_v4.csv",
        "labels_v4.csv",
        "patient_metadata_v4.csv",
        "train_ids_v4.csv",
        "val_ids_v4.csv",
        "test_ids_v4.csv"
    ]

    dataset_hashes = {}
    for fname in dataset_files:
        fpath = data_dir / fname
        assert fpath.exists(), f"Missing dataset file: {fname}"
        h = compute_sha256(fpath)
        dataset_hashes[fname] = h
        print(f"  - Data File [{fname:25s}]: {h[:16]}... ({fpath.stat().st_size / 1e6:.2f} MB)")

    model_files = [
        (expert_artifacts_dir / "clinical_v4_expert_payload.joblib"),
        (expert_artifacts_dir / "wearable_v4_expert_payload.joblib"),
        (expert_artifacts_dir / "gut_v4_expert_payload.joblib"),
        (fusion_artifacts_dir / "v4_multimodal_fusion_payload.joblib")
    ]

    model_hashes = {}
    for mpath in model_files:
        assert mpath.exists(), f"Missing model artifact: {mpath.name}"
        h = compute_sha256(mpath)
        model_hashes[mpath.name] = h
        print(f"  - Model File [{mpath.name:35s}]: {h[:16]}... ({mpath.stat().st_size / 1e6:.2f} MB)")

    evidence["dataset_hashes"] = dataset_hashes
    evidence["model_hashes"] = model_hashes

    # --------------------------------------------------------------------------
    # 2. Split Sizes & Cohort Isolation Audit
    # --------------------------------------------------------------------------
    print("\n[STEP 2] Auditing Train/Validation/Test Split Sizes & Patient Isolation...")
    train_ids = set(pd.read_csv(data_dir / "train_ids_v4.csv")["Patient_ID"].tolist())
    val_ids   = set(pd.read_csv(data_dir / "val_ids_v4.csv")["Patient_ID"].tolist())
    test_ids  = set(pd.read_csv(data_dir / "test_ids_v4.csv")["Patient_ID"].tolist())

    total_unique_patients = len(train_ids | val_ids | test_ids)
    print(f"  - Train Cohort Count      : {len(train_ids)} patients (Expected: 70,000)")
    print(f"  - Validation Cohort Count : {len(val_ids)} patients (Expected: 15,000)")
    print(f"  - Test Cohort Count       : {len(test_ids)} patients (Expected: 15,000)")
    print(f"  - Total Unique Cohort Size: {total_unique_patients} patients (Expected: 100,000)")

    assert len(train_ids) == 70000, f"Expected 70,000 train IDs, got {len(train_ids)}"
    assert len(val_ids)   == 15000, f"Expected 15,000 val IDs, got {len(val_ids)}"
    assert len(test_ids)  == 15000, f"Expected 15,000 test IDs, got {len(test_ids)}"
    assert total_unique_patients == 100000, f"Expected 100,000 total patients, got {total_unique_patients}"

    # Check for split overlaps
    train_val_overlap = train_ids.intersection(val_ids)
    train_test_overlap = train_ids.intersection(test_ids)
    val_test_overlap = val_ids.intersection(test_ids)

    assert len(train_val_overlap) == 0, f"Leakage detected: {len(train_val_overlap)} patients overlap between Train & Val!"
    assert len(train_test_overlap) == 0, f"Leakage detected: {len(train_test_overlap)} patients overlap between Train & Test!"
    assert len(val_test_overlap) == 0, f"Leakage detected: {len(val_test_overlap)} patients overlap between Val & Test!"

    print("  [OK] PASS: 100,000 patient cohort split perfectly into 70k Train / 15k Val / 15k Test with 0 patient overlap.")
    evidence["split_sizes"] = {
        "train": len(train_ids),
        "val": len(val_ids),
        "test": len(test_ids),
        "total": total_unique_patients,
        "patient_overlap_count": 0
    }

    # --------------------------------------------------------------------------
    # 3. Model Feature Vector & Data Leakage Audit
    # --------------------------------------------------------------------------
    print("\n[STEP 3] Auditing Model Feature Vector Schemas & Anti-Leakage Rules...")
    engine = V3InferenceEngine()

    c_feats = engine.clinical_payload["features"]
    w_feats = engine.wearable_payload["features"]
    g_feats = engine.gut_payload["features"]

    print(f"  - Clinical Feature Count : {len(c_feats)} (Includes Age and Gender, Excludes Patient_ID)")
    print(f"  - Wearable Feature Count : {len(w_feats)} (Excludes Patient_ID, Age, Gender)")
    print(f"  - Gut Feature Count      : {len(g_feats)} (40 taxa + Other_Taxa + 9 indices, Excludes Patient_ID, Age, Gender)")

    assert len(c_feats) == 18 and "Age" in c_feats and "Gender" in c_feats and "Patient_ID" not in c_feats
    assert len(w_feats) == 15 and "Age" not in w_feats and "Gender" not in w_feats and "Patient_ID" not in w_feats
    assert len(g_feats) == 49 and "Age" not in g_feats and "Gender" not in g_feats and "Patient_ID" not in g_feats

    targets = ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]
    for t in targets:
        assert t not in c_feats and t not in w_feats and t not in g_feats, f"Disease target label {t} leaked into feature space!"

    print("  [OK] PASS: Zero data leakage detected. Patient_ID and disease labels are 100% metadata/targets only.")
    evidence["data_leakage_audit"] = {
        "patient_id_isolated": True,
        "disease_labels_isolated": True,
        "age_gender_clinical_only": True
    }

    # --------------------------------------------------------------------------
    # 4. Publication Experiment Registry Setup
    # --------------------------------------------------------------------------
    print("\n[STEP 4] Setting Up Publication Experiment Registry Configuration...")
    pub_dir = REPO_ROOT / "expert_models" / "reports" / "publication_v4"
    pub_dir.mkdir(parents=True, exist_ok=True)

    config_json_path = pub_dir / "publication_v4_config.json"
    registry_config = {
        "dataset_version": "V4",
        "model_version": "V4",
        "cohort": {
            "total_patients": 100000,
            "train_size": 70000,
            "val_size": 15000,
            "test_size": 15000
        },
        "random_seeds": {
            "dataset_generation": 42,
            "model_training": 42,
            "bootstrap_ci": 42
        },
        "target_diseases": targets,
        "individual_experts": ["Clinical", "Wearable", "Gut"],
        "multimodal_pathways": ["C", "W", "G", "C+W", "C+G", "W+G", "C+W+G"],
        "evaluation_metrics": [
            "ROC-AUC", "PR-AUC", "Accuracy", "Precision", "Recall",
            "F1-score", "Sensitivity", "Specificity", "Brier_Score",
            "Confusion_Matrix", "Calibration_Curve"
        ],
        "confidence_interval_method": "Bootstrap 1000 resamples (95% percentile CI)",
        "statistical_testing_method": "DeLong test for ROC-AUC & Paired Bootstrap Test for PR-AUC",
        "dataset_hashes": dataset_hashes,
        "model_hashes": model_hashes
    }

    with open(config_json_path, "w") as f:
        json.dump(registry_config, f, indent=2)

    print(f"  [OK] Saved publication experiment registry configuration to '{config_json_path.relative_to(REPO_ROOT)}'.")

    # Save summary audit JSON
    audit_summary_path = REPO_ROOT / "web_platform" / "reports" / "sprint_25_1_freeze_audit.json"
    with open(audit_summary_path, "w") as f:
        json.dump(evidence, f, indent=2)

    print("\n" + "=" * 80)
    print("   ALL SPRINT 25.1 FREEZE & REPRODUCIBILITY AUDITS PASSED 100%!   ")
    print("=" * 80)

if __name__ == "__main__":
    run_sprint_25_1_audit()
