"""Helpers for working with the curated local fundamentals dataset."""
from __future__ import annotations

"""Utilities for turning the curated fundamentals CSV into screening outputs."""

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, Tuple, Optional

import pandas as pd

from etl.compute import (
    compute_overall_quality_score,
    compute_value_trap_avoidance_score,
)
from etl.fetch import load_curated_fundamentals

CURATED_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "curated_fundamentals.csv"


def _compute_price_strength(momentum: float) -> int:
    """Derive a simple price strength score from 6M momentum."""
    if pd.isna(momentum):
        return 0
    if momentum > 0.15:
        return 3
    if momentum > 0.05:
        return 2
    if momentum > 0:
        return 1
    return 0


def prepare_screening_dataframe(
    curated_df: pd.DataFrame,
    *,
    as_of: Optional[datetime] = None,
) -> pd.DataFrame:
    """Compute Magic Formula metrics from the curated fundamentals dataset."""
    required_columns = {
        "ticker",
        "company_name",
        "sector",
        "ebit",
        "enterprise_value",
        "market_cap",
        "f_score",
        "cash_flow_quality_score",
        "sentiment_score",
        "momentum_6m",
        "debt_to_equity",
        "ocf_margin",
        "fcf_margin",
        "ocf_to_ni_ratio",
    }

    missing = sorted(required_columns - set(curated_df.columns))
    if missing:
        raise ValueError(f"Curated fundamentals dataset is missing columns: {', '.join(missing)}")

    as_of = as_of or datetime.now()

    df = curated_df.copy()

    numeric_columns = [
        "ebit",
        "enterprise_value",
        "market_cap",
        "f_score",
        "cash_flow_quality_score",
        "sentiment_score",
        "momentum_6m",
        "debt_to_equity",
        "ocf_margin",
        "fcf_margin",
        "ocf_to_ni_ratio",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["earnings_yield"] = df["ebit"] / df["enterprise_value"]
    df["roc"] = df["earnings_yield"] * 1.5

    if "price_strength_score" in df.columns:
        df["price_strength_score"] = pd.to_numeric(
            df["price_strength_score"], errors="coerce"
        ).fillna(0)
    else:
        df["price_strength_score"] = 0

    df["price_strength_score"] = df.apply(
        lambda row: int(row["price_strength_score"])
        if row["price_strength_score"] not in (0, 0.0)
        else _compute_price_strength(row["momentum_6m"]),
        axis=1,
    )

    df["overall_quality_score"] = df.apply(
        lambda row: compute_overall_quality_score(
            int(row["f_score"]),
            int(row["cash_flow_quality_score"]),
            int(row["sentiment_score"]),
        ),
        axis=1,
    )
    df["value_trap_avoidance_score"] = df.apply(
        lambda row: compute_value_trap_avoidance_score(
            float(row["momentum_6m"]),
            int(row["f_score"]),
            int(row["cash_flow_quality_score"]),
        ),
        axis=1,
    )
    df["last_updated"] = as_of.isoformat()

    df = df.sort_values(["earnings_yield", "roc"], ascending=[False, False]).reset_index(drop=True)
    df["magic_formula_rank"] = df.index + 1

    column_order: Iterable[str] = [
        "magic_formula_rank",
        "ticker",
        "company_name",
        "sector",
        "earnings_yield",
        "roc",
        "f_score",
        "debt_to_equity",
        "momentum_6m",
        "price_strength_score",
        "cash_flow_quality_score",
        "sentiment_score",
        "overall_quality_score",
        "value_trap_avoidance_score",
        "ocf_margin",
        "fcf_margin",
        "ocf_to_ni_ratio",
        "market_cap",
        "ebit",
        "enterprise_value",
        "last_updated",
    ]

    existing_columns = [col for col in column_order if col in df.columns]
    df = df[existing_columns]
    return df


def refresh_from_curated(
    *,
    curated_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Tuple[pd.DataFrame, dict]:
    """Recompute and persist the sample dataset from the curated fundamentals."""
    curated_path = Path(curated_path) if curated_path else CURATED_DATA_PATH
    curated_df = load_curated_fundamentals(curated_path)
    run_time = datetime.now()
    screening_df = prepare_screening_dataframe(curated_df, as_of=run_time)

    output_dir = Path(output_dir) if output_dir else Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "latest_screening.csv"
    json_path = output_dir / "latest_screening.json"
    metadata_path = output_dir / "metadata.json"

    screening_df.to_csv(csv_path, index=False)
    screening_df.to_json(json_path, orient="records", date_format="iso")

    metadata = {
        "run_date": run_time.isoformat(),
        "total_stocks": int(len(screening_df)),
        "data_source": str(curated_path.resolve()),
        "version": "curated-local",
    }

    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")

    return screening_df, metadata
