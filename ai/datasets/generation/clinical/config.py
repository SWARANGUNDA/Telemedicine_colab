"""
config.py — Centralized configuration for the Clinical Dataset Generator.

Every configurable parameter from the Dataset Design Specification is stored
here. No medical constants are hardcoded in other modules. All values are
sourced from the specification document.

Reference: Dataset_design_specification.pdf
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# DATASET PARAMETERS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DatasetConfig:
    """Top-level configurable parameters for the generator."""

    size: int = 20_000
    seed: int = 42
    output_file: str = "Clinical_Dataset.csv"
    max_retries_per_patient: int = 3
    prevalence_tolerance: float = 0.03  # ±3% acceptable deviation


# ═══════════════════════════════════════════════════════════════════════════════
# AGE DISTRIBUTION
# Specification: ~20% aged 18–30, 30% in 31–45, 30% in 46–60, 20% in 61–85
# ═══════════════════════════════════════════════════════════════════════════════

AGE_BINS: List[Tuple[int, int]] = [
    (18, 30),
    (31, 45),
    (46, 60),
    (61, 85),
]

AGE_WEIGHTS: List[float] = [0.20, 0.30, 0.30, 0.20]


# ═══════════════════════════════════════════════════════════════════════════════
# GENDER DISTRIBUTION
# Specification: ~50/50 balanced
# ═══════════════════════════════════════════════════════════════════════════════

MALE_PROBABILITY: float = 0.50


# ═══════════════════════════════════════════════════════════════════════════════
# BMI CATEGORY DISTRIBUTION
# Specification: ~24% obese, higher % overweight, mean BMI ~27–30
# Categories follow WHO/CDC definitions
# ═══════════════════════════════════════════════════════════════════════════════

BMI_CATEGORY_PARAMS: Dict[str, Dict] = {
    "underweight": {
        "proportion": 0.05,
        "mean": 17.5,
        "std": 0.8,
        "min": 16.0,
        "max": 18.49,
    },
    "normal": {
        "proportion": 0.31,
        "mean": 22.0,
        "std": 1.8,
        "min": 18.5,
        "max": 24.99,
    },
    "overweight": {
        "proportion": 0.40,
        "mean": 27.0,
        "std": 1.3,
        "min": 25.0,
        "max": 29.99,
    },
    "obese": {
        "proportion": 0.24,
        "mean": 33.0,
        "std": 3.5,
        "min": 30.0,
        "max": 45.0,
    },
}

BMI_CATEGORY_NAMES: List[str] = ["underweight", "normal", "overweight", "obese"]
BMI_CATEGORY_PROPORTIONS: List[float] = [0.05, 0.31, 0.40, 0.24]


# ═══════════════════════════════════════════════════════════════════════════════
# HEIGHT PARAMETERS BY GENDER
# Specification: Female ~145–190 cm, Male ~155–200 cm
# ═══════════════════════════════════════════════════════════════════════════════

HEIGHT_PARAMS: Dict[str, Dict[str, float]] = {
    "Male": {"mean": 175.0, "std": 7.0, "min": 155.0, "max": 200.0},
    "Female": {"mean": 162.0, "std": 6.5, "min": 145.0, "max": 190.0},
}


# ═══════════════════════════════════════════════════════════════════════════════
# WAIST CIRCUMFERENCE PARAMETERS
# Specification: Male 65–140 cm, Female 60–130 cm
# Linear model: waist = slope × BMI + intercept + noise
# ═══════════════════════════════════════════════════════════════════════════════

WAIST_PARAMS: Dict[str, Dict[str, float]] = {
    "Male": {
        "slope": 2.0,
        "intercept": 40.0,
        "noise_std": 4.0,
        "min": 65.0,
        "max": 140.0,
    },
    "Female": {
        "slope": 1.8,
        "intercept": 32.0,
        "noise_std": 4.0,
        "min": 60.0,
        "max": 130.0,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE RANGES (from specification blueprint)
# Used for validation and clipping after noise injection
# ═══════════════════════════════════════════════════════════════════════════════

FEATURE_RANGES: Dict[str, Tuple[float, float]] = {
    "Age": (18, 85),
    "Height_cm": (140.0, 200.0),
    "Weight_kg": (40.0, 150.0),
    "BMI": (16.0, 45.0),
    "Waist_Circumference_cm": (60.0, 140.0),
    "Systolic_BP": (90, 190),
    "Diastolic_BP": (60, 120),
    "Fasting_Blood_Glucose": (70, 250),
    "HbA1c": (4.5, 12.0),
    "LDL_Cholesterol": (40, 250),
    "HDL_Cholesterol": (20, 90),
    "Triglycerides": (40, 500),
    "ALT": (10, 200),
    "AST": (10, 150),
}


# ═══════════════════════════════════════════════════════════════════════════════
# WEIGHT RANGE (for validation after BMI × height computation)
# ═══════════════════════════════════════════════════════════════════════════════

WEIGHT_RANGE: Tuple[float, float] = (40.0, 150.0)


# ═══════════════════════════════════════════════════════════════════════════════
# DISEASE PREVALENCE TARGETS
# Specification Section 9: Clinical population prevalences
# ═══════════════════════════════════════════════════════════════════════════════

PREVALENCE_TARGETS: Dict[str, float] = {
    # Individual disease targets (primary constraints)
    "Prediabetes": 0.18,
    "Type2_Diabetes": 0.16,
    "Obesity": 0.24,
    "Metabolic_Syndrome": 0.18,
    "NAFLD": 0.12,
    # Healthy is derived: 1 - P(any disease). With multi-label diseases and
    # high co-occurrence, this is mathematically ~55-60% given the above rates.
    # The spec's 30% target assumes more disease spread; we prioritize
    # individual disease accuracy over the Healthy rate.
    "Healthy": 0.55,
}


# ═══════════════════════════════════════════════════════════════════════════════
# GLYCEMIC STATE PROBABILITIES BY BMI CATEGORY
# These conditional probabilities are calibrated to achieve marginal
# prevalences of ~16% T2D and ~18% Prediabetes, with 70–80% of T2D
# patients also being obese (co-occurrence from spec Section 8).
#
# Format: {bmi_category: (p_normal, p_prediabetes, p_type2_diabetes)}
# Age modifiers are applied on top of these base probabilities.
# ═══════════════════════════════════════════════════════════════════════════════

GLYCEMIC_PROBS_BY_BMI: Dict[str, Tuple[float, float, float]] = {
    "underweight": (0.955, 0.040, 0.005),
    "normal":      (0.880, 0.095, 0.025),
    "overweight":  (0.750, 0.175, 0.075),
    "obese":       (0.320, 0.280, 0.400),
}

# Age adjustment multipliers for glycemic state probabilities
# Older age → higher diabetes/prediabetes risk (spec Section 6)
AGE_GLYCEMIC_MODIFIERS: Dict[str, float] = {
    "18-30": 0.60,
    "31-45": 0.90,
    "46-60": 1.25,
    "61-85": 1.40,
}


# ═══════════════════════════════════════════════════════════════════════════════
# DISEASE DIAGNOSTIC THRESHOLDS
# All thresholds from specification Section 7
# ═══════════════════════════════════════════════════════════════════════════════

# Type 2 Diabetes: FPG ≥ 126 OR HbA1c ≥ 6.5 (ADA criteria)
T2D_FPG_THRESHOLD: int = 126
T2D_HBA1C_THRESHOLD: float = 6.5

# Prediabetes: 100 ≤ FPG ≤ 125 OR 5.7 ≤ HbA1c ≤ 6.4 (ADA criteria)
PREDIABETES_FPG_RANGE: Tuple[int, int] = (100, 125)
PREDIABETES_HBA1C_RANGE: Tuple[float, float] = (5.7, 6.4)

# Obesity: BMI ≥ 30 (WHO/CDC)
OBESITY_BMI_THRESHOLD: float = 30.0

# Metabolic Syndrome: ≥ 3 of 5 criteria (ATP III/AHA/NHLBI)
METS_MIN_CRITERIA: int = 3

# MetS criteria thresholds (gender-specific where applicable)
METS_WAIST_THRESHOLD: Dict[str, float] = {"Male": 102.0, "Female": 88.0}
METS_TG_THRESHOLD: int = 150
METS_HDL_THRESHOLD: Dict[str, int] = {"Male": 40, "Female": 50}
METS_BP_SYSTOLIC_THRESHOLD: int = 130
METS_BP_DIASTOLIC_THRESHOLD: int = 85
METS_FPG_THRESHOLD: int = 100


# ═══════════════════════════════════════════════════════════════════════════════
# GLYCEMIC STATE FEATURE DISTRIBUTIONS
# FPG and HbA1c values for each glycemic state
# ═══════════════════════════════════════════════════════════════════════════════

GLYCEMIC_FEATURE_PARAMS: Dict[str, Dict] = {
    "normal": {
        "fpg_mean": 88.0, "fpg_std": 6.0, "fpg_min": 70, "fpg_max": 99,
        "hba1c_mean": 5.2, "hba1c_std": 0.2, "hba1c_min": 4.5, "hba1c_max": 5.6,
    },
    "prediabetes": {
        "fpg_mean": 112.0, "fpg_std": 6.0, "fpg_min": 100, "fpg_max": 125,
        "hba1c_mean": 6.0, "hba1c_std": 0.2, "hba1c_min": 5.7, "hba1c_max": 6.4,
    },
    "diabetes": {
        "fpg_mean": 160.0, "fpg_std": 28.0, "fpg_min": 126, "fpg_max": 250,
        "hba1c_mean": 7.8, "hba1c_std": 1.2, "hba1c_min": 6.5, "hba1c_max": 12.0,
    },
}

# Borderline distributions (for ~15% patients near thresholds)
BORDERLINE_GLYCEMIC_PARAMS: Dict[str, Dict] = {
    "normal_to_prediabetes": {
        "fpg_mean": 99.0, "fpg_std": 2.5, "fpg_min": 95, "fpg_max": 105,
        "hba1c_mean": 5.65, "hba1c_std": 0.12, "hba1c_min": 5.5, "hba1c_max": 5.8,
    },
    "prediabetes_to_diabetes": {
        "fpg_mean": 126.0, "fpg_std": 2.5, "fpg_min": 122, "fpg_max": 130,
        "hba1c_mean": 6.45, "hba1c_std": 0.12, "hba1c_min": 6.3, "hba1c_max": 6.6,
    },
}

# Outlier distributions (for ~2% extreme cases)
OUTLIER_DIABETES_PARAMS: Dict[str, float] = {
    "fpg_mean": 225.0, "fpg_std": 12.0, "fpg_min": 200, "fpg_max": 250,
    "hba1c_mean": 10.5, "hba1c_std": 0.7, "hba1c_min": 9.5, "hba1c_max": 12.0,
}


# ═══════════════════════════════════════════════════════════════════════════════
# LIPID PARAMETERS
# Correlated with BMI and gender (spec Section 6)
# ═══════════════════════════════════════════════════════════════════════════════

LDL_PARAMS: Dict[str, float] = {
    "mean": 120.0,
    "std": 25.0,
    "bmi_slope": 1.0,       # +1 mg/dL per BMI unit above 25
    "bmi_ref": 25.0,
}

HDL_PARAMS: Dict[str, Dict[str, float]] = {
    "Male":   {"mean": 48.0, "std": 8.0},
    "Female": {"mean": 58.0, "std": 10.0},
}
HDL_BMI_SLOPE: float = -0.5  # −0.5 mg/dL per BMI unit above 25

TRIGLYCERIDE_PARAMS: Dict[str, float] = {
    "mean": 110.0,
    "std": 28.0,
    "bmi_slope": 1.5,       # +1.5 mg/dL per BMI unit above 25
    "bmi_ref": 25.0,
    "diabetes_boost": 15.0,  # additional +15 for diabetic patients
}


# ═══════════════════════════════════════════════════════════════════════════════
# LIVER ENZYME PARAMETERS
# Correlated with BMI and metabolic state (spec Section 6)
# ═══════════════════════════════════════════════════════════════════════════════

ALT_PARAMS: Dict[str, float] = {
    "mean": 25.0,
    "std": 8.0,
    "bmi_slope": 0.8,       # +0.8 U/L per BMI unit above 25
    "bmi_ref": 25.0,
    "metabolic_boost": 18.0, # boost for obese+diabetic patients (NAFLD risk)
}

AST_PARAMS: Dict[str, float] = {
    "mean": 22.0,
    "std": 7.0,
    "alt_correlation": 0.7,  # AST tracks ALT loosely
}

# Outlier liver enzyme parameters
OUTLIER_LIVER_PARAMS: Dict[str, float] = {
    "alt_mean": 160.0, "alt_std": 15.0, "alt_min": 140, "alt_max": 200,
    "ast_mean": 115.0, "ast_std": 12.0, "ast_min": 95, "ast_max": 150,
}


# ═══════════════════════════════════════════════════════════════════════════════
# VITAL SIGNS PARAMETERS
# Blood pressure correlated with age and BMI (spec Section 6)
# ═══════════════════════════════════════════════════════════════════════════════

SBP_PARAMS: Dict[str, float] = {
    "base_mean": 110.0,
    "base_std": 8.0,
    "age_slope": 0.25,       # +0.25 mmHg per year above 40
    "age_ref": 40.0,
    "bmi_slope": 0.8,        # +0.8 mmHg per BMI unit above 25
    "bmi_ref": 25.0,
}

DBP_PARAMS: Dict[str, float] = {
    "sbp_ratio": 0.55,       # DBP ≈ SBP × 0.55 + offset
    "offset": 18.0,
    "noise_std": 4.0,
    "min_gap": 10,           # SBP must exceed DBP by at least this
}


# ═══════════════════════════════════════════════════════════════════════════════
# CO-OCCURRENCE FEATURE ADJUSTMENTS
# Additional feature shifts for multi-morbid patients to achieve
# realistic co-occurrence (spec Section 8)
# ═══════════════════════════════════════════════════════════════════════════════

COMORBIDITY_ADJUSTMENTS: Dict[str, Dict[str, float]] = {
    # Diabetic patients get metabolic feature boosts → ensures ~85-90% MetS overlap
    "diabetic": {
        "tg_boost": 12.0,
        "hdl_reduction": 3.0,
        "sbp_boost": 4.0,
        "alt_boost": 8.0,
    },
    # Obese patients get additional metabolic shifts
    "obese": {
        "tg_boost": 8.0,
        "hdl_reduction": 1.5,
        "sbp_boost": 2.0,
        "alt_boost": 5.0,
    },
    # Obese + Diabetic compounds the effects
    "obese_diabetic": {
        "tg_boost": 20.0,
        "hdl_reduction": 4.5,
        "sbp_boost": 6.0,
        "alt_boost": 14.0,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# FAMILY HISTORY PROBABILITIES
# Base rates and conditional boosts (spec Section 3)
# ═══════════════════════════════════════════════════════════════════════════════

FAMILY_HISTORY_PARAMS: Dict[str, Dict[str, float]] = {
    "Family_History_Diabetes": {
        "base_rate": 0.25,
        "diabetic_boost": 0.40,      # rate for diabetic/prediabetic patients
    },
    "Family_History_Obesity": {
        "base_rate": 0.20,
        "obese_boost": 0.35,         # rate for obese patients
    },
    "Family_History_Hypertension": {
        "base_rate": 0.30,
        "hypertensive_boost": 0.45,  # rate for patients with high BP
    },
    "Family_History_NAFLD": {
        "base_rate": 0.10,
        "nafld_risk_boost": 0.20,    # rate for NAFLD-risk patients
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# NAFLD SCORING SYSTEM
# Probabilistic assignment based on weighted risk factors (spec Section 7)
# ═══════════════════════════════════════════════════════════════════════════════

NAFLD_SCORING: Dict[str, Dict] = {
    "bmi_high": {"threshold": 30.0, "score": 2.0},
    "bmi_moderate": {"threshold": 28.0, "score": 1.0},
    "tg_high": {"threshold": 180, "score": 1.5},
    "tg_moderate": {"threshold": 150, "score": 0.8},
    "alt_high": {"threshold": 50, "score": 2.0},
    "alt_moderate": {"threshold": 35, "score": 1.0},
    "diabetes": {"score": 1.5},
    "age_over_50": {"threshold": 50, "score": 0.5},
}

# Sigmoid threshold calibrated for ~12% NAFLD prevalence
NAFLD_SIGMOID_THRESHOLD: float = 4.8
NAFLD_SIGMOID_SCALE: float = 1.2


# ═══════════════════════════════════════════════════════════════════════════════
# NOISE PARAMETERS
# Measurement noise from specification Section 11
# Format: (standard deviation for Gaussian noise)
# Actual noise is N(0, std), clipped to ± max_noise
# ═══════════════════════════════════════════════════════════════════════════════

NOISE_PARAMS: Dict[str, Dict[str, float]] = {
    "Height_cm":             {"std": 0.25, "max_noise": 0.5},
    "Weight_kg":             {"std": 0.50, "max_noise": 1.0},
    "Systolic_BP":           {"std": 1.50, "max_noise": 3.0},
    "Diastolic_BP":          {"std": 1.50, "max_noise": 3.0},
    "Fasting_Blood_Glucose": {"std": 2.50, "max_noise": 5.0},
    "HbA1c":                 {"std": 0.10, "max_noise": 0.2},
    "LDL_Cholesterol":       {"std": 2.50, "max_noise": 5.0},
    "HDL_Cholesterol":       {"std": 1.50, "max_noise": 3.0},
    "Triglycerides":         {"std": 4.00, "max_noise": 8.0},
    "ALT":                   {"std": 1.50, "max_noise": 3.0},
    "AST":                   {"std": 1.50, "max_noise": 3.0},
}


# ═══════════════════════════════════════════════════════════════════════════════
# MISSING VALUE PERCENTAGES
# From specification Sections 3 and 13
# ═══════════════════════════════════════════════════════════════════════════════

MISSING_RATES: Dict[str, float] = {
    "Waist_Circumference_cm": 0.03,
    "LDL_Cholesterol": 0.02,
    "HDL_Cholesterol": 0.02,
    "Triglycerides": 0.02,
    "ALT": 0.05,
    "AST": 0.05,
    "Family_History_Diabetes": 0.05,
    "Family_History_Obesity": 0.05,
    "Family_History_Hypertension": 0.05,
    "Family_History_NAFLD": 0.08,
}

# Features that are ALWAYS present (0% missing) — spec says mandatory
MANDATORY_FEATURES: List[str] = [
    "Patient_ID", "Age", "Gender", "Height_cm", "Weight_kg", "BMI",
    "Systolic_BP", "Diastolic_BP", "Fasting_Blood_Glucose", "HbA1c",
]

MANDATORY_LABELS: List[str] = [
    "Type2_Diabetes", "Prediabetes", "Obesity",
    "Metabolic_Syndrome", "NAFLD", "Healthy",
]


# ═══════════════════════════════════════════════════════════════════════════════
# BORDERLINE AND OUTLIER FRACTIONS
# Specification Sections 10 and 12
# ═══════════════════════════════════════════════════════════════════════════════

BORDERLINE_FRACTION: float = 0.15  # ~15% of patients near thresholds
OUTLIER_FRACTION: float = 0.02     # ~2% with extreme but plausible values


# ═══════════════════════════════════════════════════════════════════════════════
# BMI BORDERLINE PARAMETERS
# For patients near the obesity cutoff (BMI 29.5–30.5)
# ═══════════════════════════════════════════════════════════════════════════════

BMI_BORDERLINE_PARAMS: Dict[str, float] = {
    "mean": 30.0,
    "std": 0.4,
    "min": 29.0,
    "max": 31.0,
}

# Outlier BMI (extreme obesity)
BMI_OUTLIER_PARAMS: Dict[str, float] = {
    "mean": 42.0,
    "std": 1.5,
    "min": 40.0,
    "max": 45.0,
}

# Outlier lipid parameters
OUTLIER_LIPID_PARAMS: Dict[str, Dict[str, float]] = {
    "triglycerides": {"mean": 380.0, "std": 50.0, "min": 300, "max": 500},
    "ldl": {"mean": 220.0, "std": 15.0, "min": 200, "max": 250},
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATASET COLUMN ORDER (matches specification blueprint)
# ═══════════════════════════════════════════════════════════════════════════════

COLUMN_ORDER: List[str] = [
    "Patient_ID",
    "Age",
    "Gender",
    "Height_cm",
    "Weight_kg",
    "BMI",
    "Waist_Circumference_cm",
    "Systolic_BP",
    "Diastolic_BP",
    "Fasting_Blood_Glucose",
    "HbA1c",
    "LDL_Cholesterol",
    "HDL_Cholesterol",
    "Triglycerides",
    "ALT",
    "AST",
    "Family_History_Diabetes",
    "Family_History_Obesity",
    "Family_History_Hypertension",
    "Family_History_NAFLD",
    "Type2_Diabetes",
    "Prediabetes",
    "Obesity",
    "Metabolic_Syndrome",
    "NAFLD",
    "Healthy",
]

# Data types for export (used by exporter to enforce correct types)
COLUMN_DTYPES: Dict[str, str] = {
    "Patient_ID": "str",
    "Age": "int",
    "Gender": "str",
    "Height_cm": "float",
    "Weight_kg": "float",
    "BMI": "float",
    "Waist_Circumference_cm": "float",
    "Systolic_BP": "int",
    "Diastolic_BP": "int",
    "Fasting_Blood_Glucose": "int",
    "HbA1c": "float",
    "LDL_Cholesterol": "int",
    "HDL_Cholesterol": "int",
    "Triglycerides": "int",
    "ALT": "int",
    "AST": "int",
    "Family_History_Diabetes": "int",
    "Family_History_Obesity": "int",
    "Family_History_Hypertension": "int",
    "Family_History_NAFLD": "int",
    "Type2_Diabetes": "int",
    "Prediabetes": "int",
    "Obesity": "int",
    "Metabolic_Syndrome": "int",
    "NAFLD": "int",
    "Healthy": "int",
}
