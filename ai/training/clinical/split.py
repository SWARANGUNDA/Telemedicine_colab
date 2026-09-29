"""
split.py — Master Patient Split Generator.

Generates ONCE a shared Patient_ID level split across all 20,000 patients:
- 70% Train (~14,000)
- 15% Validation (~3,000)
- 15% Test (~3,000)

Uses multi-label stratified sampling to preserve disease prevalence and co-occurrences
across all 3 splits.

Saves output permanently to `expert_models/splits/patient_split.csv`.
Clinical, Wearable, and Gut experts MUST reuse this exact split unchanged.
"""

import logging
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from ai.config import expert_config as config

logger = logging.getLogger("expert_models.split")


def generate_master_patient_split(
    clinical_csv_path: Path = config.CLINICAL_DATASET_PATH,
    output_path: Path = config.PATIENT_SPLIT_PATH,
    seed: int = config.RANDOM_SEED
) -> pd.DataFrame:
    """Generate or load the master Patient_ID split table.

    If patient_split.csv already exists, loads and returns it.
    Otherwise, computes multi-label stratified split and saves it.

    Args:
        clinical_csv_path: Path to Master Clinical Dataset CSV.
        output_path: Output CSV filepath for patient_split.csv.
        seed: Random seed.

    Returns:
        DataFrame with columns ['Patient_ID', 'Split'].
    """
    if output_path.exists():
        logger.info("Loading existing master patient split from: %s", output_path)
        split_df = pd.read_csv(output_path, dtype={"Patient_ID": str})
        return split_df

    logger.info("Generating new master patient split from: %s", clinical_csv_path)
    df = pd.read_csv(clinical_csv_path, dtype={"Patient_ID": str})

    # Combine multi-label targets into composite stratification keys
    target_cols = config.TARGET_DISEASES
    raw_keys = df[target_cols].astype(str).agg("_".join, axis=1)

    # If any key combination has count < 2, map it to the most frequent key
    key_counts = raw_keys.value_counts()
    most_common = key_counts.index[0]
    strat_key = raw_keys.map(lambda k: k if key_counts[k] >= 2 else most_common)

    # First split: 70% Train, 30% Temp (Val + Test)
    train_df, temp_df = train_test_split(
        df,
        test_size=0.30,
        random_state=seed,
        stratify=strat_key
    )

    # Second split: 50% Val, 50% Test of Temp (i.e. 15% Val, 15% Test overall)
    temp_raw_keys = temp_df[target_cols].astype(str).agg("_".join, axis=1)
    temp_counts = temp_raw_keys.value_counts()
    temp_most_common = temp_counts.index[0]
    temp_strat = temp_raw_keys.map(lambda k: k if temp_counts[k] >= 2 else temp_most_common)

    val_df, test_df = train_test_split(
        temp_df,
        test_size=0.50,
        random_state=seed,
        stratify=temp_strat
    )

    # Assign split labels
    split_records = []
    for pid in train_df["Patient_ID"]:
        split_records.append({"Patient_ID": str(pid), "Split": "train"})
    for pid in val_df["Patient_ID"]:
        split_records.append({"Patient_ID": str(pid), "Split": "val"})
    for pid in test_df["Patient_ID"]:
        split_records.append({"Patient_ID": str(pid), "Split": "test"})

    split_df = pd.DataFrame(split_records)

    # Ensure output directory exists and save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    split_df.to_csv(output_path, index=False)
    logger.info(
        "Master Patient Split saved to %s: Train=%d, Val=%d, Test=%d",
        output_path, len(train_df), len(val_df), len(test_df)
    )

    return split_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_master_patient_split()
