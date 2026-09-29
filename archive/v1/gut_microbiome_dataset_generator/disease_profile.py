"""
disease_profile.py — Latent metabolic risk score computation.

Computes a continuous metabolic risk index R ∈ [0, 1] for each patient
using their clinical biomarkers and disease labels. This risk score
modulates the statistical parameters of bacterial abundance distributions
probabilistically — it is never directly converted to microbiome values.

Clinical variables are normalized to a 0–1 scale using population reference
ranges, then combined via weighted average. Disease labels provide additive
risk adjustments. Gaussian noise is injected to maintain biological
variability and prevent deterministic mapping.
"""

import logging
from typing import Dict

import numpy as np
import pandas as pd

from . import constants
from .config import GutMicrobiomeConfig

logger = logging.getLogger("gut_microbiome_generator")


def compute_metabolic_risk_scores(
    clinical_context: pd.DataFrame,
    disease_labels: pd.DataFrame,
    rng: np.random.Generator,
    config: GutMicrobiomeConfig,
) -> np.ndarray:
    """Compute latent metabolic risk score for all patients (vectorized).

    The risk score integrates normalized clinical biomarkers and disease
    labels into a single continuous metric. Higher values indicate greater
    metabolic dysregulation and will shift microbiome distributions toward
    dysbiotic profiles.

    Pipeline:
        1. Normalize each clinical variable to [0, 1] using reference ranges.
        2. Compute weighted average of normalized variables.
        3. Add family history risk component.
        4. Add disease label risk boost.
        5. Inject Gaussian noise for biological variability.
        6. Clip final score to [0, 1].

    Args:
        clinical_context: DataFrame of clinical biomarkers (may have NaN).
        disease_labels: DataFrame of disease label columns.
        rng: NumPy random Generator.
        config: Generator configuration.

    Returns:
        Array of risk scores, shape (n_patients,), values in [0, 1].
    """
    n_patients = len(clinical_context)
    risk_components: Dict[str, np.ndarray] = {}

    # Step 1: Normalize continuous clinical variables
    for variable, (ref_low, ref_high) in constants.CLINICAL_NORM_RANGES.items():
        if variable not in clinical_context.columns:
            continue

        values = clinical_context[variable].values.astype(float)

        if ref_low < ref_high:
            # Standard normalization: higher value = higher risk
            normalized = (values - ref_low) / (ref_high - ref_low)
        else:
            # Inverted normalization (e.g., HDL: lower = higher risk)
            normalized = (ref_low - values) / (ref_low - ref_high)

        # Handle NaN: impute with 0.3 (slightly below-average risk)
        normalized = np.where(np.isnan(normalized), 0.3, normalized)
        normalized = np.clip(normalized, 0.0, 1.0)

        risk_components[variable] = normalized

    # Step 2: Compute weighted clinical risk
    clinical_risk = np.zeros(n_patients)
    total_weight = 0.0

    for variable, weight in constants.CLINICAL_RISK_WEIGHTS.items():
        if variable == "Family_History":
            continue  # Handled separately
        if variable in risk_components:
            clinical_risk += weight * risk_components[variable]
            total_weight += weight

    if total_weight > 0:
        clinical_risk /= total_weight

    # Step 3: Add family history risk component
    family_history_score = _compute_family_history_score(clinical_context)
    family_weight = constants.CLINICAL_RISK_WEIGHTS.get("Family_History", 0.06)
    clinical_risk = (
        clinical_risk * (1.0 - family_weight) +
        family_history_score * family_weight
    )

    # Step 4: Add disease label risk boost
    disease_boost = _compute_disease_risk_boost(disease_labels)
    combined_risk = clinical_risk * 0.65 + disease_boost * 0.35

    # Step 5: Inject Gaussian noise for biological variability
    noise = rng.normal(0.0, config.risk_score_noise_std, size=n_patients)
    combined_risk += noise

    # Step 6: Clip to [0, 1]
    combined_risk = np.clip(combined_risk, 0.0, 1.0)

    logger.info(
        "Metabolic risk scores: mean=%.3f, std=%.3f, min=%.3f, max=%.3f",
        np.mean(combined_risk),
        np.std(combined_risk),
        np.min(combined_risk),
        np.max(combined_risk),
    )

    return combined_risk


def _compute_family_history_score(
    clinical_context: pd.DataFrame,
) -> np.ndarray:
    """Compute family history risk component.

    Combines family history flags into a normalized 0–1 score.

    Args:
        clinical_context: Clinical context DataFrame.

    Returns:
        Array of family history scores in [0, 1].
    """
    n = len(clinical_context)
    fh_columns = [
        "Family_History_Diabetes",
        "Family_History_Obesity",
        "Family_History_Hypertension",
        "Family_History_NAFLD",
    ]

    available = [c for c in fh_columns if c in clinical_context.columns]
    if not available:
        return np.zeros(n)

    fh_values = clinical_context[available].apply(
        pd.to_numeric, errors="coerce"
    ).fillna(0).values

    # Weighted: diabetes history is most impactful
    weights = {
        "Family_History_Diabetes": 0.40,
        "Family_History_Obesity": 0.25,
        "Family_History_Hypertension": 0.20,
        "Family_History_NAFLD": 0.15,
    }

    score = np.zeros(n)
    for i, col in enumerate(available):
        score += fh_values[:, i] * weights.get(col, 0.25)

    return np.clip(score, 0.0, 1.0)


def _compute_disease_risk_boost(
    disease_labels: pd.DataFrame,
) -> np.ndarray:
    """Compute additive disease risk boost from disease labels.

    Patients with active diseases receive a risk boost proportional to
    the number and severity of conditions.

    Args:
        disease_labels: DataFrame with disease label columns.

    Returns:
        Array of disease-derived risk boost in [0, 1].
    """
    n = len(disease_labels)

    # Disease severity weights (some diseases indicate higher metabolic risk)
    severity_weights = {
        "Type2_Diabetes":     0.35,
        "Metabolic_Syndrome": 0.25,
        "NAFLD":              0.20,
        "Obesity":            0.15,
        "Prediabetes":        0.10,
    }

    boost = np.zeros(n)
    for disease, weight in severity_weights.items():
        if disease in disease_labels.columns:
            vals = pd.to_numeric(
                disease_labels[disease], errors="coerce"
            ).fillna(0).values
            boost += vals * weight

    # Healthy patients get a negative boost (toward lower risk)
    if "Healthy" in disease_labels.columns:
        healthy = pd.to_numeric(
            disease_labels["Healthy"], errors="coerce"
        ).fillna(0).values
        boost -= healthy * 0.15

    return np.clip(boost, 0.0, 1.0)


def compute_disease_shifts(
    disease_labels: pd.DataFrame,
) -> pd.DataFrame:
    """Compute per-patient disease-specific abundance shifts.

    Aggregates shift factors from all active diseases for each patient.
    When a patient has multiple diseases, shifts are summed with a
    capping mechanism to prevent extreme values.

    Args:
        disease_labels: DataFrame with disease label columns.

    Returns:
        DataFrame with columns matching ALL_BACTERIA, containing
        aggregated mean shift values per patient.
    """
    n = len(disease_labels)
    shifts = pd.DataFrame(
        np.zeros((n, len(constants.ALL_BACTERIA))),
        columns=constants.ALL_BACTERIA,
    )

    for disease, shift_dict in constants.DISEASE_SHIFT_FACTORS.items():
        if disease not in disease_labels.columns:
            continue

        active = pd.to_numeric(
            disease_labels[disease], errors="coerce"
        ).fillna(0).values.reshape(-1, 1)

        for bacterium, shift_val in shift_dict.items():
            if bacterium in shifts.columns:
                shifts[bacterium] += active.flatten() * shift_val

    # Apply cumulative cap to prevent extreme shifts in multi-disease patients
    cap = constants.MAX_CUMULATIVE_SHIFT_FACTOR
    shift_magnitude = shifts.abs().sum(axis=1)
    scale_factor = np.where(
        shift_magnitude > 0,
        np.minimum(1.0, cap * len(constants.ALL_BACTERIA) / shift_magnitude),
        1.0,
    )
    shifts = shifts.multiply(scale_factor, axis=0)

    return shifts
