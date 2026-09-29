"""
main.py — Pipeline orchestrator for Clinical Dataset Generation.

Runs the complete generation pipeline:
    1. Initialize configuration and random seed
    2. Generate demographics (Patient_ID, Age, Gender)
    3. Assign metabolic profiles (BMI category, glycemic state)
    4. Generate anthropometry (Height, Weight, BMI, Waist)
    5. Generate vitals (SBP, DBP)
    6. Generate laboratory values (FPG, HbA1c, lipids, liver enzymes)
    7. Generate family history
    8. Inject measurement noise
    9. Assign disease labels from features
    10. Apply missing values
    11. Validate each patient
    12. Validate entire dataset
    13. Export to CSV

Usage:
    python -m clinical_dataset_generator.main                  # Full 20,000 patients
    python -m clinical_dataset_generator.main --demo           # Demo: 100 patients
    python -m clinical_dataset_generator.main --size 5000      # Custom size
    python -m clinical_dataset_generator.main --seed 123       # Custom seed
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

from . import config
from .demographics import generate_demographics
from .comorbidity import (
    assign_bmi_categories,
    assign_glycemic_states,
    assign_special_flags,
    get_comorbidity_adjustments,
)
from .anthropometry import generate_anthropometry
from .vitals import generate_vitals
from .laboratory import generate_laboratory
from .family_history import generate_family_history
from .disease_rules import assign_all_disease_labels
from .noise import inject_noise
from .missingness import apply_missingness
from .validator import validate_patient, validate_dataset
from .exporter import export_to_csv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def generate_dataset(cfg: config.DatasetConfig) -> pd.DataFrame:
    """Generate the complete synthetic clinical dataset.

    This is the main pipeline function. It generates all features,
    applies noise, assigns disease labels, applies missingness,
    and validates the result.

    Args:
        cfg: Dataset configuration with size, seed, and output file.

    Returns:
        Validated DataFrame containing the complete dataset.
    """
    n = cfg.size
    rng = np.random.default_rng(cfg.seed)

    logger.info(f"Starting dataset generation: {n:,} patients, seed={cfg.seed}")
    start_time = time.time()

    # ── Step 1: Demographics ──
    logger.info("Step 1/10: Generating demographics...")
    demographics = generate_demographics(n, rng)

    ages = demographics["Age"]
    genders = demographics["Gender"]

    # ── Step 2: Metabolic Profiles (internal, not stored) ──
    logger.info("Step 2/10: Assigning metabolic profiles...")
    bmi_categories = assign_bmi_categories(n, rng)
    glycemic_states = assign_glycemic_states(n, bmi_categories, ages, rng)
    is_borderline, is_outlier = assign_special_flags(n, rng)

    # Log profile summary
    _log_profile_summary(bmi_categories, glycemic_states, is_borderline, is_outlier)

    # Compute co-occurrence adjustments
    adjustments = get_comorbidity_adjustments(bmi_categories, glycemic_states)

    # ── Step 3: Anthropometry ──
    logger.info("Step 3/10: Generating anthropometric measurements...")
    anthropometry = generate_anthropometry(
        genders, bmi_categories, is_borderline, is_outlier, rng,
    )

    bmis = anthropometry["BMI"]

    # ── Step 4: Vitals ──
    logger.info("Step 4/10: Generating vital signs...")
    vitals = generate_vitals(
        ages, bmis, adjustments["sbp_boost"], rng,
    )

    # ── Step 5: Laboratory ──
    logger.info("Step 5/10: Generating laboratory parameters...")
    laboratory = generate_laboratory(
        ages, genders, bmis, glycemic_states,
        is_borderline, is_outlier, adjustments, rng,
    )

    # ── Step 6: Family History ──
    logger.info("Step 6/10: Generating family history...")
    family_hist = generate_family_history(
        n, bmis, glycemic_states, vitals["Systolic_BP"], rng,
    )

    # ── Step 7: Assemble patient data ──
    logger.info("Step 7/10: Assembling patient records...")
    data = {}
    data.update(demographics)
    data.update(anthropometry)
    data.update(vitals)
    data.update(laboratory)
    data.update(family_hist)

    # ── Step 8: Inject Noise ──
    logger.info("Step 8/10: Injecting measurement noise...")
    data = inject_noise(data, rng)

    # ── Step 9: Assign Disease Labels (from noisy features) ──
    logger.info("Step 9/10: Assigning disease labels...")
    labels = assign_all_disease_labels(data, rng)
    data.update(labels)

    # Log prevalence summary
    _log_prevalence_summary(labels, n)

    # ── Step 10: Apply Missing Values ──
    logger.info("Step 10/10: Applying missing values...")
    data = apply_missingness(data, ages, bmis, rng)

    # ── Build DataFrame ──
    logger.info("Building DataFrame...")
    df = pd.DataFrame(data)

    # Reorder columns
    available_cols = [c for c in config.COLUMN_ORDER if c in df.columns]
    df = df[available_cols]

    elapsed = time.time() - start_time
    logger.info(f"Generation complete in {elapsed:.1f}s")

    return df


def validate_and_report(
    df: pd.DataFrame,
    cfg: config.DatasetConfig,
) -> bool:
    """Run all validations and log results.

    Args:
        df: Generated dataset DataFrame.
        cfg: Dataset configuration.

    Returns:
        True if all critical validations pass.
    """
    logger.info("=" * 60)
    logger.info("VALIDATION REPORT")
    logger.info("=" * 60)

    # Per-patient validation (sample check for large datasets)
    sample_size = min(len(df), 1000)
    sample_indices = np.random.default_rng(cfg.seed).choice(
        len(df), size=sample_size, replace=False,
    )

    patient_errors = 0
    for idx in sample_indices:
        row = df.iloc[idx].to_dict()
        is_valid, errors = validate_patient(row)
        if not is_valid:
            patient_errors += 1
            if patient_errors <= 5:  # Log first 5 errors
                logger.warning(
                    f"Patient {row.get('Patient_ID', idx)} validation errors: "
                    f"{errors}"
                )

    if patient_errors > 0:
        logger.warning(
            f"Per-patient validation: {patient_errors}/{sample_size} "
            f"sampled patients had errors"
        )
    else:
        logger.info(
            f"Per-patient validation: All {sample_size} sampled patients valid"
        )

    # Dataset-wide validation
    all_valid, summary = validate_dataset(df, cfg)

    # Log summary
    for check_name, check_result in summary.items():
        if isinstance(check_result, dict):
            valid = check_result.get("valid", True)
            status = "✓ PASS" if valid else "✗ FAIL"
            logger.info(f"  {status} - {check_name}")

            # Log details for prevalence
            if check_name == "prevalence" and "details" in check_result:
                for disease, info in check_result["details"].items():
                    marker = "✓" if info["within_tolerance"] else "✗"
                    logger.info(
                        f"    {marker} {disease}: target={info['target']:.1%}, "
                        f"actual={info['actual']:.1%}, "
                        f"deviation={info['deviation']:.1%}"
                    )

            # Log correlation details
            if check_name == "correlations" and "details" in check_result:
                for pair, info in check_result["details"].items():
                    logger.info(f"    {pair}: {info}")

    logger.info("=" * 60)

    return all_valid


def _log_profile_summary(
    bmi_categories: np.ndarray,
    glycemic_states: np.ndarray,
    is_borderline: np.ndarray,
    is_outlier: np.ndarray,
) -> None:
    """Log internal metabolic profile distribution."""
    n = len(bmi_categories)

    logger.info("  BMI categories:")
    for cat in config.BMI_CATEGORY_NAMES:
        count = (bmi_categories == cat).sum()
        logger.info(f"    {cat}: {count:,} ({count/n:.1%})")

    logger.info("  Glycemic states:")
    for state in ["normal", "prediabetes", "diabetes"]:
        count = (glycemic_states == state).sum()
        logger.info(f"    {state}: {count:,} ({count/n:.1%})")

    logger.info(
        f"  Borderline: {is_borderline.sum():,} ({is_borderline.mean():.1%})"
    )
    logger.info(
        f"  Outliers: {is_outlier.sum():,} ({is_outlier.mean():.1%})"
    )


def _log_prevalence_summary(labels: Dict[str, np.ndarray], n: int) -> None:
    """Log disease prevalence summary."""
    logger.info("  Disease prevalence:")
    for disease, target in config.PREVALENCE_TARGETS.items():
        if disease in labels:
            actual = labels[disease].mean()
            status = "✓" if abs(actual - target) <= 0.03 else "⚠"
            logger.info(
                f"    {status} {disease}: {actual:.1%} "
                f"(target: {target:.1%})"
            )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Clinical Dataset Generator — Generate synthetic EHR data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m clinical_dataset_generator.main              "
            "# Generate 20,000 patients\n"
            "  python -m clinical_dataset_generator.main --demo       "
            "# Generate 100 patients (demo)\n"
            "  python -m clinical_dataset_generator.main --size 5000  "
            "# Custom size\n"
            "  python -m clinical_dataset_generator.main --seed 123   "
            "# Custom seed\n"
        ),
    )

    parser.add_argument(
        "--size", type=int, default=None,
        help="Number of patients to generate (default: 20000)",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output CSV file path (default: Clinical_Dataset.csv)",
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Generate a small demo dataset (100 patients)",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the Clinical Dataset Generator."""
    args = parse_args()

    # Build configuration
    cfg = config.DatasetConfig()

    if args.demo:
        cfg.size = 100
        cfg.output_file = "Clinical_Dataset_Demo.csv"
        logger.info("=" * 60)
        logger.info("DEMO MODE: Generating 100 patients for testing")
        logger.info("=" * 60)
    elif args.size is not None:
        cfg.size = args.size

    cfg.seed = args.seed

    if args.output is not None:
        cfg.output_file = args.output

    # Generate dataset
    df = generate_dataset(cfg)

    # Validate
    is_valid = validate_and_report(df, cfg)

    # Export
    output_path = export_to_csv(df, cfg.output_file)

    # Final summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("GENERATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  Output file: {output_path}")
    logger.info(f"  Patients: {len(df):,}")
    logger.info(f"  Features: {len(df.columns)}")
    logger.info(f"  Validation: {'PASSED' if is_valid else 'WARNINGS PRESENT'}")
    logger.info("=" * 60)

    if not is_valid:
        logger.warning(
            "Some validations had warnings. Review the log above for details."
        )
        sys.exit(0)  # Warnings are not fatal


if __name__ == "__main__":
    main()
