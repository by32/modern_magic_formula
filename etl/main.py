"""CLI entry: runs the full ETL job."""
import logging, os, pandas as pd
from etl.fetch import get_alpha_vantage_fundamentals
from etl.compute import compute_earnings_yield, compute_roc

def run():
    tickers = ["AAPL", "MSFT", "GOOG"]  # placeholder
    rows = []
    key = os.environ["ALPHA_VANTAGE_KEY"]
    for t in tickers:
        raw = get_alpha_vantage_fundamentals(t, key)
        ebit = float(raw.get("EBIT", 0))
        ev = float(raw.get("EnterpriseValue", 0))
        ey = compute_earnings_yield(ebit, ev)
        rows.append({"ticker": t, "earnings_yield": ey})
    df = pd.DataFrame(rows)
    print(df)

if __name__ == "__main__":
    run()
