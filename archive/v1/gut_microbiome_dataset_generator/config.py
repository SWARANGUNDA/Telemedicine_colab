"""
config.py — Configuration dataclasses for the Gut Microbiome Dataset Generator.

Centralizes all configurable runtime parameters including file paths, random
seed, noise levels, and generation toggles. No generation constants are
hardcoded in downstream modules.
"""

from dataclasses import dataclass


@dataclass
class GutMicrobiomeConfig:
    """Top-level configuration for the Gut Microbiome Dataset Generator.

    Attributes:
        clinical_dataset_path: Path to the master Clinical_Dataset.csv.
        output_dir: Directory for output files.
        seed: Master random seed for reproducibility.
        output_file: Name of the output CSV.
        max_regeneration_attempts: Maximum retries for patients failing validation.
        enable_noise: Whether to inject post-generation Gaussian noise.
        noise_scale: Global noise amplitude multiplier (1.0 = standard).
        correlation_strength: Scaling factor for correlation engine (0.0-1.0).
        risk_score_noise_std: Standard deviation of noise added to latent risk score.
        abundance_decimal_places: Rounding precision for relative abundance values.
        diversity_decimal_places: Rounding precision for Shannon Diversity Index.
    """

    clinical_dataset_path: str = "Clinical_Dataset.csv"
    output_dir: str = "."
    seed: int = 42
    output_file: str = "Gut_Microbiome_Dataset.csv"
    max_regeneration_attempts: int = 10
    enable_noise: bool = True
    noise_scale: float = 1.0
    correlation_strength: float = 0.8
    risk_score_noise_std: float = 0.08
    abundance_decimal_places: int = 2
    diversity_decimal_places: int = 4
