"""
config.py — Central Configuration for Phase 4 Multimodal Fusion Engine.

All paths, seeds, target ordering, modality definitions, pathway maps,
and hyperparameters for the late-fusion meta-learner system.
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Reproducibility & Base Paths
# ---------------------------------------------------------------------------
RANDOM_SEED: int = 42

BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
AI_DIR: Path = BASE_DIR / "ai"
FUSION_DIR: Path = AI_DIR / "training" / "fusion"

# Phase 3 frozen expert paths
EXPERT_MODELS_DIR: Path = AI_DIR / "models"
SPLITS_DIR: Path = BASE_DIR / "archive" / "legacy_datasets" / "expert_models_splits"
PATIENT_SPLIT_PATH: Path = SPLITS_DIR / "patient_split.csv"

# Phase 4 artifact paths
SAVED_MODELS_DIR: Path = AI_DIR / "models" / "fusion"
REPORTS_DIR: Path = BASE_DIR / "reports" / "evaluation"
OOF_DIR: Path = BASE_DIR / "archive" / "experimental_code" / "fusion_oof_probabilities"

# Ensure directories exist
SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
OOF_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Dataset Paths (read-only, Phase 1 artifacts)
# ---------------------------------------------------------------------------
CLINICAL_DATASET_PATH: Path = BASE_DIR / "archive" / "v1" / "Clinical_Dataset.csv"
WEARABLE_DATASET_PATH: Path = BASE_DIR / "archive" / "v1" / "Wearable_Dataset.csv"
GUT_DATASET_PATH: Path = BASE_DIR / "archive" / "v1" / "Gut_Microbiome_Dataset.csv"

# ---------------------------------------------------------------------------
# Target Diseases — STRICT ORDER (must match expert models)
# ---------------------------------------------------------------------------
TARGET_DISEASES: List[str] = [
    "Type2_Diabetes",
    "Prediabetes",
    "Obesity",
    "Metabolic_Syndrome",
    "NAFLD",
]

# ---------------------------------------------------------------------------
# Modality Definitions
# ---------------------------------------------------------------------------
MODALITY_KEYS: List[str] = ["clinical", "wearable", "gut"]

MODALITY_EXPERT_MAP: Dict[str, Dict[str, str]] = {
    "clinical": {
        "expert_name": "clinical",
        "version": "v1",
        "dataset_path": str(CLINICAL_DATASET_PATH),
        "schema_file": "clinical_features.json",
    },
    "wearable": {
        "expert_name": "wearable",
        "version": "v1",
        "dataset_path": str(WEARABLE_DATASET_PATH),
        "schema_file": "wearable_features.json",
    },
    "gut": {
        "expert_name": "gut",
        "version": "v1",
        "dataset_path": str(GUT_DATASET_PATH),
        "schema_file": "gut_features.json",
    },
}

# ---------------------------------------------------------------------------
# Adaptive Modality Pathways — All Valid Subsets
# ---------------------------------------------------------------------------
# Each pathway key maps to the tuple of active modality keys.
PATHWAY_DEFINITIONS: Dict[str, Tuple[str, ...]] = {
    "C":     ("clinical",),
    "W":     ("wearable",),
    "G":     ("gut",),
    "C+W":   ("clinical", "wearable"),
    "C+G":   ("clinical", "gut"),
    "W+G":   ("wearable", "gut"),
    "C+W+G": ("clinical", "wearable", "gut"),
}

# Number of probability features per pathway
# Each modality contributes 5 probabilities (one per disease).
def get_pathway_n_features(pathway_key: str) -> int:
    """Return number of input features for a given pathway."""
    return len(PATHWAY_DEFINITIONS[pathway_key]) * len(TARGET_DISEASES)

# ---------------------------------------------------------------------------
# OOF Generation Config
# ---------------------------------------------------------------------------
OOF_N_FOLDS: int = 5

# ---------------------------------------------------------------------------
# Meta-Learner Hyperparameters
# ---------------------------------------------------------------------------
META_LR_PARAMS: Dict[str, Any] = {
    "C": 1.0,
    "penalty": "l2",
    "solver": "lbfgs",
    "max_iter": 1000,
    "random_state": RANDOM_SEED,
}

META_XGB_PARAMS: Dict[str, Any] = {
    "n_estimators": 100,
    "max_depth": 3,
    "learning_rate": 0.1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": RANDOM_SEED,
    "n_jobs": -1,
    "eval_metric": "logloss",
}

# ---------------------------------------------------------------------------
# Calibration & Threshold Tuning
# ---------------------------------------------------------------------------
CALIBRATION_METHOD: str = "sigmoid"
DEFAULT_THRESHOLD: float = 0.50
THRESHOLD_SEARCH_MIN: float = 0.10
THRESHOLD_SEARCH_MAX: float = 0.90
THRESHOLD_SEARCH_STEP: float = 0.01

# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------
FUSION_VERSION: str = "v1"
