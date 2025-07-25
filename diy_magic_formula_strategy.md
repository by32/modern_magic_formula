# DIY Version of the Modern Magic Formula Strategy

This markdown document provides a practical implementation of the Modern Magic Formula investment strategy, optimized for individual investors using a low-cost brokerage account.

---

## 1. What Stays, What Goes — Executive Summary

| Component | Institutional Version | DIY Adjustment | Rationale |
|-----------|------------------------|----------------|-----------|
| Universe | Russell 1000 proxy w/ mid-cap expansion | Top 1,000 US tickers by market-cap ≥ $1B from IEX/yfinance | Easy to replicate; avoids micro-caps |
| Fundamentals Source | SEC XBRL + Yahoo hybrid | SEC EDGAR API + yfinance, lagged 90 days | Removes look-ahead bias using free data |
| Factor Mix | EY + ROC + Piotroski + CF + HRP + momentum | EY + ROC + Piotroski ≥ 5 + 12-mo price > 0 | Focuses on highest-value inputs |
| Risk Controls | Sector caps, beta band, HRP weights | Equal-weight, ≥10 stocks, ≤25%/sector | Practical and simple |
| Rebalance | Quarterly | Annual (Jan only) | Reduces tax drag and effort |
| Cost Model | Spread + impact | Assume 0 commissions + 5bps slippage | Realistic for sub-$100k accounts |
| Tax Logic | ST/LT lot tracking | Hold ≥ 12 months or use IRA | Greatly simplifies execution |
| Backtest Infra | 20+ year PIT engine | Optional script or spreadsheet since 2015 | Useful but not critical |

---

## 2. Step-by-Step Implementation

### 2.1 Set Up Free Data Access

```bash
pip install yfinance sec-edgar-downloader pandas numpy scipy
```

1. **Price Data** using yfinance:
```python
import yfinance as yf
tickers = ["AAPL", "MSFT", ...]  # Replace with top market-cap names
data = yf.Tickers(" ".join(tickers)).history(period="2y", interval="1d")["Close"]
```

2. **Fundamentals (lag 90 days)** via sec-edgar-downloader:
Use the API to download 10-K/10-Q JSON and calculate:
- Earnings Yield = EBIT / EV
- ROC = EBIT / (Net PPE + Net Working Capital)

### 2.2 Apply the Screen

```python
df['ey_rank'] = df['earnings_yield'].rank(ascending=False)
df['roc_rank'] = df['roc'].rank(ascending=False)
df['combo_rank'] = df['ey_rank'] + df['roc_rank']
df = df[df['piotroski'] >= 5]
df = df[df['price_12m_ret'] > 0]
df = df[df['market_cap'] >= 1e9]
```

Select top 20–30 names from `combo_rank`.

### 2.3 Risk & Diversification Checks

- No more than **25% weight in one sector**
- Equal-weight
- At least **20 total names** (Magic Formula guidance)
- Use fractional shares

### 2.4 Rebalancing Calendar

- Rebalance **annually**: first Monday in **January only**
- Replace names that fall out of the screen
- Maintain equal-weight, ensure minimum 20 names

### 2.5 Record-Keeping

- Track: ticker, buy date, shares, price, notes
- Compare annual performance vs **VTV** and **RSP**
- Consider pausing strategy if it underperforms both for 3 years

---

## 3. Practical Adjustments

| Problem | Workaround |
|--------|------------|
| SEC gaps in early data | Use Yahoo TTM earnings/cash flow with lag |
| No beta calculator | Use PortfolioVisualizer |
| Want automation | GitHub Actions + Codespaces for rebalancing |
| Taxable account | Hold ≥ 18 months or use IRA |

---

## 4. Expected Frictions

- Avoid low-volume names with wide spreads
- Stick to limit orders during mid-day hours
- Rebalance only on schedule unless extreme event occurs
- SEC data may rate-limit; rerun next day if so

---

## 5. Checklist Before Trading

- ✅ Screen updated in last 7 days  
- ✅ EY, ROC, Piotroski ≥ 5, 12m return > 0  
- ✅ Market cap ≥ $1B, ADV ≥ $5M  
- ✅ At least 20 names, ≤ 25% in any sector  
- ✅ Orders placed midday as limit  
- ✅ Comfortable holding for ≥12 months

---

## 6. Why This Works

Even simplified, this strategy captures proven premiums:
- **Value** (EY + ROC)
- **Quality** (Piotroski ≥ 5)
- **Momentum** (12m return > 0)

By skipping complexity and focusing on execution, you retain the alpha engine and avoid overfitting or excessive churn.

---

*Not investment advice. Always match strategy to your financial goals, risk profile, and tax circumstances.*