# GitHub Actions Workflow Architecture

## Overview
The Modern Magic Formula system uses GitHub Actions for automated data processing and quality monitoring. The Vercel web interface asynchronously fetches data from the GitHub repository.

## Data Flow Architecture

```
GitHub Actions (Data Generation) → GitHub Repository (Data Storage) → Vercel App (Data Display)
```

1. **ETL Workflows** run on schedule to generate CSV data files
2. **Data files** are committed to the repository
3. **Vercel app** fetches data dynamically from GitHub raw content API
4. **Users** see always-fresh data without rebuilding the web app

## Scheduled Workflows

### 📊 Weekly Screening Update (`update-screening.yml`)
- **Schedule**: Every Monday at 6 AM UTC
- **Purpose**: Regular weekly refresh of Magic Formula rankings
- **Process**: 
  - Runs `etl.main_russell_hybrid` to process Russell 1000 stocks
  - Commits updated CSV files to repository
  - Creates summary report with top picks
- **Output**: `data/latest_screening_hybrid.csv`

### 📅 Monthly ETL Update (`monthly-etl.yml`)  
- **Schedule**: 1st of each month at 6 AM UTC
- **Purpose**: Comprehensive monthly data refresh
- **Process**:
  - Full Russell 1000 ETL with quality validation
  - Processes ~965 stocks with SEC EDGAR + Yahoo Finance data
  - Extensive data quality checks
- **Output**: Complete dataset with metadata

### 🔄 Quarterly Rebalance (`quarterly-rebalance.yml`)
- **Schedule**: January 15, April 15, July 15, October 15 at 6 AM UTC
- **Purpose**: Major quarterly portfolio rebalancing
- **Special Features**:
  - July run includes Russell 1000 universe reconstitution
  - Extended timeout for comprehensive processing
  - Backtesting and performance analysis

### 🔍 Data Quality Monitor (`data-quality-monitor.yml`)
- **Schedule**: Daily at 12 PM UTC
- **Triggers**: Also runs after ETL updates
- **Purpose**: Continuous data quality monitoring
- **Process**:
  - Validates data freshness and completeness
  - Checks for anomalies and missing data
  - Generates quality dashboard
- **Output**: `quality_dashboard.md`

## Manual Triggers

### 🔧 Manual ETL Trigger (`manual-etl.yml`)
- **Purpose**: On-demand ETL for testing or emergency updates
- **Modes**:
  - `test`: Process 50 stocks for quick testing
  - `full`: Process all ~1000 Russell 1000 stocks
  - `emergency`: Immediate update with reduced validation
- **Use Case**: Testing changes or fixing data issues

## Web Interface Integration

The Vercel-deployed web application:
1. **Fetches data** from `https://raw.githubusercontent.com/.../data/latest_screening_hybrid.csv`
2. **Caches results** for 5 minutes to reduce API calls
3. **No rebuild needed** when data updates
4. **Always shows latest** data from most recent workflow run

## Workflow Dependencies

```
monthly-etl.yml / update-screening.yml
           ↓
    [CSV Data Files]
           ↓
   data-quality-monitor.yml
           ↓
    [Quality Dashboard]
```

## Configuration Requirements

### GitHub Secrets Required:
- `ALPHA_VANTAGE_KEY`: For fundamental data
- `FINNHUB_KEY`: For market data
- `FMP_KEY`: (Optional) Additional data source
- `IEX_TOKEN`: (Optional) Additional data source

### Permissions:
All workflows that commit data need:
```yaml
permissions:
  contents: write
```

## Best Practices

1. **Data Generation**: ETL workflows generate and commit CSV files
2. **Data Storage**: GitHub repository serves as data lake
3. **Data Display**: Vercel app fetches data dynamically
4. **Monitoring**: Daily quality checks ensure data integrity
5. **Redundancy**: Multiple data sources (SEC EDGAR + Yahoo Finance)

## Troubleshooting

### Common Issues:
1. **Permission Denied**: Ensure `contents: write` permission is set
2. **ETL Failures**: Check API key validity and rate limits
3. **Data Not Updating**: Verify workflow schedules and success status
4. **Web App Shows Old Data**: Check 5-minute cache expiration

### Monitoring Workflow Health:
```bash
# Check recent workflow runs
gh run list --repo by32/modern_magic_formula --limit 10

# View specific workflow details
gh workflow view "📊 Monthly ETL Update"

# Download artifacts from failed runs
gh run download <run-id>
```

## Future Enhancements

1. **Real-time triggers**: Webhook-based updates on market events
2. **Incremental updates**: Only process changed stocks
3. **Multi-region deployment**: Reduce latency globally
4. **Historical tracking**: Store time-series data for backtesting