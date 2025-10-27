"""Local data access helpers for the Modern Magic Formula project."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Union, Dict, Any

import pandas as pd

CURATED_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "curated_fundamentals.csv"


def load_curated_fundamentals(path: Union[str, Path] = CURATED_DATA_PATH) -> pd.DataFrame:
    """Return the curated fundamentals dataset bundled with the repository."""
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Curated fundamentals file not found: {dataset_path}")
    return pd.read_csv(dataset_path)


def iter_curated_records(path: Union[str, Path] = CURATED_DATA_PATH) -> Iterable[Dict[str, Any]]:
    """Yield curated fundamentals as dictionaries."""
    df = load_curated_fundamentals(path)
    return df.to_dict(orient="records")


def _removed_fetcher(*_args: Any, **_kwargs: Any) -> None:  # pragma: no cover - guardrail
    raise RuntimeError(
        "Remote data fetch helpers have been removed. "
        "Use `load_curated_fundamentals` to work with the bundled dataset."
    )


# Legacy names kept for compatibility with older scripts.
get_alpha_vantage_fundamentals = _removed_fetcher
get_alpha_vantage_bulk_fundamentals = _removed_fetcher
get_yahoo_finance_fundamentals = _removed_fetcher
get_6_month_price_data = _removed_fetcher
get_alpha_vantage_price_data = _removed_fetcher
get_fundamentals_with_fallback = _removed_fetcher
