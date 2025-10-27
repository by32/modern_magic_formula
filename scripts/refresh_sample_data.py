#!/usr/bin/env python3
"""Regenerate the static sample dataset from the curated fundamentals CSV."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from etl.local_pipeline import refresh_from_curated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--curated-path",
        type=Path,
        default=None,
        help="Optional path to the curated_fundamentals.csv file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where latest_screening.csv/json will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    screening_df, metadata = refresh_from_curated(
        curated_path=args.curated_path,
        output_dir=args.output_dir,
    )
    print(f"✅ Refreshed sample dataset with {len(screening_df)} rows.")
    print(f"   Source: {metadata['data_source']}")
    print(f"   Outputs written to: {(args.output_dir or Path('data')).resolve()}")


if __name__ == "__main__":
    main()
