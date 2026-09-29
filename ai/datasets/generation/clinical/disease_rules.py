"""
disease_rules.py — Assign disease labels using clinical diagnostic criteria.

Assigns six binary disease labels based exclusively on patient features:
    - Type2_Diabetes: FPG ≥ 126 OR HbA1c ≥ 6.5 (ADA criteria)
    - Prediabetes: (100 ≤ FPG ≤ 125 OR 5.7 ≤ HbA1c ≤ 6.4) AND NOT T2D
    - Obesity: BMI ≥ 30 (WHO/CDC)
    - Metabolic_Syndrome: ≥ 3 of 5 ATP III criteria
    - NAFLD: Probabilistic score from obesity, TG, ALT, T2D, age
    - Healthy: All other disease labels = 0

Disease labels are NEVER assigned randomly. They are deterministic
consequences of clinical features (except NAFLD which uses controlled
probabilistic scoring).
"""

import numpy as np
from numpy.random import Generator
from typing import Dict

from . import config


def assign_type2_diabetes(
    fpg: np.ndarray,
    hba1c: np.ndarray,
) -> np.ndarray:
    """Assign Type 2 Diabetes label using ADA diagnostic criteria.

    T2D = 1 if FPG ≥ 126 mg/dL OR HbA1c ≥ 6.5%

    Args:
        fpg: Array of fasting plasma glucose values (mg/dL).
        hba1c: Array of HbA1c values (%).

    Returns:
        Binary array (0/1) for Type 2 Diabetes.
    """
    return (
        (fpg >= config.T2D_FPG_THRESHOLD)
        | (hba1c >= config.T2D_HBA1C_THRESHOLD)
    ).astype(int)


def assign_prediabetes(
    fpg: np.ndarray,
    hba1c: np.ndarray,
    t2d_labels: np.ndarray,
) -> np.ndarray:
    """Assign Prediabetes label using ADA criteria, excluding T2D patients.

    Prediabetes = 1 if (100 ≤ FPG ≤ 125 OR 5.7 ≤ HbA1c ≤ 6.4) AND T2D = 0

    Args:
        fpg: Array of fasting plasma glucose values.
        hba1c: Array of HbA1c values.
        t2d_labels: Array of T2D labels (must already be assigned).

    Returns:
        Binary array (0/1) for Prediabetes.
    """
    fpg_range = config.PREDIABETES_FPG_RANGE
    hba1c_range = config.PREDIABETES_HBA1C_RANGE

    fpg_criterion = (fpg >= fpg_range[0]) & (fpg <= fpg_range[1])
    hba1c_criterion = (hba1c >= hba1c_range[0]) & (hba1c <= hba1c_range[1])

    return (
        (fpg_criterion | hba1c_criterion) & (t2d_labels == 0)
    ).astype(int)


def assign_obesity(bmis: np.ndarray) -> np.ndarray:
    """Assign Obesity label using WHO/CDC BMI criteria.

    Obesity = 1 if BMI ≥ 30

    Args:
        bmis: Array of BMI values.

    Returns:
        Binary array (0/1) for Obesity.
    """
    return (bmis >= config.OBESITY_BMI_THRESHOLD).astype(int)


def assign_metabolic_syndrome(
    waists: np.ndarray,
    genders: np.ndarray,
    tg: np.ndarray,
    hdl: np.ndarray,
    sbp: np.ndarray,
    dbp: np.ndarray,
    fpg: np.ndarray,
) -> np.ndarray:
    """Assign Metabolic Syndrome label using ATP III/AHA/NHLBI criteria.

    MetS = 1 if ≥ 3 of the following 5 criteria are met:
        1. Waist ≥ 102 cm (male) / 88 cm (female)
        2. Triglycerides ≥ 150 mg/dL
        3. HDL < 40 mg/dL (male) / < 50 mg/dL (female)
        4. SBP ≥ 130 mmHg OR DBP ≥ 85 mmHg
        5. Fasting glucose ≥ 100 mg/dL

    Args:
        waists: Array of waist circumference values (cm).
        genders: Array of gender strings.
        tg: Array of triglyceride values (mg/dL).
        hdl: Array of HDL cholesterol values (mg/dL).
        sbp: Array of systolic BP values (mmHg).
        dbp: Array of diastolic BP values (mmHg).
        fpg: Array of fasting glucose values (mg/dL).

    Returns:
        Binary array (0/1) for Metabolic Syndrome.
    """
    n = len(waists)

    # Criterion 1: Elevated waist circumference (gender-specific)
    male_mask = genders == "Male"
    waist_crit = np.zeros(n, dtype=int)
    waist_crit[male_mask] = (
        waists[male_mask] >= config.METS_WAIST_THRESHOLD["Male"]
    ).astype(int)
    waist_crit[~male_mask] = (
        waists[~male_mask] >= config.METS_WAIST_THRESHOLD["Female"]
    ).astype(int)

    # Criterion 2: Elevated triglycerides
    tg_crit = (tg >= config.METS_TG_THRESHOLD).astype(int)

    # Criterion 3: Low HDL (gender-specific)
    hdl_crit = np.zeros(n, dtype=int)
    hdl_crit[male_mask] = (
        hdl[male_mask] < config.METS_HDL_THRESHOLD["Male"]
    ).astype(int)
    hdl_crit[~male_mask] = (
        hdl[~male_mask] < config.METS_HDL_THRESHOLD["Female"]
    ).astype(int)

    # Criterion 4: Elevated blood pressure
    bp_crit = (
        (sbp >= config.METS_BP_SYSTOLIC_THRESHOLD)
        | (dbp >= config.METS_BP_DIASTOLIC_THRESHOLD)
    ).astype(int)

    # Criterion 5: Elevated fasting glucose
    fpg_crit = (fpg >= config.METS_FPG_THRESHOLD).astype(int)

    # Sum criteria and check ≥ 3
    total_criteria = waist_crit + tg_crit + hdl_crit + bp_crit + fpg_crit

    return (total_criteria >= config.METS_MIN_CRITERIA).astype(int)


def assign_nafld(
    bmis: np.ndarray,
    tg: np.ndarray,
    alt: np.ndarray,
    t2d_labels: np.ndarray,
    ages: np.ndarray,
    rng: Generator,
) -> np.ndarray:
    """Assign NAFLD label using probabilistic risk scoring.

    Since there is no simple blood test for NAFLD, we use a weighted
    scoring system based on clinical risk factors. The score is converted
    to a probability via a sigmoid function, then sampled.

    Risk factors and scores (from config):
        - BMI ≥ 30: +2.0 (or ≥ 28: +1.0)
        - TG ≥ 180: +1.5 (or ≥ 150: +0.8)
        - ALT > 50: +2.0 (or > 35: +1.0)
        - T2D = 1: +1.5
        - Age > 50: +0.5

    Args:
        bmis: Array of BMI values.
        tg: Array of triglyceride values.
        alt: Array of ALT values.
        t2d_labels: Array of T2D labels.
        ages: Array of patient ages.
        rng: NumPy random generator.

    Returns:
        Binary array (0/1) for NAFLD.
    """
    n = len(bmis)
    scoring = config.NAFLD_SCORING

    # Compute risk score for each patient
    score = np.zeros(n, dtype=float)

    # BMI contribution (higher score takes precedence)
    score += np.where(
        bmis >= scoring["bmi_high"]["threshold"],
        scoring["bmi_high"]["score"],
        np.where(
            bmis >= scoring["bmi_moderate"]["threshold"],
            scoring["bmi_moderate"]["score"],
            0.0,
        ),
    )

    # Triglyceride contribution
    score += np.where(
        tg >= scoring["tg_high"]["threshold"],
        scoring["tg_high"]["score"],
        np.where(
            tg >= scoring["tg_moderate"]["threshold"],
            scoring["tg_moderate"]["score"],
            0.0,
        ),
    )

    # ALT contribution
    score += np.where(
        alt > scoring["alt_high"]["threshold"],
        scoring["alt_high"]["score"],
        np.where(
            alt > scoring["alt_moderate"]["threshold"],
            scoring["alt_moderate"]["score"],
            0.0,
        ),
    )

    # Diabetes contribution
    score += t2d_labels.astype(float) * scoring["diabetes"]["score"]

    # Age contribution
    score += np.where(
        ages > scoring["age_over_50"]["threshold"],
        scoring["age_over_50"]["score"],
        0.0,
    )

    # Convert score to probability via sigmoid
    threshold = config.NAFLD_SIGMOID_THRESHOLD
    scale = config.NAFLD_SIGMOID_SCALE
    probability = 1.0 / (1.0 + np.exp(-scale * (score - threshold)))

    # Sample NAFLD label from probability
    return (rng.random(n) < probability).astype(int)


def assign_healthy(
    t2d: np.ndarray,
    prediabetes: np.ndarray,
    obesity: np.ndarray,
    mets: np.ndarray,
    nafld: np.ndarray,
) -> np.ndarray:
    """Assign Healthy label: 1 only if ALL disease labels are 0.

    Args:
        t2d: Array of T2D labels.
        prediabetes: Array of Prediabetes labels.
        obesity: Array of Obesity labels.
        mets: Array of Metabolic Syndrome labels.
        nafld: Array of NAFLD labels.

    Returns:
        Binary array (0/1) for Healthy.
    """
    any_disease = (t2d + prediabetes + obesity + mets + nafld) > 0
    return (~any_disease).astype(int)


def assign_all_disease_labels(
    data: Dict[str, np.ndarray],
    rng: Generator,
) -> Dict[str, np.ndarray]:
    """Assign all six disease labels from patient features.

    Labels are assigned in order: T2D → Prediabetes → Obesity → MetS
    → NAFLD → Healthy. This order matters because Prediabetes excludes
    T2D patients, and NAFLD uses T2D labels.

    Args:
        data: Dictionary of all patient features.
        rng: NumPy random generator (for NAFLD probabilistic assignment).

    Returns:
        Dictionary with all six disease label arrays.
    """
    # Deterministic labels from clinical criteria
    t2d = assign_type2_diabetes(
        data["Fasting_Blood_Glucose"], data["HbA1c"],
    )
    prediabetes = assign_prediabetes(
        data["Fasting_Blood_Glucose"], data["HbA1c"], t2d,
    )
    obesity = assign_obesity(data["BMI"])

    mets = assign_metabolic_syndrome(
        data["Waist_Circumference_cm"],
        data["Gender"],
        data["Triglycerides"],
        data["HDL_Cholesterol"],
        data["Systolic_BP"],
        data["Diastolic_BP"],
        data["Fasting_Blood_Glucose"],
    )

    # Probabilistic label
    nafld = assign_nafld(
        data["BMI"],
        data["Triglycerides"],
        data["ALT"],
        t2d,
        data["Age"],
        rng,
    )

    healthy = assign_healthy(t2d, prediabetes, obesity, mets, nafld)

    return {
        "Type2_Diabetes": t2d,
        "Prediabetes": prediabetes,
        "Obesity": obesity,
        "Metabolic_Syndrome": mets,
        "NAFLD": nafld,
        "Healthy": healthy,
    }
