"""
exporter.py — CSV and report file exporters.

Exports the final Gut Microbiome Dataset and generates all required
auxiliary output files:
  - Gut_Microbiome_Dataset.csv
  - dataset_summary.csv
  - feature_distribution_report.txt
  - correlation_matrix.csv
  - validation_report.txt (via validation module)
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from . import constants
from .correlations import compute_correlation_matrix

logger = logging.getLogger("gut_microbiome_generator")


def export_dataset(
    gut_df: pd.DataFrame,
    output_path: str,
    decimal_places_abundance: int = 2,
    decimal_places_diversity: int = 4,
) -> None:
    """Export the final Gut Microbiome Dataset to CSV.

    Rounds abundance values and Shannon Diversity to specified precision.
    Column order follows constants.OUTPUT_COLUMNS.

    Args:
        gut_df: Complete Gut Microbiome Dataset.
        output_path: Path for the output CSV file.
        decimal_places_abundance: Decimal places for bacterial abundances.
        decimal_places_diversity: Decimal places for Shannon Diversity.
    """
    df = gut_df.copy()

    # Round microbiome features
    for feature in constants.ALL_BACTERIA:
        if feature in df.columns:
            df[feature] = df[feature].round(decimal_places_abundance)

    if "Shannon_Diversity_Index" in df.columns:
        df["Shannon_Diversity_Index"] = df["Shannon_Diversity_Index"].round(
            decimal_places_diversity
        )

    # Ensure column order
    available_cols = [c for c in constants.OUTPUT_COLUMNS if c in df.columns]
    df = df[available_cols]

    df.to_csv(output_path, index=False)
    logger.info(
        "Dataset exported: %s (%d patients, %d columns)",
        output_path, len(df), len(df.columns),
    )


def export_summary_statistics(
    gut_df: pd.DataFrame,
    output_path: str,
) -> None:
    """Export summary statistics for all microbiome features.

    Generates a CSV with mean, std, min, 25%, 50%, 75%, max, skewness,
    and kurtosis for each microbiome feature.

    Args:
        gut_df: Complete Gut Microbiome Dataset.
        output_path: Path for the output CSV.
    """
    features = [f for f in constants.MICROBIOME_FEATURES if f in gut_df.columns]
    records = []

    for feature in features:
        vals = gut_df[feature].dropna()
        records.append({
            "Feature": feature,
            "Mean": round(float(vals.mean()), 4),
            "Std": round(float(vals.std()), 4),
            "Min": round(float(vals.min()), 4),
            "Q25": round(float(vals.quantile(0.25)), 4),
            "Median": round(float(vals.quantile(0.50)), 4),
            "Q75": round(float(vals.quantile(0.75)), 4),
            "Max": round(float(vals.max()), 4),
            "Skewness": round(float(vals.skew()), 4),
            "Kurtosis": round(float(vals.kurtosis()), 4),
        })

    summary_df = pd.DataFrame(records)
    summary_df.to_csv(output_path, index=False)
    logger.info("Summary statistics exported: %s", output_path)


def export_feature_distribution_report(
    gut_df: pd.DataFrame,
    output_path: str,
) -> None:
    """Export a detailed feature distribution report as plain text.

    Includes per-feature statistics, normality test results, and
    disease-group comparisons.

    Args:
        gut_df: Complete Gut Microbiome Dataset.
        output_path: Path for the output text file.
    """
    lines = []
    lines.append("=" * 72)
    lines.append("GUT MICROBIOME DATASET - FEATURE DISTRIBUTION REPORT")
    lines.append("=" * 72)
    lines.append(f"Total Patients: {len(gut_df)}")
    lines.append("")

    # Per-feature analysis
    for feature in constants.MICROBIOME_FEATURES:
        if feature not in gut_df.columns:
            continue

        vals = gut_df[feature].dropna()
        lines.append("-" * 50)
        lines.append(f"Feature: {feature}")
        lines.append("-" * 50)
        lines.append(f"  Mean:     {vals.mean():.4f}")
        lines.append(f"  Std:      {vals.std():.4f}")
        lines.append(f"  Min:      {vals.min():.4f}")
        lines.append(f"  Max:      {vals.max():.4f}")
        lines.append(f"  Median:   {vals.median():.4f}")
        lines.append(f"  Skewness: {vals.skew():.4f}")
        lines.append(f"  Kurtosis: {vals.kurtosis():.4f}")

        # Shapiro-Wilk normality test (subsample for large datasets)
        sample_size = min(5000, len(vals))
        subsample = vals.sample(n=sample_size, random_state=42)
        try:
            _, p_value = stats.shapiro(subsample)
            normality = "Normal" if p_value > 0.05 else "Non-Normal"
            lines.append(f"  Normality: {normality} (p={p_value:.4e})")
        except Exception:
            lines.append("  Normality: Could not compute")

        # Disease group comparison
        lines.append("")
        lines.append("  Disease Group Means:")

        if "Healthy" in gut_df.columns:
            healthy_mask = gut_df["Healthy"] == 1
            healthy_mean = vals[healthy_mask].mean()
            diseased_mean = vals[~healthy_mask].mean()
            n_diseased = int((~healthy_mask).sum())
            lines.append(f"    Healthy:  {healthy_mean:.4f} (n={healthy_mask.sum()})")
            lines.append(f"    Diseased: {diseased_mean:.4f} (n={n_diseased})")

        for disease in ["Type2_Diabetes", "Obesity", "NAFLD"]:
            if disease in gut_df.columns:
                mask = gut_df[disease] == 1
                if mask.sum() > 0:
                    disease_mean = vals[mask].mean()
                    lines.append(f"    {disease}: {disease_mean:.4f} (n={mask.sum()})")

        lines.append("")

    # Disease prevalence summary
    lines.append("=" * 50)
    lines.append("DISEASE PREVALENCE")
    lines.append("=" * 50)
    for disease in constants.DISEASE_LABEL_COLUMNS:
        if disease in gut_df.columns:
            count = int(gut_df[disease].sum())
            pct = count / len(gut_df) * 100
            lines.append(f"  {disease}: {count} ({pct:.1f}%)")
    lines.append("")

    lines.append("=" * 72)
    lines.append("END OF DISTRIBUTION REPORT")
    lines.append("=" * 72)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("Feature distribution report exported: %s", output_path)


def export_correlation_matrix(
    gut_df: pd.DataFrame,
    output_path: str,
) -> None:
    """Export the pairwise correlation matrix for microbiome features.

    Args:
        gut_df: Complete Gut Microbiome Dataset.
        output_path: Path for the output CSV.
    """
    features = [f for f in constants.MICROBIOME_FEATURES if f in gut_df.columns]
    corr_df = compute_correlation_matrix(gut_df, features)
    corr_df = corr_df.round(4)
    corr_df.to_csv(output_path)
    logger.info("Correlation matrix exported: %s", output_path)
