# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Magic Formula stock screener** that runs Joel Greenblatt's investment screen weekly. The application implements value-trap avoidance checks (momentum, Piotroski F-Score, debt analysis, cash-flow, sentiment) and presents results in an interactive dashboard.

## Architecture

The project uses a **3-tier Docker architecture**:

1. **ETL Container** (`etl/`): Python data pipeline that fetches financial data from APIs (FMP, IEX Cloud, Finnhub), computes metrics, and stores in Postgres
2. **API Container** (`api/`): FastAPI service providing read-only JSON endpoints for screening results and deltas
3. **UI Container** (`app/`): Streamlit dashboard for interactive data visualization and export

**Database**: Postgres with tables for `stocks`, `runs`, `fundamentals`, and `deltas`

## Development Commands

### Local Development Setup
```bash
# Start full stack (includes sample data)
docker compose up --build

# Run ETL job manually
docker compose run etl python -m etl.main

# Access services
# UI: http://localhost:8501
# API: http://localhost:8000
# Database: localhost:5432
```

### Testing & Code Quality
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run tests with coverage
pytest --cov

# Lint code
black .
flake8
mypy .

# Security scanning
bandit -r .
```

### Individual Service Testing
```bash
# Test single ETL module
python -m pytest tests/test_compute.py

# Run ETL directly (requires API keys in env)
python -m etl.main
```

## Environment Configuration

Required environment variables in `.env`:
```
ALPHA_VANTAGE_KEY=your_key
FMP_KEY=your_key  
FINNHUB_KEY=your_key
IEX_TOKEN=your_token
DATABASE_URL=postgresql://user:pass@db:5432/mf
```

## Key Components

### ETL Pipeline (`etl/`)
- `fetch.py`: API wrappers for financial data sources
- `compute.py`: Calculates earnings yield, ROC, F-Score, momentum, sentiment
- `store.py`: SQLAlchemy models and database operations
- `main.py`: CLI entry point for full ETL run

### API Layer (`api/`)
- FastAPI endpoints: `/api/stocks/latest`, `/api/deltas/latest`
- Read-only access to latest screening results

### UI Layer (`app/streamlit_app.py`)
- Interactive table with filtering and conditional formatting
- Export capabilities for screening results
- Detailed drill-down views

## Testing Strategy

- **Unit tests** in `tests/` directory using pytest
- Focus on `compute.py` functions for financial calculations
- Use pytest fixtures for database testing
- Mock external API calls in tests

## Deployment Notes

- Production runs weekly via cron: `0 6 * * 1 docker compose run etl python -m etl.main`
- All services containerized with separate Dockerfiles
- Use environment variables for all configuration
- Never commit API keys or credentials to repository