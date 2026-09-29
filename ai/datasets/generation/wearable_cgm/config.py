"""
config.py — Centralized configuration dataclasses and parameters.

Centralizes all configurable generation parameters, noise levels, regression
coefficients, and physiological thresholds for the synthetic wearable generator.
No constants are hardcoded in downstream calculation modules.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple, List


@dataclass
class WearableDatasetConfig:
    """Top-level configuration parameters for the Wearable Dataset Generator."""

    clinical_dataset_path: str = "Clinical_Dataset.csv"
    seed: int = 42
    output_file: str = "Wearable_Dataset.csv"
    demo_mode: bool = False
    demo_size: int = 100
    max_regeneration_attempts: int = 5
    
    # Stochastic noise and missingness toggles
    enable_noise: bool = True
    noise_scale: float = 1.0
    enable_missingness: bool = False
    missing_rate_default: float = 0.02
    enable_outliers: bool = True
    outlier_fraction: float = 0.015


# ═══════════════════════════════════════════════════════════════════════════════
# PHYSIOLOGICAL REGRESSION & GENERATION COEFFICIENTS
# Conditioning wearable metrics on continuous clinical biomarkers
# ═══════════════════════════════════════════════════════════════════════════════

# Activity Parameters (Steps, Active Minutes, Sedentary Time)
STEPS_BASE_MEAN: float = 8500.0
STEPS_BMI_SLOPE: float = -180.0     # Steps reduction per BMI unit above 22
STEPS_AGE_SLOPE: float = -45.0      # Steps reduction per year above 30
STEPS_MIN: float = 1000.0
STEPS_MAX: float = 25000.0
STEPS_NOISE_STD: float = 1200.0

ACTIVE_MINUTES_STEP_SLOPE: float = 0.0032  # MVPA min per daily step
ACTIVE_MINUTES_BMI_SLOPE: float = -0.35    # MVPA min reduction per BMI unit above 25
ACTIVE_MINUTES_MIN: float = 0.0
ACTIVE_MINUTES_MAX: float = 180.0
ACTIVE_MINUTES_NOISE_STD: float = 4.5

SEDENTARY_BASE: float = 480.0               # Base sedentary time in minutes (8 hours)
SEDENTARY_BMI_SLOPE: float = 6.5           # Additional sedentary min per BMI unit above 25
SEDENTARY_STEPS_SLOPE: float = -0.018      # Sedentary min reduction per 1000 steps
SEDENTARY_MIN: float = 120.0
SEDENTARY_MAX: float = 960.0
SEDENTARY_NOISE_STD: float = 25.0

# Cardiovascular Parameters (Resting Heart Rate)
RHR_BASE_MEAN: float = 68.0                # Base resting HR for active fit individual
RHR_BMI_SLOPE: float = 0.45                # RHR increase per BMI unit above 22.5
RHR_BP_SLOPE: float = 0.12                 # RHR increase per SBP mmHg above 110
RHR_STEPS_SLOPE: float = -0.0008           # RHR decrease per step/day
RHR_MIN: float = 40.0
RHR_MAX: float = 100.0
RHR_NOISE_STD: float = 3.5

# Sleep Parameters (Sleep Duration)
SLEEP_BASE_MEAN: float = 7.50              # Baseline sleep hours
SLEEP_AGE_SLOPE: float = -0.010            # Sleep reduction per year above 40
SLEEP_BMI_SLOPE: float = -0.025            # Sleep reduction per BMI unit above 25
SLEEP_MIN: float = 4.0
SLEEP_MAX: float = 12.0
SLEEP_NOISE_STD: float = 0.75

# Energy Expenditure Parameters (Calories Burned)
CALORIES_BMR_MALE: float = 1650.0          # Average male basal metabolic rate
CALORIES_BMR_FEMALE: float = 1350.0        # Average female basal metabolic rate
CALORIES_WEIGHT_SLOPE: float = 8.0         # kcal per kg weight
CALORIES_STEPS_SLOPE: float = 0.040        # kcal per step
CALORIES_ACTIVE_MIN_SLOPE: float = 0.100   # kcal per active minute
CALORIES_MIN: float = 800.0
CALORIES_MAX: float = 4000.0
CALORIES_NOISE_STD: float = 45.0

# Continuous Glucose Monitoring (CGM) Parameters
CGM_AVG_GLUCOSE_FPG_SLOPE: float = 0.75    # CGM mean dependence on Fasting Blood Glucose
CGM_AVG_GLUCOSE_HBA1C_SLOPE: float = 12.5  # CGM mean dependence on HbA1c
CGM_AVG_GLUCOSE_OFFSET: float = -5.0
CGM_AVG_GLUCOSE_MIN: float = 60.0
CGM_AVG_GLUCOSE_MAX: float = 250.0
CGM_AVG_GLUCOSE_NOISE_STD: float = 5.0

# Glucose Variability (SD of glucose)
CGM_GV_BASE_CV: float = 0.12               # Coefficient of variation (12% for normal)
CGM_GV_HIGH_GLUCOSE_BOOST: float = 0.0012  # Additional CV per mg/dL above 100
CGM_GV_MIN: float = 5.0
CGM_GV_MAX: float = 50.0
CGM_GV_NOISE_STD: float = 1.2

# Time In Range (TIR: 70–180 mg/dL) & Time Above Range (TAR: >180 mg/dL)
# Sigmoid models for TIR as a function of Average_Glucose
TIR_SIGMOID_MIDPOINT: float = 130.0        # Avg Glucose where TIR is ~50%
TIR_SIGMOID_K: float = 0.065              # Steepness of TIR drop
TIR_MIN: float = 0.0
TIR_MAX: float = 100.0

# Hypoglycemia (Time Below Range <70 mg/dL)
TBR_BASE_MEAN: float = 1.5                # Baseline % time below 70 mg/dL
TBR_DIABETIC_MAX: float = 8.0             # Max % for T2D/medicated patients


# ═══════════════════════════════════════════════════════════════════════════════
# MEASUREMENT NOISE SPECIFICATIONS
# Standard deviations for Gaussian measurement noise injection
# ═══════════════════════════════════════════════════════════════════════════════

NOISE_SPEC: Dict[str, Dict[str, float]] = {
    "Average_Daily_Steps":     {"std": 250.0, "max": 600.0},
    "Active_Minutes":          {"std": 1.5,   "max": 4.0},
    "Sedentary_Time_Minutes":  {"std": 8.0,   "max": 20.0},
    "Resting_Heart_Rate":      {"std": 1.0,   "max": 3.0},
    "Sleep_Duration":          {"std": 0.15,  "max": 0.4},
    "Calories_Burned":         {"std": 20.0,  "max": 50.0},
    "Average_Glucose":         {"std": 2.0,   "max": 5.0},
    "Glucose_Variability":     {"std": 0.5,   "max": 1.5},
    "Time_In_Range":           {"std": 1.0,   "max": 3.0},
    "Time_Above_Range":        {"std": 1.0,   "max": 3.0},
}
