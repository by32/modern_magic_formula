# Modern Magic Formula

A comprehensive Python-based investment screening system that enhances Joel Greenblatt's **Magic Formula** with modern quality metrics, value-trap avoidance techniques, and backtesting capabilities.

## 🚀 Key Features

### Core Magic Formula Implementation
- **Earnings Yield**: EBIT / Enterprise Value
- **Return on Capital**: EBIT / (Net Working Capital + Net Fixed Assets)
- Russell 1000 universe screening

### Modern Quality Enhancements
- **Piotroski F-Score**: 9-point financial strength assessment
- **Cash Flow Quality**: 5-point earnings validation system
- **Momentum Analysis**: 6-month price strength scoring
- **Debt Health Analysis**: Leverage and financial stability metrics
- **Sentiment Analysis**: Market confidence proxy indicators

### Advanced Backtesting Framework
- Hybrid approach combining current rankings with historical prices
- Quarterly rebalancing with realistic transaction costs
- Comprehensive performance metrics vs S&P 500 benchmark
- **Proven Results**: 16.58% annualized returns vs 10.51% benchmark (2021-2024)

### Interactive Dashboard
- Real-time screening with advanced filters
- Export capabilities for portfolio construction
- Quality score visualization and ranking

## 📊 Performance Highlights

**3-Year Backtest Results (2021-2024):**
- **Total Return**: 57.49%
- **Annualized Return**: 16.58%
- **Excess Alpha**: 7.18% above S&P 500
- **Sharpe Ratio**: 0.66
- **Maximum Drawdown**: -24.31%

## 🏗️ Architecture

| Component | Technology | Purpose |
|-----------|------------|---------|
| ETL Pipeline | Python 3.12, UV | Fetches data from Yahoo Finance & Alpha Vantage, computes all metrics |
| Backtesting Engine | Pandas, NumPy, SciPy | Historical simulation with realistic constraints |
| Interactive UI | Streamlit | Advanced filtering, visualization, and export |
| Data Storage | CSV files | Screening results and backtest data |
| CI/CD | GitHub Actions | Automated testing and deployment |

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- UV package manager (recommended) or pip

### Installation
```bash
git clone <repo>
cd modern_magic_formula

# Install dependencies with UV
uv sync

# Or with pip
pip install -r requirements.txt
```

### Running the ETL Pipeline
```bash
# Fetch latest Russell 1000 data and compute all metrics
uv run python etl/main_russell.py

# Or with pip
python etl/main_russell.py
```

### Launch Interactive Dashboard
```bash
# Start Streamlit interface
uv run streamlit run streamlit_app.py

# Or with pip
streamlit run streamlit_app.py
```

### Run Backtesting Analysis
```bash
# Execute 3-year backtest with quarterly rebalancing
uv run python backtesting/run_backtest.py

# Or with pip
python backtesting/run_backtest.py
```

## 📈 Usage Examples

### Basic Screening
```python
from etl.main_russell import run_etl_pipeline

# Run complete ETL pipeline
results = run_etl_pipeline()
print(f"Processed {len(results)} stocks")

# View top 20 Magic Formula stocks
top_stocks = results.head(20)
print(top_stocks[['ticker', 'company_name', 'magic_formula_rank', 'overall_quality_score']])
```

### Advanced Backtesting
```python
from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.metrics import create_performance_summary

# Configure backtest
config = BacktestConfig(
    start_date="2021-01-01",
    end_date="2024-01-01",
    portfolio_size=20,
    rebalance_frequency="quarterly"
)

# Run backtest
engine = BacktestEngine(config)
engine.load_universe(screening_data)
engine.fetch_historical_prices()
results = engine.run_backtest()

# Analyze performance
summary = create_performance_summary(results)
print(f"Annualized Return: {summary['metrics']['annualized_return']*100:.2f}%")
```

## 🔧 Configuration

### Environment Variables
```bash
# Required for Alpha Vantage fundamental data
export ALPHA_VANTAGE_API_KEY="your_api_key_here"

# Optional: Custom data sources
export CUSTOM_DATA_PATH="/path/to/data"
```

### Data Sources
- **Primary**: Yahoo Finance (free, no API key required)
- **Enhanced**: Alpha Vantage (free tier: 25 requests/day)
- **Universe**: Russell 1000 static list

## 📚 Documentation

- **[Methodology Report](docs/METHODOLOGY.md)**: Comprehensive strategy documentation
- **[Changelog](CHANGELOG.md)**: Version history and feature updates
- **[API Reference](docs/api.md)**: Function and class documentation

## 🧪 Testing

```bash
# Run all tests
uv run python -m pytest tests/

# Run specific test categories
uv run python -m pytest tests/test_compute.py -v
uv run python -m pytest tests/test_backtesting.py -v
```

## 🚀 Deployment

### GitHub Actions Automation
The project includes automated workflows for:
- Weekly data updates (Mondays 06:00 UTC)
- Automated testing on pull requests
- Streamlit Cloud deployment

### Manual Deployment
```bash
# Update screening data
uv run python etl/main_russell.py

# Deploy to Streamlit Cloud
# (automatically triggered on main branch push)
```

## 📊 Directory Structure

```
modern_magic_formula/
├── etl/                     # Data extraction and processing
│   ├── main_russell.py      # Main ETL orchestration
│   ├── fetch.py            # Data fetching from APIs
│   ├── compute.py          # Metric calculations
│   └── russell_1000.csv    # Static universe data
├── backtesting/            # Backtesting framework
│   ├── engine.py           # Core backtesting logic
│   ├── metrics.py          # Performance calculations
│   └── run_backtest.py     # Example implementation
├── data/                   # Generated data files
│   └── latest_screening.csv # Current screening results
├── docs/                   # Documentation
│   └── METHODOLOGY.md      # Strategy documentation
├── tests/                  # Test suite
├── streamlit_app.py        # Interactive dashboard
├── requirements.txt        # Dependencies
└── pyproject.toml         # Project configuration
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This software is provided **as-is** for educational and research purposes. It does not constitute investment advice. Past performance does not guarantee future results. Always conduct your own research and consult with qualified financial advisors before making investment decisions.