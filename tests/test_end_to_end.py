"""End-to-end test covering the local ETL refresh workflow."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from data_quality.monitoring import validate_screening_dataframe
from etl.main import run


def test_local_refresh_pipeline(tmp_path: Path) -> None:
    """Refresh the curated dataset and ensure exports & QA succeed."""

    curated_path = tmp_path / "curated.csv"
    curated_df = pd.DataFrame(
        [
            {
                "ticker": "AAA",
                "company_name": "AAA Corp",
                "sector": "Technology",
                "ebit": 1000.0,
                "enterprise_value": 10000.0,
                "market_cap": 12000.0,
                "f_score": 7,
                "cash_flow_quality_score": 4,
                "sentiment_score": 2,
                "momentum_6m": 0.20,
                "debt_to_equity": 0.30,
                "ocf_margin": 0.18,
                "fcf_margin": 0.12,
                "ocf_to_ni_ratio": 1.20,
            },
            {
                "ticker": "BBB",
                "company_name": "BBB Inc",
                "sector": "Industrials",
                "ebit": 400.0,
                "enterprise_value": 16000.0,
                "market_cap": 15000.0,
                "f_score": 6,
                "cash_flow_quality_score": 3,
                "sentiment_score": 1,
                "momentum_6m": 0.08,
                "debt_to_equity": 0.40,
                "ocf_margin": 0.15,
                "fcf_margin": 0.10,
                "ocf_to_ni_ratio": 1.05,
            },
        ]
    )
    curated_df.to_csv(curated_path, index=False)

    output_dir = tmp_path / "output"
    run(curated_path=curated_path, output_dir=output_dir)

    csv_path = output_dir / "latest_screening.csv"
    json_path = output_dir / "latest_screening.json"
    metadata_path = output_dir / "metadata.json"

    assert csv_path.exists()
    assert json_path.exists()
    assert metadata_path.exists()

    screening_df = pd.read_csv(csv_path)
    assert len(screening_df) == len(curated_df)
    assert list(screening_df["ticker"]) == ["AAA", "BBB"]
    assert list(screening_df["magic_formula_rank"]) == [1, 2]
    validate_screening_dataframe(screening_df)

    json_records = json.loads(json_path.read_text())
    assert len(json_records) == len(curated_df)
    assert json_records[0]["ticker"] == "AAA"

    metadata = json.loads(metadata_path.read_text())
    assert metadata["total_stocks"] == len(curated_df)
    assert metadata["version"] == "curated-local"
    assert Path(metadata["data_source"]) == curated_path.resolve()

