"""
train_fusion_engine.py — Phase 4 Multimodal Fusion Training Pipeline.

Executes:
1. Generate leak-free OOF probabilities for all 3 modalities (5-fold CV on Train)
2. Load target labels for Train, Val, Test splits
3. Train & select meta-learners for all 7 pathways on OOF Train + Val
4. Calibrate & tune thresholds on Validation set
5. Evaluate all 7 pathways on untouched Test set
6. Compute modality attributions for tri-modal pathway
7. Freeze and save all artifacts to fusion_engine/saved_models/fusion_v1/
"""

import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np

from . import config
from .oof_generator import generate_all_oof_probabilities, load_all_oof_probabilities
from .fusion_data_loader import build_pathway_features, load_targets_for_split
from .meta_trainer import train_and_select_for_pathway
from .evaluator import evaluate_all_pathways
from .fusion_explainer import compute_modality_attribution

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fusion_engine.train")


def run_fusion_pipeline():
    """Run the complete Phase 4 Multimodal Fusion training and evaluation pipeline."""
    logger.info("=" * 70)
    logger.info("  PHASE 4: MULTIMODAL FUSION ENGINE — TRAINING PIPELINE")
    logger.info("=" * 70)

    # ── Step 1: Generate OOF Probabilities ──
    oof_check = config.OOF_DIR / "clinical_train_probs.npy"
    if oof_check.exists():
        logger.info("Loading existing OOF probabilities from disk...")
        all_probs = load_all_oof_probabilities()
    else:
        logger.info("Generating leak-free OOF probabilities (5-fold CV on Train)...")
        all_probs = generate_all_oof_probabilities()

    # ── Step 2: Load Targets ──
    y_train = load_targets_for_split("train")
    y_val = load_targets_for_split("val")
    y_test = load_targets_for_split("test")

    logger.info("Targets loaded: Train=%d, Val=%d, Test=%d", len(y_train), len(y_val), len(y_test))

    # ── Step 3 & 4: Train Meta-Learners for all 7 Pathways ──
    pathway_models: Dict[str, Any] = {}
    pathway_model_types: Dict[str, str] = {}
    pathway_calibrators: Dict[str, Any] = {}
    pathway_thresholds: Dict[str, Dict[str, float]] = {}
    pathway_comparisons: Dict[str, Any] = {}

    for pathway_key in config.PATHWAY_DEFINITIONS:
        logger.info("─" * 50)
        logger.info("Training pathway: %s", pathway_key)

        X_train_pw = build_pathway_features(all_probs, pathway_key, "train")
        X_val_pw = build_pathway_features(all_probs, pathway_key, "val")

        model, mtype, calibrator, thresholds, comparison = train_and_select_for_pathway(
            pathway_key, X_train_pw, y_train, X_val_pw, y_val,
        )

        pathway_models[pathway_key] = model
        pathway_model_types[pathway_key] = mtype
        pathway_calibrators[pathway_key] = calibrator
        pathway_thresholds[pathway_key] = thresholds
        pathway_comparisons[pathway_key] = comparison

    # ── Step 5: Evaluate on Untouched Test Set ──
    logger.info("=" * 70)
    logger.info("  EVALUATING ALL 7 PATHWAYS ON UNTOUCHED TEST SET")
    logger.info("=" * 70)

    test_results = evaluate_all_pathways(
        all_probs, y_test, pathway_models, pathway_calibrators, pathway_thresholds,
    )

    # ── Step 6: Compute Modality Attribution for C+W+G ──
    tri_model = pathway_models["C+W+G"]
    tri_type = pathway_model_types["C+W+G"]
    modality_attribution = compute_modality_attribution(tri_model, tri_type, "C+W+G")
    logger.info("Tri-modal (C+W+G) Modality Attribution:")
    for disease, weights in modality_attribution.items():
        logger.info("  %s: %s", disease, weights)

    # ── Step 7: Freeze & Save Artifacts ──
    fusion_artifact_dir = config.SAVED_MODELS_DIR / f"fusion_{config.FUSION_VERSION}"
    meta_dir = fusion_artifact_dir / "meta_learners"
    meta_dir.mkdir(parents=True, exist_ok=True)

    # Save models
    for pathway_key, model in pathway_models.items():
        joblib.dump(model, meta_dir / f"{pathway_key}.joblib")

    # Save calibrators
    joblib.dump(pathway_calibrators, fusion_artifact_dir / "calibrators.pkl")

    # Save thresholds
    with open(fusion_artifact_dir / "thresholds.json", "w") as f:
        json.dump(pathway_thresholds, f, indent=2)

    # Save metrics
    # Convert numpy types for JSON serialization
    serializable_results = json.loads(json.dumps(test_results, default=str))
    with open(fusion_artifact_dir / "metrics.json", "w") as f:
        json.dump(serializable_results, f, indent=2)

    # Save training config
    training_config = {
        "fusion_version": config.FUSION_VERSION,
        "oof_n_folds": config.OOF_N_FOLDS,
        "random_seed": config.RANDOM_SEED,
        "pathway_model_types": pathway_model_types,
        "pathway_comparisons": pathway_comparisons,
        "modality_attribution_cwg": modality_attribution,
    }
    with open(fusion_artifact_dir / "training_config.json", "w") as f:
        json.dump(training_config, f, indent=2, default=str)

    # Save metadata
    metadata = {
        "phase": "Phase 4 - Multimodal Fusion Engine",
        "version": config.FUSION_VERSION,
        "saved_timestamp": datetime.datetime.now().isoformat(),
        "target_diseases": config.TARGET_DISEASES,
        "pathways": list(config.PATHWAY_DEFINITIONS.keys()),
        "expert_versions": {k: v["version"] for k, v in config.MODALITY_EXPERT_MAP.items()},
        "status": "FROZEN",
        "disclaimer": "Research prototype trained on synthetic data. Not for clinical use.",
    }
    with open(fusion_artifact_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # Save test results report
    reports_dir = config.REPORTS_DIR
    with open(reports_dir / "fusion_test_results.json", "w") as f:
        json.dump(serializable_results, f, indent=2)

    logger.info("=" * 70)
    logger.info("  PHASE 4 FUSION PIPELINE COMPLETE")
    logger.info("  Artifacts frozen at: %s", fusion_artifact_dir)
    logger.info("=" * 70)

    # Print final summary table
    logger.info("FINAL TEST SET RESULTS SUMMARY:")
    for pw_key in config.PATHWAY_DEFINITIONS:
        s = test_results[pw_key]["summary"]
        logger.info(
            "  %-6s  Macro F1=%.4f  Micro F1=%.4f  Brier=%.4f  Hamming=%.4f",
            pw_key, s["macro_f1"], s["micro_f1"], s["mean_brier_score"], s["hamming_loss"],
        )

    return test_results


if __name__ == "__main__":
    run_fusion_pipeline()
