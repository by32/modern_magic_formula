"""
Russell 1000 Magic Formula ETL with intelligent batching and dual data sources.

This module processes the full Russell 1000 universe using:
1. Alpha Vantage bulk API (100 tickers/call, 500 calls/day free tier)
2. Yahoo Finance fallback for remaining stocks
3. Intelligent caching and batching to respect rate limits
"""
import logging, os, pandas as pd, json, time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from etl.russell_1000 import get_cached_russell_1000
from etl.fetch import get_alpha_vantage_bulk_fundamentals, get_yahoo_finance_fundamentals
from etl.compute import compute_earnings_yield, compute_roc

def get_api_usage_tracker() -> Dict:
    """Track daily API usage to stay within limits."""
    tracker_file = 'data/api_usage.json'
    today = datetime.now().strftime('%Y-%m-%d')
    
    try:
        if os.path.exists(tracker_file):
            with open(tracker_file, 'r') as f:
                usage = json.load(f)
        else:
            usage = {}
        
        # Reset counter if it's a new day
        if usage.get('date') != today:
            usage = {'date': today, 'alpha_vantage_calls': 0, 'yahoo_calls': 0}
        
        return usage
    except Exception:
        return {'date': today, 'alpha_vantage_calls': 0, 'yahoo_calls': 0}

def save_api_usage_tracker(usage: Dict):
    """Save API usage tracking."""
    tracker_file = 'data/api_usage.json'
    os.makedirs('data', exist_ok=True)
    
    try:
        with open(tracker_file, 'w') as f:
            json.dump(usage, f, indent=2)
    except Exception as e:
        print(f"⚠️  Could not save API usage tracker: {e}")

def process_stocks_batch(stocks: List[Dict], api_key: str, batch_size: int = 100) -> List[Dict]:
    """
    Process stocks in batches using Alpha Vantage bulk API + Yahoo Finance fallback.
    
    Args:
        stocks: List of stock info dicts from Russell 1000
        api_key: Alpha Vantage API key
        batch_size: Number of stocks per Alpha Vantage call (max 100)
        
    Returns:
        List of processed stock data with financial metrics
    """
    results = []
    usage = get_api_usage_tracker()
    
    # Alpha Vantage free tier limits: 500 calls/day, 5 calls/minute
    MAX_ALPHA_CALLS_PER_DAY = 500
    MAX_ALPHA_CALLS_PER_MINUTE = 5
    
    alpha_calls_used = usage.get('alpha_vantage_calls', 0)
    yahoo_calls_used = usage.get('yahoo_calls', 0)
    
    print(f"📊 Processing {len(stocks)} stocks...")
    print(f"📈 API usage today: Alpha Vantage {alpha_calls_used}/{MAX_ALPHA_CALLS_PER_DAY}, Yahoo Finance {yahoo_calls_used}")
    
    # Split stocks into batches
    batches = [stocks[i:i + batch_size] for i in range(0, len(stocks), batch_size)]
    
    alpha_calls_this_session = 0
    yahoo_fallback_count = 0
    
    for batch_idx, batch in enumerate(batches):
        print(f"\n🔄 Processing batch {batch_idx + 1}/{len(batches)} ({len(batch)} stocks)...")
        
        # Check if we can still use Alpha Vantage
        can_use_alpha = (alpha_calls_used + alpha_calls_this_session < MAX_ALPHA_CALLS_PER_DAY)
        
        if can_use_alpha and api_key:
            # Try Alpha Vantage bulk API
            tickers = [stock['ticker'] for stock in batch]
            
            # Rate limiting: max 5 calls per minute
            if alpha_calls_this_session > 0 and alpha_calls_this_session % MAX_ALPHA_CALLS_PER_MINUTE == 0:
                print("⏱️  Rate limiting: waiting 60 seconds...")
                time.sleep(60)
            
            bulk_data = get_alpha_vantage_bulk_fundamentals(tickers, api_key)
            alpha_calls_this_session += 1
            
            # Process Alpha Vantage results
            for stock in batch:
                ticker = stock['ticker']
                
                if ticker in bulk_data:
                    raw_data = bulk_data[ticker]
                    processed = process_single_stock(ticker, raw_data, stock)
                    if processed:
                        results.append(processed)
                else:
                    # Fall back to Yahoo Finance for this stock
                    yahoo_data = get_yahoo_finance_fundamentals(ticker)
                    yahoo_calls_used += 1
                    yahoo_fallback_count += 1
                    
                    if yahoo_data:
                        processed = process_single_stock(ticker, yahoo_data, stock)
                        if processed:
                            results.append(processed)
        else:
            # Use Yahoo Finance for entire batch
            print(f"📊 Using Yahoo Finance for batch {batch_idx + 1} (Alpha Vantage limit reached)")
            
            for stock in batch:
                ticker = stock['ticker']
                yahoo_data = get_yahoo_finance_fundamentals(ticker)
                yahoo_calls_used += 1
                yahoo_fallback_count += 1
                
                if yahoo_data:
                    processed = process_single_stock(ticker, yahoo_data, stock)
                    if processed:
                        results.append(processed)
                
                # Small delay to be respectful to Yahoo Finance
                time.sleep(0.1)
    
    # Update usage tracking
    usage['alpha_vantage_calls'] = alpha_calls_used + alpha_calls_this_session
    usage['yahoo_calls'] = yahoo_calls_used
    save_api_usage_tracker(usage)
    
    print(f"\n📈 Batch processing complete:")
    print(f"   ✅ {len(results)} stocks successfully processed")
    print(f"   🌐 Alpha Vantage calls: {alpha_calls_this_session}")
    print(f"   🔄 Yahoo Finance fallbacks: {yahoo_fallback_count}")
    
    return results

def process_single_stock(ticker: str, raw_data: Dict, stock_info: Dict) -> Optional[Dict]:
    """Process a single stock's raw fundamental data into Magic Formula metrics."""
    try:
        # Extract financial data
        market_cap = float(raw_data.get("MarketCapitalization", 0))
        ebitda = float(raw_data.get("EBITDA", 0)) if raw_data.get("EBITDA") not in ['None', '', 'N/A', None] else 0
        eps = float(raw_data.get("EPS", 0)) if raw_data.get("EPS") not in ['None', '', 'N/A', None] else 0
        revenue = float(raw_data.get("RevenueTTM", 0)) if raw_data.get("RevenueTTM") not in ['None', '', 'N/A', None] else 0
        name = raw_data.get("Name", stock_info.get('name', ticker))
        
        if market_cap <= 0:
            print(f"⚠️  Invalid market cap for {ticker}, skipping...")
            return None
        
        # Calculate earnings yield using available data
        if ebitda > 0:
            # Use EBITDA as proxy for earnings, market cap as proxy for enterprise value
            ey = ebitda / market_cap
        elif eps > 0:
            # Use EPS-based earnings yield
            pe_ratio = float(raw_data.get("PERatio", 0)) if raw_data.get("PERatio") not in ['None', '', 'N/A', None] else 0
            ey = 1 / pe_ratio if pe_ratio > 0 else eps / market_cap
        else:
            print(f"⚠️  No earnings data for {ticker}, skipping...")
            return None
        
        # Calculate ROC using return on equity as proxy
        roe = float(raw_data.get("ReturnOnEquityTTM", 0)) if raw_data.get("ReturnOnEquityTTM") not in ['None', '', 'N/A', None] else 0
        roc = roe if roe > 0 else ey * 1.2  # Fallback to approximation
        
        return {
            "ticker": ticker,
            "company_name": name,
            "earnings_yield": ey,
            "roc": roc,
            "market_cap": market_cap,
            "ebitda": ebitda,
            "eps": eps,
            "revenue": revenue,
            "sector": raw_data.get("Sector", stock_info.get('sector', 'Unknown')),
            "weight": stock_info.get('weight', 0),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error processing {ticker}: {e}")
        return None

def run_russell_1000_screening():
    """
    Run the full Russell 1000 Magic Formula screening with intelligent batching.
    """
    print("🎯 Starting Russell 1000 Magic Formula ETL...")
    start_time = datetime.now()
    
    # Step 1: Get Russell 1000 stock list
    russell_stocks = get_cached_russell_1000()
    
    if not russell_stocks:
        print("❌ Could not fetch Russell 1000 list. Exiting.")
        return
    
    print(f"📋 Loaded {len(russell_stocks)} stocks from Russell 1000")
    
    # Step 2: Get API key
    api_key = os.environ.get("ALPHA_VANTAGE_KEY")
    if not api_key:
        print("⚠️  No ALPHA_VANTAGE_KEY found. Using Yahoo Finance only.")
    
    # Step 3: Process stocks with intelligent batching
    processed_stocks = process_stocks_batch(russell_stocks, api_key or "", batch_size=100)
    
    if not processed_stocks:
        print("❌ No stocks were successfully processed. Check your API keys and data sources.")
        return
    
    # Step 4: Calculate Magic Formula rankings
    df = pd.DataFrame(processed_stocks)
    
    # Sort by earnings yield (descending) and then ROC (descending)
    df = df.sort_values(['earnings_yield', 'roc'], ascending=[False, False])
    df['magic_formula_rank'] = range(1, len(df) + 1)
    
    # Step 5: Save results to static files
    os.makedirs('data', exist_ok=True)
    
    # CSV for Streamlit app
    df.to_csv('data/latest_screening.csv', index=False)
    print(f"✅ Saved {len(df)} stocks to data/latest_screening.csv")
    
    # JSON for API-like access
    df.to_json('data/latest_screening.json', orient='records', date_format='iso')
    print(f"✅ Saved data to data/latest_screening.json")
    
    # Metadata
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    
    metadata = {
        "run_date": end_time.isoformat(),
        "total_stocks": len(df),
        "russell_1000_stocks": len(russell_stocks),
        "successful_fetches": len(processed_stocks),
        "processing_time_seconds": processing_time,
        "data_sources": ["Alpha Vantage API", "Yahoo Finance"],
        "version": "2.0-russell1000"
    }
    
    with open('data/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Saved metadata")
    
    # Step 6: Display results
    print(f"\n🏆 Russell 1000 Magic Formula Rankings (Top 20):")
    print("="*80)
    for _, row in df.head(20).iterrows():
        print(f"{row['magic_formula_rank']:2d}. {row['ticker']:6s} - {row['company_name'][:35]:<35}")
        print(f"    EY: {row['earnings_yield']*100:6.2f}%  ROC: {row['roc']*100:6.2f}%  MC: ${row['market_cap']/1e9:6.0f}B  [{row['sector'][:20]}]")
        print()
    
    print(f"🎯 Russell 1000 ETL Complete!")
    print(f"   📊 {len(processed_stocks)}/{len(russell_stocks)} stocks processed ({len(processed_stocks)/len(russell_stocks)*100:.1f}%)")
    print(f"   ⏱️  Processing time: {processing_time:.1f} seconds")
    print(f"   🥇 Top pick: {df.iloc[0]['ticker']} - {df.iloc[0]['company_name']}")

if __name__ == "__main__":
    run_russell_1000_screening()