"""
distributions.py — Statistical distribution samplers for microbiome features.

Provides vectorized sampling from Truncated Normal, Log-Normal, and Gamma
distributions with configurable location, scale, and bounds. All samplers
accept numpy Generator instances for reproducibility.
"""

import numpy as np
from scipy import stats


def sample_truncated_normal(
    rng: np.random.Generator,
    mean: float,
    std: float,
    lower: float,
    upper: float,
    size: int = 1,
) -> np.ndarray:
    """Sample from a truncated normal distribution.

    Uses scipy.stats.truncnorm for accurate boundary handling. Generates
    values within [lower, upper] centered on mean with given std.

    Args:
        rng: NumPy random Generator for reproducibility.
        mean: Distribution mean (location parameter).
        std: Distribution standard deviation (scale parameter).
        lower: Lower truncation bound.
        upper: Upper truncation bound.
        size: Number of samples to draw.

    Returns:
        Array of samples within [lower, upper].
    """
    if std <= 0:
        return np.full(size, mean)

    a = (lower - mean) / std
    b = (upper - mean) / std

    # Use scipy truncnorm with the provided rng
    samples = stats.truncnorm.rvs(
        a, b, loc=mean, scale=std, size=size,
        random_state=rng,
    )
    return samples


def sample_lognormal_bounded(
    rng: np.random.Generator,
    mean: float,
    std: float,
    lower: float,
    upper: float,
    size: int = 1,
) -> np.ndarray:
    """Sample from a log-normal distribution with post-hoc clipping.

    Useful for right-skewed biological data such as bacterial abundances.
    Parameters are specified in the *natural* (non-log) space for ease of
    use; internally converted to log-space mu/sigma.

    Args:
        rng: NumPy random Generator.
        mean: Desired mean in natural space (must be > 0).
        std: Desired standard deviation in natural space.
        lower: Lower bound (clip).
        upper: Upper bound (clip).
        size: Number of samples.

    Returns:
        Array of samples clipped to [lower, upper].
    """
    if mean <= 0:
        return np.full(size, lower)
    if std <= 0:
        return np.full(size, np.clip(mean, lower, upper))

    # Convert natural-space mean/std to log-space parameters
    variance = std ** 2
    mu_log = np.log(mean ** 2 / np.sqrt(variance + mean ** 2))
    sigma_log = np.sqrt(np.log(1.0 + variance / mean ** 2))

    samples = rng.lognormal(mean=mu_log, sigma=sigma_log, size=size)
    return np.clip(samples, lower, upper)


def sample_gamma_bounded(
    rng: np.random.Generator,
    mean: float,
    std: float,
    lower: float,
    upper: float,
    size: int = 1,
) -> np.ndarray:
    """Sample from a Gamma distribution with clipping.

    Suitable for strictly positive, right-skewed distributions such as
    inflammatory bacteria that are often near-zero with occasional spikes.

    Args:
        rng: NumPy random Generator.
        mean: Desired mean (shape * scale).
        std: Desired standard deviation.
        lower: Lower clipping bound.
        upper: Upper clipping bound.
        size: Number of samples.

    Returns:
        Array of samples clipped to [lower, upper].
    """
    if mean <= 0 or std <= 0:
        return np.full(size, np.clip(mean, lower, upper))

    # Gamma parameterization: shape = (mean/std)^2, scale = std^2/mean
    shape = (mean / std) ** 2
    scale = (std ** 2) / mean

    samples = rng.gamma(shape=shape, scale=scale, size=size)
    return np.clip(samples, lower, upper)
