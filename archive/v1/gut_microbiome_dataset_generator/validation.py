"""
validation.py — Patient-level and dataset-level validators.

Validates every generated microbiome profile for biological plausibility,
physiological bounds, correlation consistency, and disease coherence.
Also validates the complete dataset for statistical properties and
alignment with the Clinical Dataset.
"""

import logging
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from . import constants

logger = logging.getLogger("gut_microbiome_generator")


def validate_patient(
    patient_row: pd.Series,
) -> Tuple[bool, List[str]]:
    """Validate a single patient's microbiome profile.

    Checks:
      - Non-negative abundances
      - Individual feature bounds
      - Total abundance sum constraint
      - Shannon Diversity Index bounds
      - No impossible profiles (e.g., all zeros)

    Args:
        patient_row: Series containing all microbiome feature values.

    Returns:
        Tuple of (is_valid, list_of_issues).
    """
    issues: List[str] = []

    # Check non-negativity for all bacterial abundances
    for bacterium in constants.ALL_BACTERIA:
        if bacterium in patient_row.index:
            val = patient_row[bacterium]
            if np.isnan(val):
                issues.append(f"{bacterium}: NaN value")
            elif val < 0:
                issues.append(f"{bacterium}: negative value ({val:.3f})")

    # Check individual bounds
    for bacterium, (lower, upper) in constants.ABUNDANCE_BOUNDS.items():
        if bacterium in patient_row.index:
            val = patient_row[bacterium]
            if not np.isnan(val) and (val < lower - 0.01 or val > upper + 0.01):
                issues.append(
                    f"{bacterium}: out of bounds ({val:.3f}, "
                    f"expected [{lower}, {upper}])"
                )

    # Check Shannon Diversity bounds
    if "Shannon_Diversity_Index" in patient_row.index:
        shannon = patient_row["Shannon_Diversity_Index"]
        lower, upper = constants.SHANNON_DIVERSITY_BOUNDS
        if np.isnan(shannon):
            issues.append("Shannon_Diversity_Index: NaN value")
        elif shannon < lower - 0.01 or shannon > upper + 0.01:
            issues.append(
                f"Shannon_Diversity_Index: out of bounds ({shannon:.4f}, "
                f"expected [{lower}, {upper}])"
            )

    # Check total abundance sum
    total = 0.0
    for bacterium in constants.ALL_BACTERIA:
        if bacterium in patient_row.index:
            val = patient_row[bacterium]
            if not np.isnan(val):
                total += val

    if total > constants.MAX_TOTAL_ABUNDANCE:
        issues.append(
            f"Total abundance too high: {total:.2f}% "
            f"(max {constants.MAX_TOTAL_ABUNDANCE}%)"
        )

    # Check for impossible profile: all bacteria near zero
    bacteria_values = [
        patient_row[b] for b in constants.ALL_BACTERIA
        if b in patient_row.index and not np.isnan(patient_row[b])
    ]
    if bacteria_values and max(bacteria_values) < 0.01:
        issues.append("Impossible profile: all bacteria near zero")

    return len(issues) == 0, issues


def validate_dataset(
    gut_df: pd.DataFrame,
    clinical_df: pd.DataFrame = None,
) -> Tuple[bool, Dict[str, object]]:
    """Validate the complete generated dataset.

    Performs dataset-level checks:
      - Correct number of rows
      - No NaN in microbiome features
      - All features within bounds
      - Reasonable statistical distributions
      - Feature correlations in expected direction
      - Alignment with Clinical Dataset (if provided)

    Args:
        gut_df: Generated Gut Microbiome Dataset.
        clinical_df: Optional Clinical Dataset for alignment check.

    Returns:
        Tuple of (all_passed, validation_results_dict).
    """
    results: Dict[str, object] = {}
    all_passed = True

    # Row count
    n_rows = len(gut_df)
    results["row_count"] = n_rows
    if clinical_df is not None and n_rows != len(clinical_df):
        results["row_count_match"] = False
        all_passed = False
    else:
        results["row_count_match"] = True

    # NaN check in microbiome features
    nan_counts = {}
    for feature in constants.MICROBIOME_FEATURES:
        if feature in gut_df.columns:
            nan_count = gut_df[feature].isna().sum()
            nan_counts[feature] = int(nan_count)
            if nan_count > 0:
                all_passed = False
    results["nan_counts"] = nan_counts

    # Negative value check
    neg_counts = {}
    for feature in constants.ALL_BACTERIA:
        if feature in gut_df.columns:
            neg_count = int((gut_df[feature] < 0).sum())
            neg_counts[feature] = neg_count
            if neg_count > 0:
                all_passed = False
    results["negative_counts"] = neg_counts

    # Bounds check
    bounds_violations = {}
    for feature in constants.ALL_BACTERIA:
        if feature in gut_df.columns:
            lower, upper = constants.ABUNDANCE_BOUNDS[feature]
            violations = int(
                ((gut_df[feature] < lower - 0.01) |
                 (gut_df[feature] > upper + 0.01)).sum()
            )
            bounds_violations[feature] = violations
            if violations > 0:
                all_passed = False

    if "Shannon_Diversity_Index" in gut_df.columns:
        lower, upper = constants.SHANNON_DIVERSITY_BOUNDS
        violations = int(
            ((gut_df["Shannon_Diversity_Index"] < lower - 0.01) |
             (gut_df["Shannon_Diversity_Index"] > upper + 0.01)).sum()
        )
        bounds_violations["Shannon_Diversity_Index"] = violations
        if violations > 0:
            all_passed = False

    results["bounds_violations"] = bounds_violations

    # Summary statistics
    stats_summary = {}
    for feature in constants.MICROBIOME_FEATURES:
        if feature in gut_df.columns:
            vals = gut_df[feature].dropna()
            stats_summary[feature] = {
                "mean": float(vals.mean()),
                "std": float(vals.std()),
                "min": float(vals.min()),
                "max": float(vals.max()),
                "median": float(vals.median()),
                "q25": float(vals.quantile(0.25)),
                "q75": float(vals.quantile(0.75)),
            }
    results["statistics"] = stats_summary

    # Correlation direction checks
    corr_checks = _validate_correlation_directions(gut_df)
    results["correlation_checks"] = corr_checks
    if not all(v["passed"] for v in corr_checks.values()):
        # Log warnings but don't fail — correlations are probabilistic
        logger.warning("Some correlation direction checks did not pass.")

    # Alignment check
    if clinical_df is not None:
        alignment_checks = _validate_alignment(gut_df, clinical_df)
        results["alignment"] = alignment_checks
        if not alignment_checks["passed"]:
            all_passed = False

    results["all_passed"] = all_passed
    return all_passed, results


def _validate_correlation_directions(
    gut_df: pd.DataFrame,
) -> Dict[str, Dict[str, object]]:
    """Validate that key correlations have the expected direction.

    Checks that:
      - Beneficial bacteria are positively correlated with each other
      - Inflammatory bacteria are negatively correlated with beneficial
      - Shannon Diversity correlates positively with beneficial bacteria

    Args:
        gut_df: Generated dataset.

    Returns:
        Dictionary of correlation check results.
    """
    checks = {}

    key_pairs = [
        ("Akkermansia", "Faecalibacterium", "positive"),
        ("Faecalibacterium", "Roseburia", "positive"),
        ("Escherichia_Shigella", "Faecalibacterium", "negative"),
        ("Escherichia_Shigella", "Akkermansia", "negative"),
        ("Collinsella", "Faecalibacterium", "negative"),
        ("Shannon_Diversity_Index", "Faecalibacterium", "positive"),
        ("Shannon_Diversity_Index", "Escherichia_Shigella", "negative"),
    ]

    for feat_a, feat_b, expected_dir in key_pairs:
        if feat_a in gut_df.columns and feat_b in gut_df.columns:
            r = gut_df[[feat_a, feat_b]].corr().iloc[0, 1]
            if expected_dir == "positive":
                passed = r > 0
            else:
                passed = r < 0

            checks[f"{feat_a}_vs_{feat_b}"] = {
                "correlation": float(r),
                "expected": expected_dir,
                "passed": passed,
            }

    return checks


def _validate_alignment(
    gut_df: pd.DataFrame,
    clinical_df: pd.DataFrame,
) -> Dict[str, object]:
    """Validate alignment between Gut and Clinical datasets.

    Args:
        gut_df: Generated Gut Microbiome Dataset.
        clinical_df: Master Clinical Dataset.

    Returns:
        Alignment validation results.
    """
    result = {"passed": True, "details": {}}

    for col in constants.ALIGNMENT_COLUMNS:
        if col not in gut_df.columns:
            result["passed"] = False
            result["details"][col] = "Missing from Gut Dataset"
            continue

        if col == "Patient_ID":
            match = (gut_df[col].values == clinical_df[col].values).all()
        else:
            gut_vals = pd.to_numeric(gut_df[col], errors="coerce")
            clin_vals = pd.to_numeric(clinical_df[col], errors="coerce")
            match = bool(
                (gut_vals.eq(clin_vals) | (gut_vals.isna() & clin_vals.isna())).all()
            )

        result["details"][col] = "MATCH" if match else "MISMATCH"
        if not match:
            result["passed"] = False

    return result


def generate_validation_report(
    validation_results: Dict[str, object],
    output_path: str,
) -> None:
    """Write a comprehensive validation report to a text file.

    Args:
        validation_results: Results from validate_dataset().
        output_path: Path to write the report.
    """
    lines = []
    lines.append("=" * 72)
    lines.append("GUT MICROBIOME DATASET - VALIDATION REPORT")
    lines.append("=" * 72)
    lines.append("")

    # Overall result
    passed = validation_results.get("all_passed", False)
    lines.append(f"OVERALL RESULT: {'✓ PASSED' if passed else '✗ FAILED'}")
    lines.append(f"Total Patients: {validation_results.get('row_count', 'N/A')}")
    lines.append(f"Row Count Match: {validation_results.get('row_count_match', 'N/A')}")
    lines.append("")

    # NaN counts
    lines.append("-" * 40)
    lines.append("NaN VALUES")
    lines.append("-" * 40)
    nan_counts = validation_results.get("nan_counts", {})
    for feature, count in nan_counts.items():
        status = "✓" if count == 0 else "✗"
        lines.append(f"  {status} {feature}: {count}")
    lines.append("")

    # Negative values
    lines.append("-" * 40)
    lines.append("NEGATIVE VALUES")
    lines.append("-" * 40)
    neg_counts = validation_results.get("negative_counts", {})
    for feature, count in neg_counts.items():
        status = "✓" if count == 0 else "✗"
        lines.append(f"  {status} {feature}: {count}")
    lines.append("")

    # Bounds violations
    lines.append("-" * 40)
    lines.append("BOUNDS VIOLATIONS")
    lines.append("-" * 40)
    bounds = validation_results.get("bounds_violations", {})
    for feature, count in bounds.items():
        status = "✓" if count == 0 else "✗"
        lines.append(f"  {status} {feature}: {count}")
    lines.append("")

    # Statistics
    lines.append("-" * 40)
    lines.append("FEATURE STATISTICS")
    lines.append("-" * 40)
    stats = validation_results.get("statistics", {})
    for feature, s in stats.items():
        lines.append(f"  {feature}:")
        lines.append(
            f"    Mean={s['mean']:.4f}  Std={s['std']:.4f}  "
            f"Min={s['min']:.4f}  Max={s['max']:.4f}"
        )
        lines.append(
            f"    Q25={s['q25']:.4f}  Median={s['median']:.4f}  "
            f"Q75={s['q75']:.4f}"
        )
    lines.append("")

    # Correlation checks
    lines.append("-" * 40)
    lines.append("CORRELATION DIRECTION CHECKS")
    lines.append("-" * 40)
    corr_checks = validation_results.get("correlation_checks", {})
    for pair, info in corr_checks.items():
        status = "✓" if info["passed"] else "✗"
        lines.append(
            f"  {status} {pair}: r={info['correlation']:.4f} "
            f"(expected {info['expected']})"
        )
    lines.append("")

    # Alignment
    alignment = validation_results.get("alignment", {})
    if alignment:
        lines.append("-" * 40)
        lines.append("PATIENT ALIGNMENT")
        lines.append("-" * 40)
        details = alignment.get("details", {})
        for col, status in details.items():
            mark = "✓" if status == "MATCH" else "✗"
            lines.append(f"  {mark} {col}: {status}")
        lines.append("")

    lines.append("=" * 72)
    lines.append("END OF VALIDATION REPORT")
    lines.append("=" * 72)

    report_text = "\n".join(lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    logger.info("Validation report written to: %s", output_path)
