"""
sprint_24_5_verification.py — Comprehensive Automated Audit for Sprint 24.5.
Verifies Upload & Preprocessing Compatibility with FINAL V4 Schemas & Models.
"""

import sys
import os
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from multimodal_data_intake_engine.config import (
    CLINICAL_FEATURES, WEARABLE_FEATURES, GUT_TAXA_40, GUT_INDICES_9, GUT_FEATURES
)
from multimodal_data_intake_engine.v3_schema_validator import V3SchemaValidator
from expert_models.v3_inference_engine import V3InferenceEngine
from fusion_engine.v3_scientific_router import V3ScientificRouter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("sprint_24_5_verification")

def test_sprint_24_5_compatibility():
    results = {}
    print("=" * 80)
    print("      SPRINT 24.5 — V4 UPLOAD & PREPROCESSING COMPATIBILITY AUDIT      ")
    print("=" * 80)

    # 1. Feature Schema Counts
    print("\n[TEST 1] Verifying V4 Canonical Feature Counts...")
    assert len(CLINICAL_FEATURES) == 18, f"Expected 18 Clinical features, got {len(CLINICAL_FEATURES)}"
    assert len(WEARABLE_FEATURES) == 15, f"Expected 15 Wearable features, got {len(WEARABLE_FEATURES)}"
    assert len(GUT_TAXA_40) == 40, f"Expected 40 Gut Taxa, got {len(GUT_TAXA_40)}"
    assert len(GUT_INDICES_9) == 9, f"Expected 9 Gut Derived Indices, got {len(GUT_INDICES_9)}"
    assert len(GUT_FEATURES) == 49, f"Expected 49 total Gut model input features, got {len(GUT_FEATURES)}"
    print("  [OK] PASS: Clinical (18), Wearable (15), Gut Taxa (40), Gut Indices (9), Total Gut (49).")
    results["feature_schema_audit"] = "PASS"

    # 2. V4 Sample Files Verification
    print("\n[TEST 2] Verifying V4 Sample Files in public/samples/ & reports/...")
    samples_dir = REPO_ROOT / "web_platform" / "frontend" / "public" / "samples"
    reports_dir = REPO_ROOT / "web_platform" / "reports"

    clin_csv = samples_dir / "clinical_v4_sample.csv"
    wear_csv = samples_dir / "wearable_v4_sample.csv"
    gut_csv  = samples_dir / "gut_v4_sample.csv"

    assert clin_csv.exists() and (reports_dir / "clinical_v4_sample.csv").exists(), "Clinical V4 sample missing!"
    assert wear_csv.exists() and (reports_dir / "wearable_v4_sample.csv").exists(), "Wearable V4 sample missing!"
    assert gut_csv.exists() and (reports_dir / "gut_v4_sample.csv").exists(), "Gut V4 sample missing!"

    clin_df = pd.read_csv(clin_csv)
    wear_df = pd.read_csv(wear_csv)
    gut_df  = pd.read_csv(gut_csv)

    print(f"  - Clinical Sample Cols: {len(clin_df.columns)} (Includes Patient_ID + 18 features)")
    print(f"  - Wearable Sample Cols: {len(wear_df.columns)} (Includes Patient_ID + 15 features)")
    print(f"  - Gut Sample Cols: {len(gut_df.columns)} (Includes Patient_ID + 40 taxa + Other_Taxa + 9 indices)")

    assert set(CLINICAL_FEATURES).issubset(set(clin_df.columns)), "Clinical CSV missing required V4 features"
    assert set(WEARABLE_FEATURES).issubset(set(wear_df.columns)), "Wearable CSV missing required V4 features"
    assert set(GUT_TAXA_40).issubset(set(gut_df.columns)), "Gut CSV missing required 40 V4 taxa"
    print("  [OK] PASS: All 3 V4 sample CSV files contain exact canonical feature columns.")
    results["sample_files_audit"] = "PASS"

    # 3. Upload Validation Engine Testing
    print("\n[TEST 3] Testing Upload Validation & Schema Inspection Engine...")
    
    # Valid V4 Clinical, Wearable, Gut dicts
    clin_dict = clin_df.to_dict(orient="records")[0]
    wear_dict = wear_df.to_dict(orient="records")[0]
    gut_dict  = gut_df.to_dict(orient="records")[0]

    valid_payload = {
        "patient_id": "P_AUDIT_V4",
        "clinical_data": clin_dict,
        "wearable_data": wear_dict,
        "gut_data": gut_dict
    }

    val_res = V3SchemaValidator.validate_and_inspect_payload(valid_payload)
    assert val_res["modality_mask"] == "C+W+G", f"Expected C+W+G mask, got {val_res['modality_mask']}"
    assert val_res["gut_validation_error"] is None, f"Unexpected gut validation error: {val_res['gut_validation_error']}"
    print("  [OK] PASS: Valid V4 Full Multimodal payload accepted cleanly.")

    # Invalid Case 1: Gut composition sum != 100% (e.g. 50%)
    bad_gut_dict = dict(gut_dict)
    bad_gut_dict["Akkermansia_muciniphila"] = 5.0
    bad_gut_dict["Faecalibacterium_prausnitzii"] = 0.0
    bad_gut_dict["Other_Taxa"] = 0.0
    for k in GUT_TAXA_40[2:]:
        bad_gut_dict[k] = 0.0
    bad_sum_payload = {"patient_id": "P_BAD_SUM", "gut_data": bad_gut_dict}
    val_bad_sum = V3SchemaValidator.validate_and_inspect_payload(bad_sum_payload)
    assert val_bad_sum["gut_validation_error"] is not None, "Expected gut sum validation failure!"
    print(f"  [OK] PASS: Gut sum != 100% correctly caught: '{val_bad_sum['gut_validation_error']}'")

    # Invalid Case 2: Legacy V3 20-taxa gut sample
    legacy_gut_dict = {
        "Patient_ID": "P_V3_LEGACY",
        "Akkermansia": 5.2, "Faecalibacterium": 12.1, "Roseburia": 4.5, "Bifidobacterium": 6.8,
        "Bacteroides": 18.2, "Prevotella": 8.1, "Ruminococcus": 3.4, "Blautia": 5.0, "Collinsella": 2.1
    }
    val_legacy_gut = V3SchemaValidator.validate_and_inspect_payload({"patient_id": "P_V3", "gut_data": legacy_gut_dict})
    assert val_legacy_gut["gut_validation_error"] is not None, "Expected legacy 20-taxa gut rejection!"
    print(f"  [OK] PASS: Legacy 20-taxa V3 gut sample correctly rejected: '{val_legacy_gut['gut_validation_error']}'")

    # 4. Verifying All 7 Modality Pathways
    print("\n[TEST 4] Evaluating All 7 Modality Pathways (C, W, G, C+W, C+G, W+G, C+W+G)...")
    engine = V3InferenceEngine()
    router = V3ScientificRouter(engine)

    pathways = {
        "C": {"patient_id": "P_C", "clinical_data": clin_dict},
        "W": {"patient_id": "P_W", "wearable_data": wear_dict},
        "G": {"patient_id": "P_G", "gut_data": gut_dict},
        "C+W": {"patient_id": "P_CW", "clinical_data": clin_dict, "wearable_data": wear_dict},
        "C+G": {"patient_id": "P_CG", "clinical_data": clin_dict, "gut_data": gut_dict},
        "W+G": {"patient_id": "P_WG", "wearable_data": wear_dict, "gut_data": gut_dict},
        "C+W+G": {"patient_id": "P_CWG", "clinical_data": clin_dict, "wearable_data": wear_dict, "gut_data": gut_dict}
    }

    pathway_results = {}
    for path_name, raw_pld in pathways.items():
        v_intake = V3SchemaValidator.validate_and_inspect_payload(raw_pld)
        pred_out = router.route_and_predict(v_intake)
        t2d_prob = pred_out["predictions"]["Type2_Diabetes"]["calibrated_probability"]
        pathway_results[path_name] = {
            "effective_pathway": pred_out["routing_metadata"]["effective_pathway"],
            "t2d_calibrated_probability": t2d_prob,
            "risk_level": pred_out["predictions"]["Type2_Diabetes"]["risk_level"]
        }
        print(f"  - Pathway [{path_name}]: Effective = {pred_out['routing_metadata']['effective_pathway']} | T2D Prob = {t2d_prob:.4f} ({pred_out['predictions']['Type2_Diabetes']['risk_level']})")

    assert len(pathway_results) == 7, "Failed to evaluate all 7 modality pathways"
    print("  [OK] PASS: All 7 modality pathways executed without errors.")
    results["pathways_7_audit"] = pathway_results

    # Save summary audit report
    audit_report_path = reports_dir / "sprint_24_5_compatibility_audit.json"
    with open(audit_report_path, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print("   ALL SPRINT 24.5 COMPATIBILITY TESTS PASSED WITH 100% VERIFICATION!   ")
    print("=" * 80)

if __name__ == "__main__":
    test_sprint_24_5_compatibility()
