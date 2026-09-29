"""
glucose.py — Continuous Glucose Monitoring (CGM) feature generator.

Generates Average_Glucose, Glucose_Variability, Time_In_Range (TIR), and
Time_Above_Range (TAR) conditioned on clinical Fasting_Blood_Glucose and HbA1c.
Enforces the mathematical identity: TIR + TAR + TBR = 100%.
"""

import numpy as np
from numpy.random import Generator
from typing import Dict

from . import config


def generate_glucose_features(
    context: Dict[str, np.ndarray],
    rng: Generator,
    config_obj: config.WearableDatasetConfig = config.WearableDatasetConfig(),
) -> Dict[str, np.ndarray]:
    """Generate CGM metrics conditioned on clinical Fasting_Blood_Glucose and HbA1c.

    Args:
        context: Patient clinical context dictionary.
        rng: NumPy random generator.
        config_obj: Configuration object.

    Returns:
        Dictionary containing CGM feature arrays.
    """
    n = len(context["Patient_ID"])
    fpg = context["Fasting_Blood_Glucose"]
    hba1c = context["HbA1c"]

    # ── 1. Average Glucose (CGM Mean mg/dL) ──
    # Linear function of Fasting Glucose and HbA1c
    cgm_mean_raw = (
        config.CGM_AVG_GLUCOSE_FPG_SLOPE * fpg
        + config.CGM_AVG_GLUCOSE_HBA1C_SLOPE * hba1c
        + config.CGM_AVG_GLUCOSE_OFFSET
    )
    noise_cgm = rng.normal(
        0, config.CGM_AVG_GLUCOSE_NOISE_STD * config_obj.noise_scale, size=n
    )
    avg_glucose = np.clip(
        cgm_mean_raw + noise_cgm,
        config.CGM_AVG_GLUCOSE_MIN,
        config.CGM_AVG_GLUCOSE_MAX,
    )
    avg_glucose = np.round(avg_glucose, 1)

    # ── 2. Glucose Variability (SD of CGM in mg/dL) ──
    # Coefficient of variation (CV) increases as mean glucose climbs
    excess_glucose = np.maximum(0.0, avg_glucose - 100.0)
    cv = config.CGM_GV_BASE_CV + config.CGM_GV_HIGH_GLUCOSE_BOOST * excess_glucose
    gv_mean = avg_glucose * cv

    noise_gv = rng.normal(
        0, config.CGM_GV_NOISE_STD * config_obj.noise_scale, size=n
    )
    glucose_variability = np.clip(
        gv_mean + noise_gv,
        config.CGM_GV_MIN,
        config.CGM_GV_MAX,
    )
    glucose_variability = np.round(glucose_variability, 1)

    # ── 3. Time In Range (TIR: % time 70–180 mg/dL) ──
    # Logistic sigmoid mapping Average Glucose to TIR
    z = config.TIR_SIGMOID_K * (avg_glucose - config.TIR_SIGMOID_MIDPOINT)
    tir_mean = 100.0 / (1.0 + np.exp(z))

    noise_tir = rng.normal(
        0, config.NOISE_SPEC["Time_In_Range"]["std"] * config_obj.noise_scale, size=n
    )
    tir = np.clip(tir_mean + noise_tir, config.TIR_MIN, config.TIR_MAX)

    # ── 4. Hypoglycemia & Time Above Range (TAR: % time >180 mg/dL) ──
    # TBR (<70 mg/dL) is 0-3% for normals, slightly higher for diabetics
    is_diabetic = fpg >= 126.0
    tbr_base = np.where(is_diabetic, 2.5, 0.8)
    tbr_noise = np.abs(rng.normal(0, 0.5, size=n))
    tbr = np.clip(tbr_base + tbr_noise, 0.0, config.TBR_DIABETIC_MAX)

    # Ensure TIR + TBR <= 100%
    tir = np.minimum(tir, 100.0 - tbr)
    tar = 100.0 - tir - tbr

    # Round percentages to 1 decimal place
    tir = np.round(tir, 1)
    tar = np.round(tar, 1)

    return {
        "Average_Glucose": avg_glucose,
        "Glucose_Variability": glucose_variability,
        "Time_In_Range": tir,
        "Time_Above_Range": tar,
    }
