"""
main.py — Main CLI orchestrator and entrypoint.

Executes the synthetic wearable dataset generation pipeline, validates the dataset,
and exports all six required research output files:
1. Wearable_Dataset.csv
2. dataset_summary_stats.csv
3. correlation_matrix.csv
4. feature_distribution_report.txt
5. disease_prevalence_report.txt
6. validation_report.txt

Usage:
    python -m wearable_dataset_generator.main              # Full 20,000 patients
    python -m wearable_dataset_generator.main --demo       # Demo mode (100 patients)
    python -m wearable_dataset_generator.main --seed 123   # Custom random seed
"""

import argparse
import logging
import sys
import time
from pathlib import Path

from . import config, generator, validation, utils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Wearable Dataset Generator — Synthetic Wearable EHR Metric Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m wearable_dataset_generator.main               # Generate full dataset\n"
            "  python -m wearable_dataset_generator.main --demo        # Generate demo (100 patients)\n"
            "  python -m wearable_dataset_generator.main --seed 123    # Custom random seed\n"
        ),
    )

    parser.add_argument(
        "--clinical-file",
        type=str,
        default="Clinical_Dataset.csv",
        help="Path to Master Patient Dataset (default: Clinical_Dataset.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="Wearable_Dataset.csv",
        help="Output CSV file path (default: Wearable_Dataset.csv)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Generate a small demo dataset (100 patients)",
    )
    parser.add_argument(
        "--noise-scale",
        type=float,
        default=1.0,
        help="Noise scale multiplier (default: 1.0)",
    )

    return parser.parse_args()


def main() -> None:
    """Main CLI entrypoint for the Wearable Dataset Generator."""
    args = parse_args()

    # Build Configuration Object
    cfg = config.WearableDatasetConfig()
    cfg.clinical_dataset_path = args.clinical_file
    cfg.output_file = args.output
    cfg.seed = args.seed
    cfg.demo_mode = args.demo
    cfg.noise_scale = args.noise_scale

    if args.demo:
        logger.info("=" * 60)
        logger.info("DEMO MODE: Generating 100 patients for fast testing")
        logger.info("=" * 60)

    # 1. Run Generation Pipeline
    wearable_df, clinical_df = generator.generate_wearable_dataset(cfg)

    # 2. Run Dataset-Wide Validation Suite
    all_valid, summary = validation.validate_wearable_dataset(wearable_df, clinical_df)

    # 3. Export Main Dataset CSV
    logger.info(f"Exporting final wearable dataset to '{cfg.output_file}'...")
    wearable_df.to_csv(cfg.output_file, index=False)

    # 4. Generate all 5 required analytical report files
    logger.info("Generating analytical research reports...")
    utils.generate_summary_stats_csv(wearable_df, "dataset_summary_stats.csv")
    utils.generate_correlation_matrix_csv(wearable_df, "correlation_matrix.csv")
    utils.generate_feature_distribution_report(wearable_df, "feature_distribution_report.txt")
    utils.generate_disease_prevalence_report(wearable_df, "disease_prevalence_report.txt")
    utils.generate_validation_report_file(all_valid, summary, wearable_df, "validation_report.txt")

    # 5. Output Final Logging Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("WEARABLE DATASET GENERATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  Output CSV       : {cfg.output_file}")
    logger.info(f"  Total Patients   : {len(wearable_df):,}")
    logger.info(f"  Feature Count    : {len(wearable_df.columns)}")
    logger.info(f"  Validation Status: {'PASSED ✓' if all_valid else 'WARNINGS PRESENT ⚠'}")
    logger.info("  Generated Reports:")
    logger.info("    - dataset_summary_stats.csv")
    logger.info("    - correlation_matrix.csv")
    logger.info("    - feature_distribution_report.txt")
    logger.info("    - disease_prevalence_report.txt")
    logger.info("    - validation_report.txt")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
