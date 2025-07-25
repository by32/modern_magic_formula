"""CLI entry: runs the full ETL job and saves results to static files."""
import logging, os, pandas as pd, json
from datetime import datetime
from etl.fetch import get_alpha_vantage_fundamentals
from etl.compute import compute_earnings_yield, compute_roc

def run():
    # Expanded ticker list for better Magic Formula screening
    tickers = ["AAPL", "MSFT", "GOOGL", "BRK.B", "JNJ", "V", "PG", "JPM", "UNH", "HD", "MA", "DIS", "ADBE", "CRM", "NFLX"]
    rows = []
    key = os.environ.get("ALPHA_VANTAGE_KEY")
    
    if not key:
        raise ValueError("ALPHA_VANTAGE_KEY environment variable is required")
    
    print(f"🔑 Starting Magic Formula ETL with Alpha Vantage API...")
    print(f"📊 Processing {len(tickers)} tickers...")
    
    successful_fetches = 0
    
    for i, ticker in enumerate(tickers):
        try:
            print(f"📈 Fetching data for {ticker} ({i+1}/{len(tickers)})...")
            raw = get_alpha_vantage_fundamentals(ticker, key)
            
            # Check if we got valid data
            if not raw:
                print(f"⚠️  No fundamental data for {ticker}, skipping...")
                continue
                
            # Use Alpha Vantage's available fields
            market_cap = float(raw.get("MarketCapitalization", 0))
            ebitda = float(raw.get("EBITDA", 0)) if raw.get("EBITDA") not in ['None', '', 'N/A', None] else 0
            eps = float(raw.get("EPS", 0)) if raw.get("EPS") not in ['None', '', 'N/A', None] else 0
            revenue = float(raw.get("RevenueTTM", 0)) if raw.get("RevenueTTM") not in ['None', '', 'N/A', None] else 0
            name = raw.get("Name", ticker)
            
            if market_cap <= 0:
                print(f"⚠️  Invalid market cap for {ticker}, skipping...")
                continue
            
            # Calculate earnings yield using available data
            if ebitda > 0:
                # Use EBITDA as proxy for earnings, market cap as proxy for enterprise value
                ey = ebitda / market_cap
            elif eps > 0:
                # Use EPS-based earnings yield
                pe_ratio = float(raw.get("PERatio", 0)) if raw.get("PERatio") not in ['None', '', 'N/A', None] else 0
                ey = 1 / pe_ratio if pe_ratio > 0 else eps / market_cap
            else:
                print(f"⚠️  No earnings data for {ticker}, skipping...")
                continue
            
            # Calculate ROC using return on equity as proxy
            roe = float(raw.get("ReturnOnEquityTTM", 0)) if raw.get("ReturnOnEquityTTM") not in ['None', '', 'N/A', None] else 0
            roc = roe if roe > 0 else ey * 1.2  # Fallback to approximation
            
            rows.append({
                "ticker": ticker,
                "company_name": name,
                "earnings_yield": ey,
                "roc": roc,
                "market_cap": market_cap,
                "ebitda": ebitda,
                "eps": eps,
                "revenue": revenue,
                "last_updated": datetime.now().isoformat()
            })
            
            successful_fetches += 1
            print(f"✅ Successfully processed {ticker}")
            
        except Exception as e:
            print(f"❌ Error processing {ticker}: {e}")
            continue
    
    if not rows:
        print("❌ No valid data retrieved. Check your API key and ticker symbols.")
        return
    
    # Create DataFrame and calculate rankings
    df = pd.DataFrame(rows)
    df = df.sort_values(['earnings_yield', 'roc'], ascending=[False, False])
    df['magic_formula_rank'] = range(1, len(df) + 1)
    
    # Save to static files
    os.makedirs('data', exist_ok=True)
    
    # CSV for Streamlit app
    df.to_csv('data/latest_screening.csv', index=False)
    print(f"✅ Saved {len(df)} stocks to data/latest_screening.csv")
    
    # JSON for API-like access
    df.to_json('data/latest_screening.json', orient='records', date_format='iso')
    print(f"✅ Saved data to data/latest_screening.json")
    
    # Metadata
    metadata = {
        "run_date": datetime.now().isoformat(),
        "total_stocks": len(df),
        "successful_fetches": successful_fetches,
        "data_sources": ["Alpha Vantage API"],
        "version": "1.0-live"
    }
    
    with open('data/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Saved metadata")
    
    # Display results
    print(f"\n🏆 Magic Formula Rankings (Top 10):")
    print("="*60)
    for _, row in df.head(10).iterrows():
        print(f"{row['magic_formula_rank']:2d}. {row['ticker']:6s} - {row['company_name']}")
        print(f"    EY: {row['earnings_yield']*100:.2f}%  ROC: {row['roc']*100:.2f}%  MC: ${row['market_cap']/1e9:.0f}B")
        print()
    
    print(f"🎯 ETL Complete! {successful_fetches} stocks successfully processed.")

if __name__ == "__main__":
    run()
