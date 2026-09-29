"""
correlations.py — Gaussian Copula correlation engine.

Enforces realistic inter-feature correlations among the 10 microbiome
features using a Cholesky decomposition-based approach. The target
correlation structure is defined in constants.TARGET_CORRELATIONS.

The engine works by:
  1. Building a 10x10 target correlation matrix from pairwise targets.
  2. Converting generated features to uniform marginals (rank-based).
  3. Transforming to standard normal space.
  4. Applying the target correlation via Cholesky decomposition.
  5. Transforming back to original marginal distributions.

This preserves each feature's marginal distribution while inducing
the desired correlation structure.
"""

import logging
from typing import List

import numpy as np
import pandas as pd
from scipy import stats

from . import constants

logger = logging.getLogger("gut_microbiome_generator")


def build_target_correlation_matrix(
    feature_names: List[str],
) -> np.ndarray:
    """Build the target correlation matrix from pairwise specifications.

    Constructs a symmetric positive-definite correlation matrix from the
    target correlations defined in constants. Diagonal elements are 1.0.
    Unspecified pairs default to 0.0.

    Args:
        feature_names: Ordered list of feature names.

    Returns:
        Square correlation matrix of shape (n_features, n_features).
    """
    n = len(feature_names)
    name_to_idx = {name: i for i, name in enumerate(feature_names)}
    corr_matrix = np.eye(n)

    for feat_a, feat_b, target_r in constants.TARGET_CORRELATIONS:
        if feat_a in name_to_idx and feat_b in name_to_idx:
            i, j = name_to_idx[feat_a], name_to_idx[feat_b]
            corr_matrix[i, j] = target_r
            corr_matrix[j, i] = target_r

    # Ensure positive semi-definiteness via eigenvalue correction
    corr_matrix = _nearest_positive_definite(corr_matrix)

    return corr_matrix


def apply_correlation_structure(
    data: pd.DataFrame,
    feature_names: List[str],
    target_corr: np.ndarray,
    strength: float = 0.8,
    rng: np.random.Generator = None,
) -> pd.DataFrame:
    """Apply target correlation structure to generated features.

    Uses a Gaussian Copula approach:
      1. Convert marginals to uniform via empirical CDF (rank-based).
      2. Transform to standard normal (inverse normal CDF).
      3. Apply Cholesky rotation to impose target correlations.
      4. Transform back to uniform, then to original marginals.

    The strength parameter controls interpolation between the original
    (uncorrelated) data and the fully correlated transformation.

    Args:
        data: DataFrame of generated microbiome features.
        feature_names: Ordered feature names matching target_corr.
        target_corr: Target correlation matrix.
        strength: Correlation blending strength in [0, 1].
        rng: NumPy random Generator (for tie-breaking).

    Returns:
        DataFrame with correlation structure applied.
    """
    n_samples = len(data)
    n_features = len(feature_names)

    if n_samples < 10:
        logger.warning("Too few samples for correlation engine. Skipping.")
        return data

    result = data.copy()

    # Extract feature values as matrix
    X = np.column_stack([data[f].values for f in feature_names])

    # Store original marginals for back-transformation
    original_sorted = np.sort(X, axis=0).copy()

    # Step 1: Convert to uniform marginals using ranks
    ranks = np.zeros_like(X)
    for j in range(n_features):
        # Add tiny jitter to break ties
        jitter = rng.uniform(-1e-10, 1e-10, size=n_samples) if rng else 0
        order = np.argsort(X[:, j] + jitter)
        ranks[order, j] = np.linspace(
            0.5 / n_samples, 1.0 - 0.5 / n_samples, n_samples
        )

    # Step 2: Transform to standard normal
    Z = stats.norm.ppf(ranks)
    Z = np.clip(Z, -4.0, 4.0)  # Prevent extreme values

    # Step 3: Apply Cholesky correlation
    try:
        L = np.linalg.cholesky(target_corr)
    except np.linalg.LinAlgError:
        logger.warning("Cholesky failed; using nearest PD matrix.")
        target_corr = _nearest_positive_definite(target_corr)
        L = np.linalg.cholesky(target_corr)

    # Current correlation in Z-space
    Z_current_corr = np.corrcoef(Z, rowvar=False)
    try:
        L_current = np.linalg.cholesky(Z_current_corr)
        # Decorrelate then re-correlate
        Z_white = np.linalg.solve(L_current, Z.T).T
        Z_correlated = (L @ Z_white.T).T
    except np.linalg.LinAlgError:
        # Fallback: direct rotation
        Z_correlated = (L @ Z.T).T

    # Blend with original based on strength
    Z_blended = strength * Z_correlated + (1.0 - strength) * Z

    # Step 4: Transform back to uniform
    U_correlated = stats.norm.cdf(Z_blended)
    U_correlated = np.clip(U_correlated, 0.001, 0.999)

    # Step 5: Map back to original marginals via rank matching
    for j in range(n_features):
        # Convert uniform back to indices in sorted original
        indices = np.clip(
            (U_correlated[:, j] * n_samples).astype(int),
            0, n_samples - 1,
        )
        result[feature_names[j]] = original_sorted[indices, j]

    logger.info("Correlation structure applied (strength=%.2f)", strength)

    return result


def _nearest_positive_definite(matrix: np.ndarray) -> np.ndarray:
    """Find the nearest positive-definite matrix to the input.

    Uses the Higham (2002) algorithm via eigenvalue clipping. Ensures
    all eigenvalues are > epsilon and the diagonal remains 1.0.

    Args:
        matrix: Input symmetric matrix.

    Returns:
        Nearest positive-definite correlation matrix.
    """
    n = matrix.shape[0]
    eigenvalues, eigenvectors = np.linalg.eigh(matrix)

    # Clip small/negative eigenvalues
    eigenvalues = np.maximum(eigenvalues, 1e-6)

    # Reconstruct
    result = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T

    # Normalize to correlation matrix (diagonal = 1)
    d = np.sqrt(np.diag(result))
    result = result / np.outer(d, d)

    # Enforce symmetry
    result = (result + result.T) / 2.0
    np.fill_diagonal(result, 1.0)

    return result


def compute_correlation_matrix(
    data: pd.DataFrame,
    feature_names: List[str],
) -> pd.DataFrame:
    """Compute the Pearson correlation matrix of microbiome features.

    Args:
        data: DataFrame containing microbiome feature columns.
        feature_names: List of feature column names.

    Returns:
        Correlation matrix as a DataFrame.
    """
    return data[feature_names].corr(method="pearson")
