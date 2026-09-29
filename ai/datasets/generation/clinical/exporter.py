"""
exporter.py — Export validated dataset to CSV.

Handles:
    - Column ordering (matches specification blueprint)
    - Data type enforcement (integers, floats, strings)
    - Missing value representation (NaN → empty cell in CSV)
    - Export summary logging
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from . import config

logger = logging.getLogger(__name__)


def _enforce_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Enforce correct data types for each column.

    Integer columns with NaN are stored as float (pandas limitation);
    this is handled by using nullable integer types where possible.

    Args:
        df: Dataset DataFrame.

    Returns:
        DataFrame with enforced types.
    """
    for col, dtype_str in config.COLUMN_DTYPES.items():
        if col not in df.columns:
            continue

        if dtype_str == "int":
            # Use nullable integer to handle NaN in integer columns
            if df[col].isna().any():
                df[col] = df[col].astype("Int64")
            else:
                df[col] = df[col].astype(int)

        elif dtype_str == "float":
            df[col] = df[col].astype(float)

        elif dtype_str == "str":
            df[col] = df[col].astype(str)

    return df


def export_to_csv(
    df: pd.DataFrame,
    output_path: str,
) -> Path:
    """Export the validated dataset to a CSV file.

    Args:
        df: Validated dataset DataFrame.
        output_path: Output file path (relative or absolute).

    Returns:
        Path to the exported CSV file.

    Raises:
        ValueError: If DataFrame is empty.
        OSError: If file cannot be written.
    """
    if df.empty:
        raise ValueError("Cannot export empty DataFrame")

    output = Path(output_path)

    # Ensure output directory exists
    output.parent.mkdir(parents=True, exist_ok=True)

    # Reorder columns to match specification blueprint
    available_cols = [c for c in config.COLUMN_ORDER if c in df.columns]
    df = df[available_cols]

    # Enforce data types
    df = _enforce_dtypes(df)

    # Export to CSV
    df.to_csv(output, index=False, na_rep="")

    # Log export summary
    file_size = output.stat().st_size
    size_mb = file_size / (1024 * 1024)

    logger.info(
        f"Dataset exported to: {output.resolve()}\n"
        f"  Rows: {len(df):,}\n"
        f"  Columns: {len(df.columns)}\n"
        f"  File size: {size_mb:.2f} MB"
    )

    return output.resolve()
