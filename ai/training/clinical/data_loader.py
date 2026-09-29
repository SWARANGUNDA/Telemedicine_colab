"""
data_loader.py — Common Dataset Loader for Clinical, Wearable, and Gut Experts.

Loads datasets, validates required predictor columns against JSON schemas,
enforces Patient_ID uniqueness and shared 1-to-1 alignment with `patient_split.csv`,
verifies feature ordering, and strictly separates X (approved predictors only) from
y (5 disease targets).

Never includes Patient_ID, Healthy, target columns, split info, or other leakage fields in X.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from ai.config import expert_config as config
from . import split

logger = logging.getLogger("expert_models.data_loader")


def load_schema(schema_filename: str) -> Dict:
    """Load JSON predictor schema from expert_models/schemas/."""
    schema_path = config.SCHEMAS_DIR / schema_filename
    if not schema_path.exists():
        raise FileNotFoundError(f"Predictor schema not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_dataset_for_expert(
    dataset_path: Path,
    schema_filename: str,
    split_path: Path = config.PATIENT_SPLIT_PATH
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, List[str]]:
    """Load and validate dataset for a specific expert model.

    Args:
        dataset_path: Path to dataset CSV (Clinical, Wearable, or Gut).
        schema_filename: Schema JSON filename (e.g. 'clinical_features.json').
        split_path: Path to patient_split.csv.

    Returns:
        Tuple of (X, y, splits_series, approved_feature_order):
        - X: DataFrame containing ONLY approved predictor features in schema order
        - y: DataFrame containing 5 target disease columns
        - splits_series: Series indicating 'train', 'val', or 'test' per patient
        - approved_feature_order: List of predictor feature names
    """
    schema = load_schema(schema_filename)
    approved_predictors = [p["name"] for p in schema["predictors"]]

    # Load dataset & master split
    logger.info("Loading dataset: %s", dataset_path)
    df = pd.read_csv(dataset_path, dtype={"Patient_ID": str})
    split_df = split.generate_master_patient_split(output_path=split_path)

    # 1. Validate Patient_ID uniqueness
    if df["Patient_ID"].duplicated().any():
        raise ValueError(f"Duplicate Patient_IDs detected in {dataset_path}")

    # 2. Validate alignment with patient_split.csv
    if len(df) != len(split_df):
        raise ValueError(
            f"Dataset length mismatch: {dataset_path} has {len(df)} rows, "
            f"split table has {len(split_df)} rows."
        )

    merged = pd.merge(df, split_df, on="Patient_ID", how="left")
    if merged["Split"].isna().any():
        raise ValueError(f"Some Patient_IDs in {dataset_path} were not found in patient_split.csv")

    # 3. Validate target column availability
    for target in config.TARGET_DISEASES:
        if target not in merged.columns:
            if target == "High_Adiposity_Risk" and "Obesity" in merged.columns:
                continue
            if target == "Obesity" and "High_Adiposity_Risk" in merged.columns:
                continue
            raise ValueError(f"Target column '{target}' missing from {dataset_path}")

    # 4. Validate approved predictor availability
    missing_predictors = set(approved_predictors) - set(merged.columns)
    if missing_predictors:
        raise ValueError(
            f"Missing required predictor columns in {dataset_path}: {missing_predictors}"
        )

    # 5. Extract X (Approved predictors ONLY, strict ordering)
    X = merged[approved_predictors].copy()

    # 6. Extract y (5 Disease targets)
    target_cols = [c if c in merged.columns else ("Obesity" if c == "High_Adiposity_Risk" and "Obesity" in merged.columns else c) for c in config.TARGET_DISEASES]
    y = merged[target_cols].copy()

    # 7. Extract splits Series
    splits_series = merged["Split"].copy()

    # 8. Strict Leakage Verification
    leakage_check = set(X.columns).intersection(set(config.EXCLUDED_COLUMNS))
    if leakage_check:
        raise ValueError(f"LEAKAGE DETECTED in X predictors: {leakage_check}")

    logger.info(
        "Successfully loaded %s: %d patients, %d predictors, 5 targets. "
        "Splits: Train=%d, Val=%d, Test=%d",
        dataset_path.name,
        len(X),
        len(approved_predictors),
        (splits_series == "train").sum(),
        (splits_series == "val").sum(),
        (splits_series == "test").sum()
    )

    return X, y, splits_series, approved_predictors
