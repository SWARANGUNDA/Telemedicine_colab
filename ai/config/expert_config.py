"""
config.py — Central Configuration for Expert Models & Training Pipelines.

Avoids hardcoded configuration scattered across modules.
Centralizes random seeds, dataset paths, split ratios, CV folds, hyperparameter grids,
calibration settings, threshold tuning parameters, and artifact paths.
"""

from pathlib import Path
from typing import Any, Dict, List

# -----------------------------------------------------------------------------
# Global Reproducibility & Base Paths
# -----------------------------------------------------------------------------
RANDOM_SEED: int = 42

BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
AI_DIR: Path = BASE_DIR / "ai"

CLINICAL_DATASET_PATH: Path = BASE_DIR / "archive" / "v1" / "Clinical_Dataset.csv"
WEARABLE_DATASET_PATH: Path = BASE_DIR / "archive" / "v1" / "Wearable_Dataset.csv"
GUT_DATASET_PATH: Path = BASE_DIR / "archive" / "v1" / "Gut_Microbiome_Dataset.csv"

EXPERT_MODELS_DIR: Path = AI_DIR / "models"
SCHEMAS_DIR: Path = AI_DIR / "datasets" / "schemas"
SPLITS_DIR: Path = BASE_DIR / "archive" / "legacy_datasets" / "expert_models_splits"
SAVED_MODELS_DIR: Path = AI_DIR / "models"
REPORTS_DIR: Path = BASE_DIR / "reports" / "evaluation"

PATIENT_SPLIT_PATH: Path = SPLITS_DIR / "patient_split.csv"

# Ensure directories exist
SPLITS_DIR.mkdir(parents=True, exist_ok=True)
SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# Target Labels & Split Configuration
# -----------------------------------------------------------------------------
TARGET_DISEASES: List[str] = [
    "Type2_Diabetes",
    "Prediabetes",
    "Obesity",
    "Metabolic_Syndrome",
    "NAFLD"
]

EXCLUDED_COLUMNS: List[str] = [
    "Patient_ID",
    "Healthy",
    "Split",
    "split"
] + TARGET_DISEASES

SPLIT_RATIOS: Dict[str, float] = {
    "train": 0.70,
    "val": 0.15,
    "test": 0.15
}

CV_FOLDS: int = 5


# -----------------------------------------------------------------------------
# Model Hyperparameters & Search Grids
# -----------------------------------------------------------------------------
XGBOOST_PARAMS: Dict[str, Any] = {
    "n_estimators": 150,
    "max_depth": 5,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": RANDOM_SEED,
    "n_jobs": -1,
    "eval_metric": "logloss"
}

LIGHTGBM_PARAMS: Dict[str, Any] = {
    "n_estimators": 150,
    "max_depth": 5,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": RANDOM_SEED,
    "n_jobs": -1,
    "verbose": -1
}

CATBOOST_PARAMS: Dict[str, Any] = {
    "iterations": 150,
    "depth": 5,
    "learning_rate": 0.05,
    "random_seed": RANDOM_SEED,
    "thread_count": -1,
    "verbose": False
}

RANDOM_FOREST_PARAMS: Dict[str, Any] = {
    "n_estimators": 150,
    "max_depth": 8,
    "min_samples_split": 5,
    "random_state": RANDOM_SEED,
    "n_jobs": -1
}


# -----------------------------------------------------------------------------
# Calibration & Threshold Tuning Settings
# -----------------------------------------------------------------------------
CALIBRATION_METHOD: str = "sigmoid"  # Options: 'sigmoid' (Platt) or 'isotonic'
THRESHOLD_SEARCH_MIN: float = 0.10
THRESHOLD_SEARCH_MAX: float = 0.90
THRESHOLD_SEARCH_STEP: float = 0.01
DEFAULT_THRESHOLD: float = 0.50

EXPERT_VERSION: str = "v1"
