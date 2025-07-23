# Magic Formula Screener

This project is a Python‑based web application that runs Joel Greenblatt’s **Magic Formula** screen weekly, 
adds value‑trap avoidance checks (momentum, Piotroski F‑Score, debt, cash‑flow, sentiment), and surfaces the results in an interactive dashboard.

**Main components**

| Component | Tech | Purpose |
|-----------|------|---------|
| ETL job   | Python 3.12, Docker | Pulls data from free APIs (FMP, IEX Cloud, Finnhub), computes metrics, stores in Postgres |
| API       | FastAPI            | Read‑only JSON endpoints for latest screening results & deltas |
| UI        | Streamlit          | Table, filters, drill‑downs, export |
| Storage   | Postgres (RDS)     | Historical run data |
| CI/CD     | GitHub Actions     | Build, test, deploy Docker images and Streamlit app |

## Quick‑start (local)

```bash
git clone <repo>
cd magic_formula_app
docker compose up --build
# ⇨ visit http://localhost:8501 for the Streamlit UI
```

`docker compose` spins up:

* **db** – Postgres 15 with sample data
* **etl** – Reads env vars for API keys, fetches data, writes to DB
* **api** – FastAPI on port 8000
* **ui** – Streamlit on port 8501

## Weekly Automation

Add a crontab entry on your host or schedule a GitHub Actions workflow:

```
# Every Monday 06:00 UTC
0 6 * * 1 docker compose run etl python -m etl.main
```

## Configuration

Create `.env` (or use AWS SSM) with:

```
ALPHA_VANTAGE_KEY=XXXX
FMP_KEY=XXXX
FINNHUB_KEY=XXXX
IEX_TOKEN=XXXX
DATABASE_URL=postgresql://user:pass@db:5432/mf
```

## Disclaimer

This software is provided **as‑is** for educational purposes. It does not constitute investment advice.
