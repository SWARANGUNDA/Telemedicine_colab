"""
fusion_data_loader.py — Assembles fusion feature matrices from expert probabilities.

Builds the concatenated probability feature matrices for each of the 7
modality pathways (C, W, G, C+W, C+G, W+G, C+W+G) and loads the
corresponding target labels from the master patient split.
"""

import logging
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from ai.config import expert_config as expert_config
from ai.config import fusion_config as config

logger = logging.getLogger("fusion_engine.fusion_data_loader")


def build_pathway_features(
    all_probs: Dict[str, Dict[str, np.ndarray]],
    pathway_key: str,
    split_name: str,
) -> np.ndarray:
    """Concatenate expert probability columns for a given pathway and split.

    Args:
        all_probs: Dict from oof_generator (modality -> split -> array).
        pathway_key: One of 'C', 'W', 'G', 'C+W', 'C+G', 'W+G', 'C+W+G'.
        split_name: One of 'train', 'val', 'test'.

    Returns:
        2D array of shape (n_samples, n_modalities * 5).
    """
    modalities = config.PATHWAY_DEFINITIONS[pathway_key]
    arrays = [all_probs[mod][split_name] for mod in modalities]
    return np.hstack(arrays)


def load_targets_for_split(split_name: str) -> np.ndarray:
    """Load target labels for a specific split from the master dataset.

    Args:
        split_name: One of 'train', 'val', 'test'.

    Returns:
        2D array of shape (n_samples, 5).
    """
    split_df = pd.read_csv(config.PATIENT_SPLIT_PATH, dtype={"Patient_ID": str})
    clinical_df = pd.read_csv(config.CLINICAL_DATASET_PATH, dtype={"Patient_ID": str})

    # Merge to get proper alignment
    merged = clinical_df.merge(split_df, on="Patient_ID", how="inner")
    mask = merged["Split"] == split_name
    y = merged.loc[mask, config.TARGET_DISEASES].values

    return y


def get_feature_column_names(pathway_key: str) -> list:
    """Return ordered column names for a given pathway's feature matrix."""
    modalities = config.PATHWAY_DEFINITIONS[pathway_key]
    cols = []
    for mod in modalities:
        prefix = mod[:3].upper()  # CLI, WEA, GUT
        for disease in config.TARGET_DISEASES:
            cols.append(f"{prefix}_{disease}")
    return cols
