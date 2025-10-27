#!/usr/bin/env python3
"""Simple data quality checks for the generated screening dataset."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

REQUIRED_COLUMNS: Iterable[str] = (
    "magic_formula_rank",
    "ticker",
    "company_name",
    "sector",
    "earnings_yield",
    "roc",
    "f_score",
    "market_cap",
    "enterprise_value",
    "ebit",
    "last_updated",
)

STRING_COLUMNS = ("ticker", "company_name", "sector")

NUMERIC_RANGE_CHECKS = {
    "earnings_yield": (-1.0, 2.0),
    "roc": (-1.0, 10.0),
    "f_score": (0, 9),
}

POSITIVE_VALUE_COLUMNS = ("market_cap", "enterprise_value")
INTEGER_COLUMNS = ("magic_formula_rank",)


def _ensure_numeric(series: pd.Series, column: str) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.isna().any():
        raise ValueError(f"Column '{column}' contains missing or non-numeric values")
    return numeric


def validate_screening_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Validate the in-memory screening dataframe.

    Raises ``ValueError`` when required conditions are not met and returns the
    original dataframe when all checks pass.
    """

    if df is None or df.empty:
        raise ValueError("Screening dataset is empty")

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            "Screening dataset is missing required columns: " + ", ".join(missing)
        )

    for column in STRING_COLUMNS:
        if df[column].isna().any():
            raise ValueError(f"Column '{column}' contains null values")
        if (df[column].astype(str).str.strip() == "").any():
            raise ValueError(f"Column '{column}' contains blank values")

    for column, (min_value, max_value) in NUMERIC_RANGE_CHECKS.items():
        numeric = _ensure_numeric(df[column], column)
        if (numeric < min_value).any():
            raise ValueError(
                f"Column '{column}' has values below the minimum of {min_value}"
            )
        if (numeric > max_value).any():
            raise ValueError(
                f"Column '{column}' has values above the maximum of {max_value}"
            )

    for column in POSITIVE_VALUE_COLUMNS:
        numeric = _ensure_numeric(df[column], column)
        if (numeric <= 0).any():
            raise ValueError(f"Column '{column}' must contain positive values")

    for column in INTEGER_COLUMNS:
        numeric = _ensure_numeric(df[column], column)
        if (numeric <= 0).any():
            raise ValueError(f"Column '{column}' must contain positive integers")
        if not (numeric % 1 == 0).all():
            raise ValueError(f"Column '{column}' must contain whole numbers")

    return df


def run_data_quality_checks(data_path: str = "data/latest_screening.csv") -> pd.DataFrame:
    """Load the latest screening export and ensure it meets quality expectations."""

    csv_path = Path(data_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    df = pd.read_csv(csv_path)
    validate_screening_dataframe(df)

    print(f"✅ Data quality checks passed for {csv_path} ({len(df)} rows)")
    return df


if __name__ == "__main__":
    run_data_quality_checks()
