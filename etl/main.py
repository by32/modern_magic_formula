"""CLI entry point for refreshing the curated Magic Formula dataset."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from data_quality.monitoring import run_data_quality_checks
from etl.local_pipeline import refresh_from_curated


def run(*, curated_path: Optional[Path] = None, output_dir: Optional[Path] = None) -> None:
    """Load the curated fundamentals CSV, rank the rows, and rewrite exports."""
    screening_df, metadata = refresh_from_curated(
        curated_path=curated_path,
        output_dir=output_dir,
    )

    print(f"✅ Refreshed sample dataset with {len(screening_df)} rows.")
    print(f"   Source: {metadata['data_source']}")
    print(f"   Last run: {metadata['run_date']}")

    target_dir = Path(output_dir) if output_dir else Path("data")
    run_data_quality_checks(target_dir / "latest_screening.csv")


if __name__ == "__main__":
    run()
