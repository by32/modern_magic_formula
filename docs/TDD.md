# Technical Design Document (TDD)

## Architecture Diagram
```
┌────────cron────────┐
│ GitHub Actions     │
└──┬──────────────▲──┘
   │ weekly run   │
┌──▼──────────────┴─┐        ┌──────────────┐
│ etl (Docker)      │  REST  │ FastAPI API  │
│  • fetch.py       │ <────► │  /api/*      │
│  • compute.py     │        └──▲───────────┘
│  • store.py       │           │ read‑only
└──▲────────────────┘           │
   │ writes                      │
┌──┴──────────────┐              │
│ Postgres        │──────────────┘
└─────────────────┘              ▲
                                 │
                          ┌──────┴───────┐
                          │ Streamlit UI │
                          └──────────────┘
```

## Key Components
### 1 ETL Package (`etl/`)
* `fetch.py` – API wrappers for FMP, IEX Cloud, Finnhub
* `compute.py` – calculates EY, ROC, F‑Score, momentum, sentiment
* `store.py` – SQLAlchemy models; upserts results
* `main.py` – CLI entry: `python -m etl.main`

### 2 API (`api/`)
* FastAPI app with endpoints:
  * `/api/stocks/latest`
  * `/api/deltas/latest`

### 3 UI (`app/streamlit_app.py`)
* Loads latest screening into Pandas
* `st.dataframe` table with conditional formatting
* Expander for detailed view

## Database Schema
```
TABLE stocks (
  ticker TEXT PK,
  name   TEXT
);

TABLE runs (
  run_id SERIAL PK,
  run_date TIMESTAMP DEFAULT now()
);

TABLE fundamentals (
  run_id INT FK REFERENCES runs,
  ticker TEXT FK REFERENCES stocks,
  earnings_yield NUMERIC,
  roc NUMERIC,
  f_score SMALLINT,
  debt_to_equity NUMERIC,
  momentum_6m NUMERIC,
  short_pct_float NUMERIC,
  news_sentiment NUMERIC,
  combined_rank INT,
  PRIMARY KEY (run_id, ticker)
);

TABLE deltas (
  run_id INT FK,
  ticker TEXT,
  status TEXT,
  rank_change INT,
  PRIMARY KEY (run_id, ticker)
);
```

## Technology Choices
| Concern | Choice | Reason |
|---------|--------|--------|
| Web UI  | **Streamlit** | Fast dashboarding, pure Python |
| API     | **FastAPI**   | ASGI, OpenAPI schema, easy tests |
| DB      | **Postgres**  | ACID, JSONB support |
| Tests   | **pytest** + `pytest‑asyncio` | Async friendly |
| CI/CD   | **GitHub Actions** | Free for small usage |

## Security
* Secrets via environment; no credentials in Git
* HTTPS termination at reverse‑proxy/CDN
* Rate‑limit UI and API to 100 req/min/IP
