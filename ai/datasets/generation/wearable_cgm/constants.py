"""
constants.py — Fixed medical constants, feature bounds, and column mappings.

Defines feature names, physiological bounds, clinical column requirements,
and exported dataset column ordering for the Wearable Dataset Generator.
"""

from typing import List, Dict, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# COLUMN AND FEATURE NAMES
# ═══════════════════════════════════════════════════════════════════════════════

# Preserved identity & metadata fields from Clinical_Dataset.csv
PRESERVED_IDENTITY_COLUMNS: List[str] = [
    "Patient_ID",
    "Age",
    "Gender",
]

PRESERVED_DISEASE_LABELS: List[str] = [
    "Type2_Diabetes",
    "Prediabetes",
    "Obesity",
    "Metabolic_Syndrome",
    "NAFLD",
    "Healthy",
]

# Required clinical context features for conditioning wearable metrics
REQUIRED_CLINICAL_CONTEXT: List[str] = [
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
]

# Wearable-derived features to generate
WEARABLE_GENERATED_FEATURES: List[str] = [
    "Average_Daily_Steps",
    "Active_Minutes",
    "Sedentary_Time_Minutes",
    "Resting_Heart_Rate",
    "Sleep_Duration",
    "Calories_Burned",
    "Average_Glucose",
    "Glucose_Variability",
    "Time_In_Range",
    "Time_Above_Range",
]

# Final exported CSV column order
OUTPUT_COLUMN_ORDER: List[str] = [
    "Patient_ID",
    "Age",
    "Gender",
    "Average_Daily_Steps",
    "Active_Minutes",
    "Sedentary_Time_Minutes",
    "Resting_Heart_Rate",
    "Sleep_Duration",
    "Calories_Burned",
    "Average_Glucose",
    "Glucose_Variability",
    "Time_In_Range",
    "Time_Above_Range",
    "Type2_Diabetes",
    "Prediabetes",
    "Obesity",
    "Metabolic_Syndrome",
    "NAFLD",
    "Healthy",
]

# Data types for export enforcement
COLUMN_DTYPES: Dict[str, str] = {
    "Patient_ID": "str",
    "Age": "int64",
    "Gender": "str",
    "Average_Daily_Steps": "int64",
    "Active_Minutes": "float64",
    "Sedentary_Time_Minutes": "float64",
    "Resting_Heart_Rate": "float64",
    "Sleep_Duration": "float64",
    "Calories_Burned": "float64",
    "Average_Glucose": "float64",
    "Glucose_Variability": "float64",
    "Time_In_Range": "float64",
    "Time_Above_Range": "float64",
    "Type2_Diabetes": "int64",
    "Prediabetes": "int64",
    "Obesity": "int64",
    "Metabolic_Syndrome": "int64",
    "NAFLD": "int64",
    "Healthy": "int64",
}


# ═══════════════════════════════════════════════════════════════════════════════
# PHYSIOLOGICAL BOUNDS AND VALIDATION LIMITS
# ═══════════════════════════════════════════════════════════════════════════════

FEATURE_BOUNDS: Dict[str, Tuple[float, float]] = {
    "Age": (18.0, 80.0),
    "Average_Daily_Steps": (1000.0, 25000.0),
    "Active_Minutes": (0.0, 180.0),
    "Sedentary_Time_Minutes": (120.0, 960.0),
    "Resting_Heart_Rate": (40.0, 100.0),
    "Sleep_Duration": (4.0, 12.0),
    "Calories_Burned": (800.0, 4000.0),
    "Average_Glucose": (60.0, 250.0),
    "Glucose_Variability": (5.0, 50.0),
    "Time_In_Range": (0.0, 100.0),
    "Time_Above_Range": (0.0, 100.0),
}

# Maximum allowed total daily time in minutes (24 hours = 1440 min)
DAILY_TIME_BUDGET_MINUTES: float = 1440.0

# Critical correlation direction expectations for dataset-wide validation
EXPECTED_CORRELATIONS: Dict[Tuple[str, str], str] = {
    ("Average_Daily_Steps", "Sedentary_Time_Minutes"): "negative",
    ("Average_Daily_Steps", "Active_Minutes"): "positive",
    ("Average_Daily_Steps", "Calories_Burned"): "positive",
    ("Average_Glucose", "Time_In_Range"): "negative",
    ("Average_Glucose", "Time_Above_Range"): "positive",
    ("Average_Glucose", "Glucose_Variability"): "positive",
    ("Resting_Heart_Rate", "Average_Daily_Steps"): "negative",
}
