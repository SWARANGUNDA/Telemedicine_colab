"""
demographics.py — Clinical dataset loader and identity preservation module.

Loads the Master Patient Dataset (`Clinical_Dataset.csv`), preserves identity fields
(Patient_ID, Age, Gender, Disease Labels) without modification, and extracts
clinical biomarkers as context for downstream wearable feature generation.
"""

import logging
from pathlib import Path
from typing import Tuple, Dict, Any

import pandas as pd
import numpy as np

from . import constants

logger = logging.getLogger(__name__)


def load_clinical_master_dataset(
    file_path: str,
    demo_mode: bool = False,
    demo_size: int = 100,
) -> pd.DataFrame:
    """Load and validate the Master Patient Dataset (Clinical_Dataset.csv).

    Args:
        file_path: Path to the Clinical_Dataset.csv file.
        demo_mode: If True, slice the first demo_size patients.
        demo_size: Number of patients to include in demo mode.

    Returns:
        DataFrame containing the loaded and validated clinical data.

    Raises:
        FileNotFoundError: If Clinical_Dataset.csv does not exist.
        ValueError: If mandatory columns are missing from the dataset.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Master Patient Dataset not found at '{file_path}'. "
            "Please ensure Clinical_Dataset.csv is generated and present."
        )

    logger.info(f"Loading Master Patient Dataset from '{file_path}'...")
    df = pd.read_csv(file_path)

    # Validate mandatory identity columns
    for col in constants.PRESERVED_IDENTITY_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"Mandatory identity column '{col}' missing from {file_path}")

    # Validate target disease labels
    for col in constants.PRESERVED_DISEASE_LABELS:
        if col not in df.columns:
            raise ValueError(f"Mandatory disease label '{col}' missing from {file_path}")

    # Validate required clinical context features
    for col in constants.REQUIRED_CLINICAL_CONTEXT:
        if col not in df.columns:
            raise ValueError(f"Required clinical context feature '{col}' missing from {file_path}")

    if demo_mode:
        df = df.iloc[:demo_size].copy()
        logger.info(f"Demo mode active: Loaded first {len(df)} patients.")
    else:
        logger.info(f"Successfully loaded {len(df):,} patients from Master Patient Dataset.")

    return df


def extract_patient_context(df: pd.DataFrame) -> Dict[str, np.ndarray]:
    """Extract preserved identity fields and clinical context arrays from DataFrame.

    Args:
        df: Master clinical DataFrame.

    Returns:
        Dictionary containing extracted numpy arrays for identity and clinical variables.
    """
    context: Dict[str, np.ndarray] = {}

    # Preserved Identity Fields
    context["Patient_ID"] = df["Patient_ID"].to_numpy(dtype=str)
    context["Age"] = df["Age"].to_numpy(dtype=int)
    context["Gender"] = df["Gender"].to_numpy(dtype=str)

    # Preserved Disease Targets
    for disease in constants.PRESERVED_DISEASE_LABELS:
        context[disease] = df[disease].to_numpy(dtype=int)

    # Clinical Context Features (impute missing values if any exist in optional clinical labs)
    context["BMI"] = df["BMI"].to_numpy(dtype=float)
    context["Height_cm"] = df["Height_cm"].to_numpy(dtype=float)
    context["Weight_kg"] = df["Weight_kg"].to_numpy(dtype=float)

    # Clinical labs (fill potential NaNs with median for conditioning safety)
    context["Fasting_Blood_Glucose"] = (
        df["Fasting_Blood_Glucose"].fillna(df["Fasting_Blood_Glucose"].median()).to_numpy(dtype=float)
    )
    context["HbA1c"] = (
        df["HbA1c"].fillna(df["HbA1c"].median()).to_numpy(dtype=float)
    )
    context["Systolic_BP"] = (
        df["Systolic_BP"].fillna(df["Systolic_BP"].median()).to_numpy(dtype=float)
    )
    context["Diastolic_BP"] = (
        df["Diastolic_BP"].fillna(df["Diastolic_BP"].median()).to_numpy(dtype=float)
    )
    context["Triglycerides"] = (
        df["Triglycerides"].fillna(df["Triglycerides"].median()).to_numpy(dtype=float)
    )

    return context
