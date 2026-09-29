"""
loader.py — Master Clinical Dataset loader and validator.

Loads Clinical_Dataset.csv, validates required columns, extracts alignment
metadata and clinical context columns, and provides per-patient access for
the generation pipeline. Handles missing values gracefully.
"""

import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

from . import constants

logger = logging.getLogger("gut_microbiome_generator")


def load_clinical_dataset(filepath: str) -> pd.DataFrame:
    """Load and validate the Master Clinical Dataset.

    Reads Clinical_Dataset.csv, verifies that all required alignment and
    clinical context columns are present, and logs dataset summary.

    Args:
        filepath: Path to Clinical_Dataset.csv.

    Returns:
        DataFrame containing the full clinical dataset.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If required columns are missing.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Clinical dataset not found: {filepath}")

    logger.info("Loading Clinical Dataset from: %s", filepath)
    df = pd.read_csv(filepath, dtype={"Patient_ID": str})

    # Validate required alignment columns
    missing_alignment = set(constants.ALIGNMENT_COLUMNS) - set(df.columns)
    if missing_alignment:
        raise ValueError(
            f"Missing alignment columns in Clinical Dataset: {missing_alignment}"
        )

    # Validate clinical context columns (warn if missing, don't fail)
    missing_context = set(constants.CLINICAL_CONTEXT_COLUMNS) - set(df.columns)
    if missing_context:
        logger.warning(
            "Missing clinical context columns (will use defaults): %s",
            missing_context,
        )

    logger.info(
        "Clinical Dataset loaded: %d patients, %d columns",
        len(df),
        len(df.columns),
    )

    # Log disease prevalence summary
    for disease in constants.DISEASE_LABEL_COLUMNS:
        if disease in df.columns:
            count = df[disease].sum()
            pct = count / len(df) * 100
            logger.info("  %s: %d (%.1f%%)", disease, count, pct)

    return df


def extract_alignment_data(clinical_df: pd.DataFrame) -> pd.DataFrame:
    """Extract alignment metadata columns for the output dataset.

    These columns are copied verbatim into the Gut Microbiome Dataset
    without any modification to maintain multimodal patient alignment.

    Args:
        clinical_df: Full clinical dataset DataFrame.

    Returns:
        DataFrame containing only alignment columns.
    """
    return clinical_df[constants.ALIGNMENT_COLUMNS].copy()


def extract_clinical_context(clinical_df: pd.DataFrame) -> pd.DataFrame:
    """Extract clinical context columns used for microbiome generation.

    These columns are used internally to compute latent metabolic risk
    and modulate bacterial abundance distributions. They are NOT exported
    to the Gut Microbiome Dataset.

    Missing values are preserved as NaN for downstream imputation with
    population defaults during risk score calculation.

    Args:
        clinical_df: Full clinical dataset DataFrame.

    Returns:
        DataFrame containing clinical context columns (numeric).
    """
    available_cols = [
        col for col in constants.CLINICAL_CONTEXT_COLUMNS
        if col in clinical_df.columns
    ]

    context = clinical_df[available_cols].copy()

    # Convert to numeric, coercing errors to NaN
    for col in context.columns:
        context[col] = pd.to_numeric(context[col], errors="coerce")

    return context


def validate_patient_alignment(
    clinical_df: pd.DataFrame,
    gut_df: pd.DataFrame,
) -> Tuple[bool, str]:
    """Verify that alignment columns are identical between datasets.

    Args:
        clinical_df: Original Clinical Dataset.
        gut_df: Generated Gut Microbiome Dataset.

    Returns:
        Tuple of (is_valid, message).
    """
    issues: list = []

    # Check row count
    if len(clinical_df) != len(gut_df):
        issues.append(
            f"Row count mismatch: Clinical={len(clinical_df)}, Gut={len(gut_df)}"
        )

    # Check each alignment column
    for col in constants.ALIGNMENT_COLUMNS:
        if col not in gut_df.columns:
            issues.append(f"Missing column in Gut Dataset: {col}")
            continue

        clinical_vals = clinical_df[col].values
        gut_vals = gut_df[col].values

        if len(clinical_vals) != len(gut_vals):
            issues.append(f"Length mismatch for {col}")
            continue

        # Use array comparison (handles NaN for numeric, exact for string)
        if col == "Patient_ID":
            mismatches = np.sum(clinical_vals != gut_vals)
        else:
            # Numeric columns: compare with NaN handling
            clinical_num = pd.to_numeric(
                pd.Series(clinical_vals), errors="coerce"
            )
            gut_num = pd.to_numeric(pd.Series(gut_vals), errors="coerce")
            mismatches = int(
                (~clinical_num.eq(gut_num) & ~(clinical_num.isna() & gut_num.isna())).sum()
            )

        if mismatches > 0:
            issues.append(
                f"Column '{col}': {mismatches} mismatched values"
            )

    if issues:
        return False, "; ".join(issues)
    return True, "All alignment columns verified identical."
