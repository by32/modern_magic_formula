# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Modern Magic Formula stock screener** that implements Joel Greenblatt's investment methodology with advanced features. The application screens ~1000 Russell 1000 stocks monthly using SEC point-in-time fundamentals and provides a professional web interface for individual investors.

## Architecture

The project uses a **modern serverless architecture**:

1. **ETL Pipeline** (`etl/`): Python data pipeline with hybrid SEC EDGAR + Yahoo Finance data fetching
2. **Web Interface** (`web/`): Next.js/React application deployed on Vercel with Tailwind CSS
3. **GitHub Actions** (`/.github/workflows/`): Automated monthly ETL, quarterly rebalancing, and quality monitoring
4. **Data Storage**: CSV files in Git with dynamic fetching via GitHub raw content API

## Production Status: ✅ FULLY OPERATIONAL

### Current Capabilities:
- **Russell 1000 Processing**: 965+ stocks analyzed monthly (94.8% success rate)
- **SEC EDGAR Integration**: 99.6% coverage with point-in-time fundamentals
- **Magic Formula Rankings**: Complete earnings yield + ROC calculations  
- **Quality Scoring**: Piotroski F-Score integration with value trap avoidance
- **Web Interface**: Professional React app at https://modernmagicformula.vercel.app
- **Automated Updates**: Monthly ETL via GitHub Actions

## Quick Start

### View Latest Results
```bash
# Check latest screening data
cat data/latest_screening_hybrid.csv

# View web interface
# Visit your deployed Vercel app
```

### Run Manual ETL
```bash
# Test mode (50 stocks)
gh workflow run "🔧 Manual ETL Trigger" --field mode=test

# Full production (1000 stocks) 
gh workflow run "🔧 Manual ETL Trigger" --field mode=full
```

### Local Development
```bash
# Install dependencies
uv sync

# Run ETL locally
uv run python -m etl.main_russell_hybrid

# Start web development server
cd web && npm run dev
```

## Environment Configuration

GitHub Actions configured with secrets:
```
ALPHA_VANTAGE_KEY=*** (required)
FINNHUB_KEY=*** (required)
FMP_KEY= (optional)
IEX_TOKEN= (optional)
```

## Key Components

### ETL Pipeline (`etl/`)
- `main_russell_hybrid.py`: Primary ETL orchestrator with hybrid SEC+Yahoo data
- `hybrid_fundamentals.py`: Point-in-time SEC EDGAR integration
- `compute.py`: Magic Formula calculations, F-Score, and quality scoring
- `fetch.py`: API data fetching (Alpha Vantage, Yahoo Finance)
- `russell_1000.py`: Russell 1000 universe management
- `sec_direct_fundamentals.py`: Direct SEC XBRL API access
- `transaction_costs.py`: Bid-ask spread modeling
- `realistic_costs.py`: Advanced transaction cost modeling

### Web Interface (`web/`)
- `src/app/page.tsx`: Main DIY stock screening interface
- `src/app/api/stocks/route.ts`: Dynamic data API from GitHub
- `src/app/api/quality/route.ts`: Data quality monitoring API
- Deployed on Vercel with automatic GitHub integration

### Automation (`/.github/workflows/`)
- `monthly-etl.yml`: Automated Russell 1000 refresh (1st of month)
- `quarterly-rebalance.yml`: Quarterly portfolio rebalancing
- `data-quality-monitor.yml`: Daily quality checks and alerts
- `manual-etl.yml`: On-demand ETL trigger

## Data Quality

### Current Metrics (Production):
- **Processing Success**: 94.8% (965/1018 stocks)
- **SEC EDGAR Coverage**: 99.6% (961/965 stocks)
- **Yahoo Finance Coverage**: 100% (965/965 stocks)
- **Processing Time**: ~24 minutes for full Russell 1000
- **Data Freshness**: Updated monthly via automated workflows

## Magic Formula Implementation

### Core Methodology:
1. **Earnings Yield**: EBIT / Enterprise Value
2. **Return on Capital**: EBIT / (Working Capital + Net Fixed Assets)
3. **Combined Ranking**: Average of EY rank + ROC rank
4. **Quality Filter**: Piotroski F-Score ≥5 recommended
5. **Sector Diversification**: Max 25% per sector

### Enhanced Features:
- **Point-in-time fundamentals** (eliminates look-ahead bias)
- **Value trap avoidance** (momentum, debt analysis, cash flow quality)
- **Transaction cost modeling** (Corwin-Schultz bid-ask spreads)
- **Tax-aware analysis** (FIFO/LIFO lot tracking)

## Recent Major Updates

### ✅ Completed (December 2025):
- **Security fix**: Patched critical RCE vulnerability (CVE-2025-55182) - Next.js upgraded to 15.4.8
- **ETL cleanup**: Removed 5 legacy files (~1,100 lines), keeping full investment toolkit
- **Codebase simplification**: Reduced from 14 to 8 ETL modules

### ✅ Completed (August 2025):
- **Fixed numpy/pandas binary compatibility** in GitHub Actions
- **Migrated from Streamlit Cloud to Vercel** (better reliability)
- **Implemented dynamic data sync** from GitHub raw content API
- **Successfully completed first production run** (965 stocks processed)
- **Resolved all GitHub Actions workflow failures**
- **Created professional React/Next.js web interface**

### 📊 Production Run Results:
- **Top Picks**: OGN (52% EY), CHRD (44% EY), VTRS (33% EY), EQH (27% EY), OXY (26% EY)
- **Sector Distribution**: Energy, Healthcare, Technology, Financial Services
- **Quality Scores**: F-Scores 2-6, with energy stocks leading

## Testing Strategy

- **Unit Tests**: `tests/test_compute.py` for financial calculations
- **Integration Tests**: GitHub Actions workflows with real API data
- **Quality Monitoring**: Automated daily checks with Great Expectations
- **Manual Testing**: On-demand ETL triggers for validation

## Deployment

### Production Setup:
1. **GitHub Actions**: Automated monthly ETL processing
2. **Vercel Deployment**: Web interface with serverless API routes
3. **Data Pipeline**: CSV files committed to Git, served via GitHub API
4. **Monitoring**: Daily quality checks with artifact uploads

### Access Points:
- **Web Interface**: https://modernmagicformula.vercel.app
- **GitHub Actions**: https://github.com/by32/modern_magic_formula/actions
- **Data Files**: `data/latest_screening_hybrid.csv`
- **Quality Reports**: Uploaded as GitHub Actions artifacts

## Important Notes

- **API Rate Limits**: Monitor Alpha Vantage usage (production uses ~1000 calls/month)
- **Processing Time**: Full ETL takes 20-30 minutes, plan accordingly
- **Data Quality**: 94.8% success rate is excellent for financial data
- **Git Permissions**: Manual commits may fail, but artifacts are always saved
- **Security**: All API keys stored as GitHub Secrets, never in code

---
*Last Updated: December 2025 - System is fully operational and processing Russell 1000 monthly*