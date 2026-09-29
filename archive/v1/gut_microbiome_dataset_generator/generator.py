"""
generator.py — Core orchestration pipeline for the Gut Microbiome Dataset.

Coordinates the full generation pipeline:
  1. Load Clinical Dataset and extract alignment/context data.
  2. Compute latent metabolic risk scores.
  3. Compute disease-specific abundance shifts.
  4. Generate beneficial bacteria.
  5. Generate inflammatory bacteria.
  6. Generate context-dependent bacteria.
  7. Apply correlation structure.
  8. Generate Shannon Diversity Index.
  9. Inject biological noise.
  10. Validate every patient (regenerate on failure).
  11. Validate complete dataset.
  12. Export all output files.
"""

import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .config import GutMicrobiomeConfig
from . import constants
from .loader import (
    load_clinical_dataset,
    extract_alignment_data,
    extract_clinical_context,
)
from .disease_profile import (
    compute_metabolic_risk_scores,
    compute_disease_shifts,
)
from .bacteria import (
    generate_beneficial_bacteria,
    generate_inflammatory_bacteria,
    generate_context_dependent_bacteria,
)
from .diversity import generate_shannon_diversity
from .correlations import (
    build_target_correlation_matrix,
    apply_correlation_structure,
)
from .noise import inject_noise
from .validation import (
    validate_patient,
    validate_dataset,
    generate_validation_report,
)
from .exporter import (
    export_dataset,
    export_summary_statistics,
    export_feature_distribution_report,
    export_correlation_matrix,
)
from .utils import create_rng

logger = logging.getLogger("gut_microbiome_generator")


def run_pipeline(config: GutMicrobiomeConfig) -> pd.DataFrame:
    """Execute the complete Gut Microbiome Dataset generation pipeline.

    Args:
        config: Generator configuration.

    Returns:
        The final validated Gut Microbiome Dataset as a DataFrame.
    """
    start_time = time.time()
    output_dir = Path(config.output_dir)

    logger.info("=" * 72)
    logger.info("GUT MICROBIOME DATASET GENERATOR - STARTING PIPELINE")
    logger.info("=" * 72)
    logger.info("Seed: %d", config.seed)

    # ─── Step 1: Load Clinical Dataset ────────────────────────────────────
    logger.info("Step 1: Loading Clinical Dataset...")
    clinical_df = load_clinical_dataset(config.clinical_dataset_path)
    n_patients = len(clinical_df)
    logger.info("Loaded %d patients.", n_patients)

    # ─── Step 2: Extract alignment data ───────────────────────────────────
    logger.info("Step 2: Extracting alignment data...")
    alignment_df = extract_alignment_data(clinical_df)
    clinical_context = extract_clinical_context(clinical_df)
    disease_labels = clinical_df[
        [c for c in constants.DISEASE_LABEL_COLUMNS if c in clinical_df.columns]
    ].copy()

    # ─── Step 3: Initialize RNG ───────────────────────────────────────────
    logger.info("Step 3: Initializing RNG (seed=%d)...", config.seed)
    rng = create_rng(config.seed)

    # ─── Step 4: Compute metabolic risk scores ────────────────────────────
    logger.info("Step 4: Computing metabolic risk scores...")
    risk_scores = compute_metabolic_risk_scores(
        clinical_context, disease_labels, rng, config,
    )

    # ─── Step 5: Compute disease-specific shifts ──────────────────────────
    logger.info("Step 5: Computing disease-specific abundance shifts...")
    disease_shifts = compute_disease_shifts(disease_labels)

    # ─── Step 6: Extract age values ───────────────────────────────────────
    age_values = pd.to_numeric(
        clinical_df["Age"], errors="coerce"
    ).fillna(constants.AGE_REFERENCE).values.astype(float)

    # ─── Step 7: Generate bacterial abundances ────────────────────────────
    logger.info("Step 7: Generating beneficial bacteria...")
    beneficial_df = generate_beneficial_bacteria(
        rng, risk_scores, disease_shifts, age_values,
    )

    logger.info("Step 8: Generating inflammatory bacteria...")
    inflammatory_df = generate_inflammatory_bacteria(
        rng, risk_scores, disease_shifts, age_values,
    )

    logger.info("Step 9: Generating context-dependent bacteria...")
    context_df = generate_context_dependent_bacteria(
        rng, risk_scores, disease_shifts, age_values,
    )

    # Combine all bacteria
    bacteria_df = pd.concat(
        [beneficial_df, inflammatory_df, context_df],
        axis=1,
    )

    # ─── Step 8: Apply correlation structure ──────────────────────────────
    logger.info("Step 10: Applying correlation structure...")
    target_corr = build_target_correlation_matrix(constants.ALL_BACTERIA)
    bacteria_df = apply_correlation_structure(
        bacteria_df,
        constants.ALL_BACTERIA,
        target_corr,
        strength=config.correlation_strength,
        rng=rng,
    )

    # ─── Step 9: Generate Shannon Diversity Index ─────────────────────────
    logger.info("Step 11: Generating Shannon Diversity Index...")
    shannon_values = generate_shannon_diversity(
        rng, bacteria_df, risk_scores, age_values,
    )

    # ─── Step 10: Assemble the full microbiome DataFrame ──────────────────
    microbiome_df = bacteria_df.copy()
    microbiome_df["Shannon_Diversity_Index"] = shannon_values

    # ─── Step 11: Inject biological noise ─────────────────────────────────
    logger.info("Step 12: Injecting biological noise...")
    microbiome_df = inject_noise(microbiome_df, rng, config)

    # ─── Step 12: Assemble complete dataset ───────────────────────────────
    logger.info("Step 13: Assembling complete dataset...")
    gut_df = alignment_df.reset_index(drop=True).copy()
    for feature in constants.MICROBIOME_FEATURES:
        gut_df[feature] = microbiome_df[feature].values

    # ─── Step 13: Patient-level validation with regeneration ──────────────
    logger.info("Step 14: Running patient-level validation...")
    total_regenerated = 0
    for idx in range(n_patients):
        patient = gut_df.iloc[idx]
        is_valid, issues = validate_patient(patient)

        if not is_valid:
            # Regenerate microbiome features for this patient
            for attempt in range(config.max_regeneration_attempts):
                regen_rng = create_rng(config.seed + idx * 1000 + attempt + 1)

                # Regenerate from individual patient context
                patient_risk = risk_scores[idx:idx + 1]
                patient_shifts = disease_shifts.iloc[idx:idx + 1].reset_index(drop=True)
                patient_age = age_values[idx:idx + 1]

                ben = generate_beneficial_bacteria(
                    regen_rng, patient_risk, patient_shifts, patient_age,
                )
                inf = generate_inflammatory_bacteria(
                    regen_rng, patient_risk, patient_shifts, patient_age,
                )
                ctx = generate_context_dependent_bacteria(
                    regen_rng, patient_risk, patient_shifts, patient_age,
                )

                regen_bacteria = pd.concat([ben, inf, ctx], axis=1)
                regen_shannon = generate_shannon_diversity(
                    regen_rng, regen_bacteria, patient_risk, patient_age,
                )

                # Update the row
                for feature in constants.ALL_BACTERIA:
                    gut_df.at[idx, feature] = regen_bacteria[feature].values[0]
                gut_df.at[idx, "Shannon_Diversity_Index"] = regen_shannon[0]

                # Re-validate
                is_valid, issues = validate_patient(gut_df.iloc[idx])
                if is_valid:
                    total_regenerated += 1
                    break
            else:
                logger.warning(
                    "Patient %s failed validation after %d attempts: %s",
                    gut_df.at[idx, "Patient_ID"],
                    config.max_regeneration_attempts,
                    "; ".join(issues),
                )

    if total_regenerated > 0:
        logger.info("Regenerated microbiome features for %d patients.", total_regenerated)

    # ─── Step 14: Round values ────────────────────────────────────────────
    for feature in constants.ALL_BACTERIA:
        if feature in gut_df.columns:
            gut_df[feature] = gut_df[feature].round(config.abundance_decimal_places)
    gut_df["Shannon_Diversity_Index"] = gut_df["Shannon_Diversity_Index"].round(
        config.diversity_decimal_places
    )

    # ─── Step 15: Dataset-level validation ────────────────────────────────
    logger.info("Step 15: Running dataset-level validation...")
    all_passed, validation_results = validate_dataset(gut_df, clinical_df)

    if all_passed:
        logger.info("[PASS] Dataset validation PASSED.")
    else:
        logger.warning("[WARN] Dataset validation has warnings. Review the report.")

    # ─── Step 16: Export all outputs ──────────────────────────────────────
    logger.info("Step 16: Exporting output files...")

    dataset_path = output_dir / config.output_file
    export_dataset(
        gut_df, str(dataset_path),
        config.abundance_decimal_places,
        config.diversity_decimal_places,
    )

    export_summary_statistics(
        gut_df, str(output_dir / "dataset_summary.csv"),
    )

    export_feature_distribution_report(
        gut_df, str(output_dir / "feature_distribution_report.txt"),
    )

    export_correlation_matrix(
        gut_df, str(output_dir / "correlation_matrix.csv"),
    )

    generate_validation_report(
        validation_results,
        str(output_dir / "validation_report.txt"),
    )

    elapsed = time.time() - start_time
    logger.info("=" * 72)
    logger.info("PIPELINE COMPLETE in %.2f seconds.", elapsed)
    logger.info("Output: %s", dataset_path)
    logger.info("=" * 72)

    return gut_df
