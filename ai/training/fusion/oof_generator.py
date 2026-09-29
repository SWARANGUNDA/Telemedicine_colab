"""
oof_generator.py — Leak-Free Out-of-Fold Expert Probability Generator.

For each modality (Clinical, Wearable, Gut), performs 5-Fold Stratified CV
on the 14,000-patient Training split to generate out-of-fold probability
predictions. These OOF probabilities are used as meta-learner training
features, preventing stacking leakage.

Also generates direct expert probability predictions for Validation and
Test sets using the frozen Phase 3 expert models (no leakage concern for
val/test since those samples were never in the expert training set).
"""

import logging
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from ai.config import expert_config as expert_config
from ai.training.clinical import data_loader as expert_data_loader
from ai.training.clinical.preprocessing import ExpertPreprocessor
from ai.training.clinical.trainer import SingleDiseaseEstimator
from ai.training.clinical.artifact_manager import ExpertArtifactManager
from ai.config import fusion_config as config

logger = logging.getLogger("fusion_engine.oof_generator")


def _get_composite_strat_key(y: pd.DataFrame) -> np.ndarray:
    """Create composite stratification key from multi-label targets."""
    raw_keys = y.astype(str).apply("_".join, axis=1)
    counts = raw_keys.value_counts()
    most_common = counts.index[0]
    return raw_keys.map(lambda k: k if counts[k] >= 2 else most_common).values


def generate_oof_probabilities_for_modality(
    modality_key: str,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate OOF train, direct val, and direct test probability matrices
    for a single modality.

    Args:
        modality_key: One of 'clinical', 'wearable', 'gut'.

    Returns:
        Tuple of (oof_train_probs, val_probs, test_probs),
        each of shape (n_samples, 5).
    """
    mod_info = config.MODALITY_EXPERT_MAP[modality_key]
    dataset_path = Path(mod_info["dataset_path"])
    schema_file = mod_info["schema_file"]
    expert_name = mod_info["expert_name"]
    expert_version = mod_info["version"]

    # Load dataset and split
    X, y, splits, approved = expert_data_loader.load_dataset_for_expert(
        dataset_path=dataset_path,
        schema_filename=schema_file,
    )

    train_mask = splits == "train"
    val_mask = splits == "val"
    test_mask = splits == "test"

    X_train, y_train = X[train_mask].reset_index(drop=True), y[train_mask].reset_index(drop=True)
    X_val = X[val_mask]
    X_test = X[test_mask]

    # --- OOF Probability Generation on Train (5-fold CV) ---
    n_train = len(X_train)
    oof_probs = np.zeros((n_train, len(config.TARGET_DISEASES)))

    # Determine model type from frozen expert metadata
    mgr = ExpertArtifactManager(expert_name, expert_version)
    artifacts = mgr.load_artifacts()
    model_type = artifacts.get("model", None)
    # Detect architecture from training config
    training_cfg_path = mgr.artifact_dir / "training_config.json"
    import json
    with open(training_cfg_path, "r") as f:
        tcfg = json.load(f)
    architecture = tcfg.get("best_architecture", "xgboost")

    strat_key = _get_composite_strat_key(y_train)
    skf = StratifiedKFold(
        n_splits=config.OOF_N_FOLDS,
        shuffle=True,
        random_state=config.RANDOM_SEED,
    )

    logger.info(
        "Generating %d-fold OOF probabilities for %s (%s architecture)",
        config.OOF_N_FOLDS, modality_key.upper(), architecture.upper(),
    )

    for fold_idx, (fit_indices, oof_indices) in enumerate(skf.split(X_train, strat_key)):
        X_fit = X_train.iloc[fit_indices]
        y_fit = y_train.iloc[fit_indices].values
        X_oof = X_train.iloc[oof_indices]

        # Fit preprocessor on this fold's training data
        prep = ExpertPreprocessor(feature_order=approved, preserve_nans=True, scale_numeric=False)
        X_fit_prep = prep.fit_transform(X_fit)
        X_oof_prep = prep.transform(X_oof)

        # Fit model on this fold
        estimator = SingleDiseaseEstimator(model_type=architecture)
        estimator.fit(X_fit_prep, y_fit)

        # Predict OOF probabilities
        fold_probs = estimator.predict_proba(X_oof_prep)
        oof_probs[oof_indices] = fold_probs

        logger.info(
            "  Fold %d/%d complete: %d fit, %d OOF",
            fold_idx + 1, config.OOF_N_FOLDS, len(fit_indices), len(oof_indices),
        )

    # --- Direct Probabilities for Val and Test (using frozen expert) ---
    frozen_model = artifacts["model"]
    frozen_preprocessor = artifacts["preprocessor"]
    frozen_calibrator = artifacts["calibrator"]

    X_val_prep = frozen_preprocessor.transform(X_val[approved])
    X_test_prep = frozen_preprocessor.transform(X_test[approved])

    val_raw = frozen_model.predict_proba(X_val_prep)
    test_raw = frozen_model.predict_proba(X_test_prep)

    # Apply frozen calibration
    val_probs = frozen_calibrator.calibrate_probas(val_raw)
    test_probs = frozen_calibrator.calibrate_probas(test_raw)

    logger.info(
        "OOF generation complete for %s: Train OOF shape=%s, Val=%s, Test=%s",
        modality_key.upper(), oof_probs.shape, val_probs.shape, test_probs.shape,
    )

    return oof_probs, val_probs, test_probs


def generate_all_oof_probabilities() -> Dict[str, Dict[str, np.ndarray]]:
    """Generate OOF train, val, and test probability matrices for all 3 modalities.

    Returns:
        Dict mapping modality_key -> {"train": array, "val": array, "test": array}.
    """
    all_probs = {}

    for modality_key in config.MODALITY_KEYS:
        train_p, val_p, test_p = generate_oof_probabilities_for_modality(modality_key)
        all_probs[modality_key] = {
            "train": train_p,
            "val": val_p,
            "test": test_p,
        }

        # Save to disk for reproducibility
        for split_name, arr in [("train", train_p), ("val", val_p), ("test", test_p)]:
            out_path = config.OOF_DIR / f"{modality_key}_{split_name}_probs.npy"
            np.save(out_path, arr)
            logger.info("Saved %s %s probs to %s", modality_key, split_name, out_path)

    return all_probs


def load_all_oof_probabilities() -> Dict[str, Dict[str, np.ndarray]]:
    """Load previously generated OOF probability matrices from disk."""
    all_probs = {}
    for modality_key in config.MODALITY_KEYS:
        all_probs[modality_key] = {}
        for split_name in ["train", "val", "test"]:
            path = config.OOF_DIR / f"{modality_key}_{split_name}_probs.npy"
            all_probs[modality_key][split_name] = np.load(path)
    return all_probs
