"""
generator.py — Pipeline orchestrator module for Wearable Dataset Generation.

Coordinates loading Clinical_Dataset.csv, preserving patient identity (Patient_ID, Age,
Gender, Disease Labels), generating stochastic wearable metrics conditioned on clinical
biomarkers, executing single-patient validation & auto-regeneration loops, and building
the final aligned DataFrame.
"""

import logging
import time
from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd

from . import config, constants, demographics, activity, heart, sleep, glucose, correlations, noise, validation

logger = logging.getLogger(__name__)


def generate_wearable_dataset(
    config_obj: config.WearableDatasetConfig,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Execute the complete synthetic wearable dataset generation pipeline.

    Args:
        config_obj: Configuration object specifying paths, seed, and options.

    Returns:
        Tuple of (generated_wearable_df, master_clinical_df).
    """
    start_time = time.time()
    rng = np.random.default_rng(config_obj.seed)

    logger.info(f"Starting Wearable Dataset Generation (seed={config_obj.seed})...")

    # Step 1: Load Clinical Master Dataset
    clinical_df = demographics.load_clinical_master_dataset(
        file_path=config_obj.clinical_dataset_path,
        demo_mode=config_obj.demo_mode,
        demo_size=config_obj.demo_size,
    )
    n = len(clinical_df)

    # Step 2: Extract Patient Identity & Clinical Conditioning Context
    logger.info("Extracting clinical conditioning context...")
    context = demographics.extract_patient_context(clinical_df)

    # Step 3: Generate Wearable Feature Domains
    logger.info("Generating physical activity metrics...")
    act_feats = activity.generate_activity_features(context, rng, config_obj)

    logger.info("Generating cardiovascular metrics...")
    heart_feats = heart.generate_heart_features(context, act_feats, rng, config_obj)

    logger.info("Generating sleep metrics...")
    sleep_feats = sleep.generate_sleep_features(context, rng, config_obj)

    logger.info("Generating continuous glucose monitoring (CGM) metrics...")
    glucose_feats = glucose.generate_glucose_features(context, rng, config_obj)

    # Combine generated wearable features
    wearables: Dict[str, np.ndarray] = {}
    wearables.update(act_feats)
    wearables.update(heart_feats)
    wearables.update(sleep_feats)
    wearables.update(glucose_feats)

    # Step 4: Apply Cross-Domain Physiological Correlations
    logger.info("Applying cross-domain physiological correlation adjustments...")
    wearables = correlations.apply_physiological_correlations(wearables)

    # Step 5: Inject Gaussian Noise & Outliers
    if config_obj.enable_noise:
        logger.info("Injecting Gaussian measurement noise...")
        wearables = noise.inject_gaussian_noise(wearables, rng, config_obj)

    if config_obj.enable_outliers:
        logger.info("Injecting controlled extreme outliers...")
        wearables = noise.inject_outliers(wearables, rng, config_obj)

    if config_obj.enable_missingness:
        logger.info("Injecting Missing-at-Random (MAR) data gaps...")
        wearables = noise.inject_missingness(wearables, rng, config_obj)

    # Step 6: Per-Patient Validation & Single-Patient Regeneration Loop
    logger.info("Running per-patient validation and auto-regeneration loop...")
    invalid_count = 0

    for i in range(n):
        # Extract single patient record dictionary
        patient_rec = {feat: wearables[feat][i] for feat in constants.WEARABLE_GENERATED_FEATURES}
        is_valid, errors = validation.validate_patient_record(patient_rec)

        attempts = 0
        while not is_valid and attempts < config_obj.max_regeneration_attempts:
            invalid_count += 1
            attempts += 1
            
            # Slice single-patient context
            single_ctx = {k: np.array([v[i]]) for k, v in context.items()}

            # Regenerate ONLY wearable metrics for patient i
            single_act = activity.generate_activity_features(single_ctx, rng, config_obj)
            single_hr = heart.generate_heart_features(single_ctx, single_act, rng, config_obj)
            single_slp = sleep.generate_sleep_features(single_ctx, rng, config_obj)
            single_glc = glucose.generate_glucose_features(single_ctx, rng, config_obj)

            single_w: Dict[str, np.ndarray] = {}
            single_w.update(single_act)
            single_w.update(single_hr)
            single_w.update(single_slp)
            single_w.update(single_glc)
            single_w = correlations.apply_physiological_correlations(single_w)

            # Update patient i in main arrays
            for feat in constants.WEARABLE_GENERATED_FEATURES:
                wearables[feat][i] = single_w[feat][0]

            patient_rec = {feat: wearables[feat][i] for feat in constants.WEARABLE_GENERATED_FEATURES}
            is_valid, errors = validation.validate_patient_record(patient_rec)

    if invalid_count > 0:
        logger.info(f"Auto-regeneration loop resolved {invalid_count} patient-level violations.")

    # Step 7: Assemble Final DataFrame Preserving Clinical Identity
    logger.info("Assembling final multimodal wearable DataFrame...")
    data_dict: Dict[str, Any] = {}

    # 1. Preserved Identity
    data_dict["Patient_ID"] = context["Patient_ID"]
    data_dict["Age"] = context["Age"]
    data_dict["Gender"] = context["Gender"]

    # 2. Generated Wearables
    for feat in constants.WEARABLE_GENERATED_FEATURES:
        data_dict[feat] = wearables[feat]

    # 3. Preserved Target Labels
    for label in constants.PRESERVED_DISEASE_LABELS:
        data_dict[label] = context[label]

    wearable_df = pd.DataFrame(data_dict)

    # Reorder columns and enforce types
    wearable_df = wearable_df[constants.OUTPUT_COLUMN_ORDER]
    for col, dtype_str in constants.COLUMN_DTYPES.items():
        if col in wearable_df.columns and not wearable_df[col].isnull().any():
            wearable_df[col] = wearable_df[col].astype(dtype_str)

    elapsed = time.time() - start_time
    logger.info(f"Generation pipeline completed successfully in {elapsed:.2f} seconds.")

    return wearable_df, clinical_df
