"""Russell 1000 stock list fetcher from iShares ETF data."""
import requests
import pandas as pd
import io
from typing import List, Dict
import time

def fetch_russell_1000_list() -> List[Dict[str, str]]:
    """
    Fetch Russell 1000 stock list from iShares IWB ETF holdings.
    
    Returns:
        List of dicts with ticker, name, sector, weight info
    """
    url = "https://www.ishares.com/us/products/239707/ishares-russell-1000-etf/1467271812596.ajax?fileType=csv&fileName=IWB_holdings&dataType=fund"
    
    try:
        print("📥 Fetching Russell 1000 list from iShares ETF...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Parse CSV content
        csv_content = response.text
        
        # Skip header rows and read CSV
        lines = csv_content.strip().split('\n')
        
        # Find the start of actual data (usually after some metadata rows)
        data_start = 0
        for i, line in enumerate(lines):
            if 'Ticker' in line or 'Symbol' in line:
                data_start = i
                break
        
        # Read the actual data
        csv_data = '\n'.join(lines[data_start:])
        df = pd.read_csv(io.StringIO(csv_data))
        
        # Clean and standardize column names
        df.columns = df.columns.str.strip()
        
        # Look for ticker column (might be 'Ticker' or 'Symbol')
        ticker_col = None
        for col in df.columns:
            if col.lower() in ['ticker', 'symbol']:
                ticker_col = col
                break
        
        if ticker_col is None:
            print(f"⚠️  Could not find ticker column. Available columns: {list(df.columns)}")
            return []
        
        # Extract relevant data
        stocks = []
        for _, row in df.iterrows():
            ticker = str(row[ticker_col]).strip()
            
            # Skip empty or invalid tickers
            if pd.isna(ticker) or ticker == '' or ticker == 'nan':
                continue
                
            # Skip cash and other non-equity holdings
            if ticker.upper() in ['CASH', 'USD', 'CASH_USD', '-']:
                continue
            
            name = str(row.get('Name', ticker)).strip() if 'Name' in row else ticker
            sector = str(row.get('Sector', 'Unknown')).strip() if 'Sector' in row else 'Unknown'
            weight = float(row.get('Weight (%)', 0)) if 'Weight (%)' in row else 0.0
            
            stocks.append({
                'ticker': ticker,
                'name': name,
                'sector': sector,
                'weight': weight
            })
        
        print(f"✅ Successfully fetched {len(stocks)} stocks from Russell 1000")
        
        # Show top 10 by weight
        stocks_sorted = sorted(stocks, key=lambda x: x['weight'], reverse=True)
        print("\n🏆 Top 10 holdings by weight:")
        for i, stock in enumerate(stocks_sorted[:10]):
            print(f"{i+1:2d}. {stock['ticker']:6s} - {stock['name'][:40]:<40} ({stock['weight']:.2f}%)")
        
        return stocks
        
    except Exception as e:
        print(f"❌ Error fetching Russell 1000 list: {e}")
        return []

def get_cached_russell_1000() -> List[Dict[str, str]]:
    """
    Get Russell 1000 list with caching (daily refresh).
    Falls back to hardcoded major stocks if fetch fails.
    """
    import os
    import json
    from datetime import datetime, timedelta
    
    cache_file = 'data/russell_1000_cache.json'
    
    # Check if cache exists and is fresh (< 24 hours old)
    if os.path.exists(cache_file):
        try:
            cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
            if cache_age < timedelta(hours=24):
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    print(f"📋 Using cached Russell 1000 list ({len(cached_data)} stocks)")
                    return cached_data
        except Exception as e:
            print(f"⚠️  Error reading cache: {e}")
    
    # Fetch fresh data
    stocks = fetch_russell_1000_list()
    
    if stocks:
        # Save to cache
        os.makedirs('data', exist_ok=True)
        try:
            with open(cache_file, 'w') as f:
                json.dump(stocks, f, indent=2)
            print(f"💾 Cached Russell 1000 list to {cache_file}")
        except Exception as e:
            print(f"⚠️  Could not save cache: {e}")
        
        return stocks
    else:
        print("⚠️  Falling back to major stock list...")
        # Fallback to expanded major stocks if API fails
        return [
            {'ticker': 'AAPL', 'name': 'Apple Inc', 'sector': 'Technology', 'weight': 5.0},
            {'ticker': 'MSFT', 'name': 'Microsoft Corporation', 'sector': 'Technology', 'weight': 4.5},
            {'ticker': 'GOOGL', 'name': 'Alphabet Inc Class A', 'sector': 'Technology', 'weight': 3.5},
            {'ticker': 'AMZN', 'name': 'Amazon.com Inc', 'sector': 'Consumer Discretionary', 'weight': 3.0},
            {'ticker': 'NVDA', 'name': 'NVIDIA Corporation', 'sector': 'Technology', 'weight': 2.8},
            {'ticker': 'META', 'name': 'Meta Platforms Inc', 'sector': 'Technology', 'weight': 2.5},
            {'ticker': 'TSLA', 'name': 'Tesla Inc', 'sector': 'Consumer Discretionary', 'weight': 2.0},
            {'ticker': 'BRK.B', 'name': 'Berkshire Hathaway Inc Class B', 'sector': 'Financial Services', 'weight': 1.8},
            {'ticker': 'JNJ', 'name': 'Johnson & Johnson', 'sector': 'Healthcare', 'weight': 1.5},
            {'ticker': 'V', 'name': 'Visa Inc Class A', 'sector': 'Financial Services', 'weight': 1.4},
            # Add more major stocks to get closer to 50-100 for testing
        ]

if __name__ == "__main__":
    # Test the function
    stocks = get_cached_russell_1000()
    print(f"\n🎯 Total stocks available: {len(stocks)}")