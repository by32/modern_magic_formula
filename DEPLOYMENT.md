# Deployment Guide

This guide walks you through deploying your Magic Formula screener to **$0/month** hosting using Streamlit Cloud.

## ✅ What We've Built

- **Static Files Architecture**: ETL → CSV/JSON files → Streamlit dashboard
- **Sample Data Generated**: 6 stocks with realistic Magic Formula rankings
- **GitHub Actions Workflow**: Automated weekly data updates
- **Working Streamlit App**: Ready for cloud deployment

## 🚀 Next Steps for Full Deployment

### 1. Set Up API Keys (Optional)

For real financial data, add these secrets to your GitHub repository:

**GitHub Settings → Secrets and Variables → Actions**:
```
ALPHA_VANTAGE_KEY=your_alpha_vantage_key
FMP_KEY=your_fmp_key  
FINNHUB_KEY=your_finnhub_key
IEX_TOKEN=your_iex_token
```

**Get free API keys from**:
- [Alpha Vantage](https://www.alphavantage.co/support/#api-key) - 25 calls/day free
- [Financial Modeling Prep](https://financialmodelingprep.com/developer/docs) - 250 calls/day free
- [Finnhub](https://finnhub.io/register) - 60 calls/minute free
- [IEX Cloud](https://iexcloud.io/pricing/) - 500,000 calls/month free

*Note: The app works fine with sample data if you skip this step.*

### 2. Deploy to Streamlit Cloud

1. **Push to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "🚀 Ready for Streamlit Cloud deployment"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New App"
   - Connect your GitHub repository
   - Set **Main file path**: `streamlit_app.py`
   - Click "Deploy!"

3. **Your app will be live** at: `https://your-repo-name.streamlit.app`

### 3. Set Up Automated Updates

The GitHub Actions workflow is already configured to:
- ✅ Run every Monday at 6:00 UTC
- ✅ Generate new screening data
- ✅ Commit updates to repository
- ✅ Automatically trigger Streamlit app refresh

**Manual trigger**: Go to GitHub Actions → "Update Magic Formula Screening" → "Run workflow"

## 📊 Testing Locally

**Start the app locally**:
```bash
# Install dependencies
uv venv && source .venv/bin/activate
uv pip install pandas streamlit

# Generate sample data (if needed)
python generate_sample_data.py

# Run the app
streamlit run streamlit_app.py
```

**Visit**: http://localhost:8501

## 🎯 What You'll Get

**Free hosting** with:
- ✅ Interactive Magic Formula dashboard
- ✅ Weekly automated data updates  
- ✅ Filtering by market cap, earnings yield, ROC
- ✅ CSV export functionality
- ✅ Stock details and rankings
- ✅ Clean, professional interface

**Zero monthly costs** using:
- Streamlit Cloud (free hosting)
- GitHub Actions (free CI/CD)
- Static file storage (no database costs)

## 🔧 Advanced Setup

### Custom Domain (Optional)
Streamlit Cloud supports custom domains on paid plans, or you can use a reverse proxy.

### Enhanced Data Sources
Add more financial metrics by expanding the ETL process:
- Debt-to-equity ratios
- Piotroski F-Score
- Momentum indicators
- Sentiment analysis

### Backtesting Module
Add historical performance tracking by storing previous screening results.

## 📈 Usage

Once deployed, your app will:
1. **Display** the latest Magic Formula rankings
2. **Update** automatically every Monday
3. **Allow** users to filter and export results  
4. **Show** detailed metrics for each stock

Perfect for personal investment research or sharing with others!

## 🆘 Troubleshooting

**App won't start?**
- Check `requirements.txt` has all dependencies
- Ensure `streamlit_app.py` is in the root directory

**No data showing?**  
- Run `python generate_sample_data.py` to create test data
- Check `data/` directory exists and has CSV files

**GitHub Actions failing?**
- Check if API keys are set correctly in repository secrets
- Review the workflow logs in GitHub Actions tab

## 🎉 You're Done!

Your Magic Formula screener is now ready for $0/month deployment. The static files approach gives you maximum reliability with minimal complexity.