#!/usr/bin/env python3
"""Helpers for running the lightweight data-quality checks alongside ETL runs."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from data_quality.monitoring import (
    run_data_quality_checks,
    validate_screening_dataframe,
)


def ensure_dataframe_quality(df: pd.DataFrame) -> pd.DataFrame:
    """Validate an in-memory dataframe produced by an ETL step."""

    return validate_screening_dataframe(df)


def run_post_etl_quality_check(
    data_path: str | Path = "data/latest_screening.csv",
) -> pd.DataFrame:
    """Validate a persisted screening export."""

    return run_data_quality_checks(str(data_path))


def integrate_with_pipeline(
    curated_df: pd.DataFrame,
    *,
    output_dir: Optional[Path] = None,
) -> pd.DataFrame:
    """Example helper that validates and persists an ETL result."""

    validate_screening_dataframe(curated_df)

    output_dir = Path(output_dir) if output_dir else Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "latest_screening.csv"
    curated_df.to_csv(csv_path, index=False)

    run_post_etl_quality_check(csv_path)
    return curated_df


def test_etl_integration():
    """Quick smoke test when run as a script."""

    run_post_etl_quality_check("data/latest_screening.csv")
    print("✅ Basic ETL data quality check passed.")


if __name__ == "__main__":
    test_etl_integration()
