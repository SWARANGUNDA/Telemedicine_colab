"""
main.py — CLI entry point for the Gut Microbiome Dataset Generator.

Configures the generation pipeline, executes end-to-end dataset creation,
and produces all required output files. Run from the project root:

    python gut_microbiome_dataset_generator/main.py

Or with custom clinical dataset path:

    python gut_microbiome_dataset_generator/main.py --clinical-path path/to/Clinical_Dataset.csv
"""

import argparse
import logging
import sys
from pathlib import Path

from .config import GutMicrobiomeConfig
from .generator import run_pipeline
from .utils import setup_logging


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Gut Microbiome Dataset Generator — Synthetic 16S rRNA profile generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--clinical-path",
        type=str,
        default="Clinical_Dataset.csv",
        help="Path to the master Clinical_Dataset.csv (default: Clinical_Dataset.csv)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Directory for output files (default: current directory)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--noise-scale",
        type=float,
        default=1.0,
        help="Noise amplitude multiplier (default: 1.0)",
    )
    parser.add_argument(
        "--correlation-strength",
        type=float,
        default=0.8,
        help="Correlation engine strength 0.0-1.0 (default: 0.8)",
    )
    parser.add_argument(
        "--no-noise",
        action="store_true",
        help="Disable post-generation noise injection",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the dataset generation pipeline."""
    args = parse_arguments()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(level=log_level)

    logger.info("Gut Microbiome Dataset Generator v1.0.0")
    logger.info("Python %s", sys.version)

    # Resolve paths
    clinical_path = Path(args.clinical_path)
    output_dir = Path(args.output_dir)

    if not clinical_path.exists():
        logger.error("Clinical dataset not found: %s", clinical_path)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Build configuration
    config = GutMicrobiomeConfig(
        clinical_dataset_path=str(clinical_path),
        output_dir=str(output_dir),
        seed=args.seed,
        noise_scale=args.noise_scale,
        correlation_strength=args.correlation_strength,
        enable_noise=not args.no_noise,
    )

    logger.info("Configuration:")
    logger.info("  Clinical Dataset: %s", config.clinical_dataset_path)
    logger.info("  Output Directory: %s", config.output_dir)
    logger.info("  Seed: %d", config.seed)
    logger.info("  Noise: %s (scale=%.2f)", config.enable_noise, config.noise_scale)
    logger.info("  Correlation Strength: %.2f", config.correlation_strength)

    # Run the pipeline
    try:
        gut_df = run_pipeline(config)
        logger.info("SUCCESS: Generated Gut Microbiome Dataset with %d patients.", len(gut_df))
    except Exception as e:
        logger.exception("Pipeline failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
