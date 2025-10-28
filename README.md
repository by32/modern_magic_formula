# Modern Magic Formula

A lightweight research environment for exploring Joel Greenblatt's Magic Formula using a fully reproducible, static data bundle. The repository ships with a curated snapshot of fundamentals and helper utilities so you can experiment locally without chasing API credentials or running long-running download jobs.

## What's Included

- **Static ETL flow** powered by [`etl/local_pipeline.py`](etl/local_pipeline.py) that transforms the curated fundamentals CSV into ranked Magic Formula outputs.
- **Bundled sample dataset** in `data/` (`latest_screening.csv`/`.json` and `metadata.json`) generated from the curated snapshot so you can start immediately.
- **Lightweight Streamlit viewer** (`streamlit_app.py`) for inspecting the ranked stocks and confirming the bundle loaded correctly.

## Quick Start

1. **Set up the environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Launch the Streamlit viewer**
   ```bash
   streamlit run streamlit_app.py
   ```
   The app reads `data/latest_screening.csv` by default and simply surfaces the rows so you can validate the static bundle.

## Refreshing the Sample Data

When a fresh curated fundamentals snapshot is available, regenerate the derived screens with the provided helper:

```bash
python scripts/refresh_sample_data.py \
    --curated-path data/curated_fundamentals.csv \
    --output-dir data
```

The script recalculates Magic Formula metrics, writes new CSV/JSON outputs, and updates `metadata.json` with the run timestamp and source path. You can point `--curated-path` at any compatible CSV if you maintain multiple snapshots.

## Project Layout

```
modern_magic_formula/
├── app/                     # Original, full Streamlit experience (optional)
├── data/                    # Bundled sample dataset and metadata
├── etl/                     # Static ETL helpers for curated fundamentals
├── scripts/                 # CLI utilities such as refresh_sample_data.py
└── streamlit_app.py         # Minimal viewer for the static bundle
```

## Troubleshooting

- The project is designed to run **without external API keys**. If something requests credentials, confirm you are using the static pipeline (`etl/local_pipeline.py`) and bundled dataset.
- Regenerating the sample data will overwrite the files in `data/`; keep backups if you need to compare historical runs.
- If Streamlit fails to load, ensure the virtual environment is activated and `streamlit` is installed from `requirements.txt`.

## License

This project is released under the MIT License. See [LICENSE](LICENSE) for details.
