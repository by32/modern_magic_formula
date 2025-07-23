"""Data-fetching utilities for external APIs."""
import requests, os, time, logging
import yfinance as yf
from typing import List, Dict, Optional

def get_alpha_vantage_fundamentals(ticker: str, api_key: str):
    """Fetch fundamental data from Alpha Vantage API with proper error handling"""
    url = "https://www.alphavantage.co/query"
    params = {"function": "OVERVIEW", "symbol": ticker, "apikey": api_key}
    
    try:
        print(f"🌐 Making API call to Alpha Vantage for {ticker}...")
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        
        data = r.json()
        
        # Debug: Print the response structure
        print(f"📡 API Response keys: {list(data.keys())}")
        
        # Check for Alpha Vantage error responses
        if "Error Message" in data:
            print(f"❌ Alpha Vantage Error: {data['Error Message']}")
            return {}
        elif "Note" in data:
            print(f"⚠️  Alpha Vantage Rate Limit: {data['Note']}")
            print("💡 Sleeping 60 seconds to respect rate limits...")
            time.sleep(60)  # Wait 60 seconds for rate limit
            return {}
        elif "Information" in data:
            print(f"ℹ️  Alpha Vantage Info: {data['Information']}")
            return {}
        elif len(data) == 0:
            print(f"⚠️  Empty response from Alpha Vantage for {ticker}")
            return {}
        else:
            # Check if we have the essential fields (using Alpha Vantage's actual field names)
            required_fields = ["Symbol", "Name", "MarketCapitalization"]
            optional_fields = ["EBITDA", "EPS", "BookValue", "RevenueTTM"]
            
            missing_required = [field for field in required_fields if field not in data or data[field] in ['None', '', 'N/A']]
            
            if missing_required:
                print(f"⚠️  Missing required fields for {ticker}: {missing_required}")
                print(f"📊 Available fields: {list(data.keys())[:10]}...")  # Show first 10 fields
                return {}
            else:
                # Check if we have at least some financial data
                has_financial_data = any(field in data and data[field] not in ['None', '', 'N/A', None] for field in optional_fields)
                
                if not has_financial_data:
                    print(f"⚠️  No usable financial data for {ticker}")
                    return {}
                else:
                    print(f"✅ Got valid data for {ticker}: {data.get('Name', 'Unknown')}")
                    print(f"📈 Available financial fields: {[f for f in optional_fields if f in data and data[f] not in ['None', '', 'N/A', None]]}")
                    return data
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error fetching {ticker}: {e}")
        return {}
    except Exception as e:
        print(f"❌ Unexpected error fetching {ticker}: {e}")
        return {}

def get_alpha_vantage_bulk_fundamentals(tickers: List[str], api_key: str) -> Dict[str, dict]:
    """
    Fetch fundamental data for multiple tickers using Alpha Vantage bulk API.
    Maximum 100 tickers per call.
    
    Args:
        tickers: List of stock symbols (max 100)
        api_key: Alpha Vantage API key
        
    Returns:
        Dict mapping ticker -> fundamental data
    """
    if len(tickers) > 100:
        print(f"⚠️  Warning: {len(tickers)} tickers provided, but bulk API supports max 100. Truncating.")
        tickers = tickers[:100]
    
    url = "https://www.alphavantage.co/query"
    # Convert list to comma-separated string
    symbol_string = ",".join(tickers)
    
    params = {
        "function": "OVERVIEW",
        "symbol": symbol_string,
        "apikey": api_key
    }
    
    try:
        print(f"🌐 Making bulk API call to Alpha Vantage for {len(tickers)} tickers...")
        r = requests.get(url, params=params, timeout=60)
        r.raise_for_status()
        
        data = r.json()
        
        # Handle different response formats
        results = {}
        
        if isinstance(data, dict):
            # Check for error messages
            if "Note" in data:
                print(f"⚠️  Alpha Vantage Rate Limit: {data['Note']}")
                return {}
            elif "Error Message" in data:
                print(f"❌ Alpha Vantage Error: {data['Error Message']}")
                return {}
            elif "Information" in data:
                print(f"ℹ️  Alpha Vantage Info: {data['Information']}")
                return {}
            else:
                # Single stock response
                symbol = data.get('Symbol', tickers[0] if tickers else 'UNKNOWN')
                results[symbol] = data
        elif isinstance(data, list):
            # Multiple stocks response
            for item in data:
                if isinstance(item, dict) and 'Symbol' in item:
                    results[item['Symbol']] = item
        
        print(f"✅ Bulk API returned data for {len(results)} stocks")
        return results
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error in bulk fetch: {e}")
        return {}
    except Exception as e:
        print(f"❌ Unexpected error in bulk fetch: {e}")
        return {}

def get_yahoo_finance_fundamentals(ticker: str) -> Optional[dict]:
    """
    Fetch fundamental data from Yahoo Finance using yfinance library.
    This is used as a backup when Alpha Vantage fails or hits rate limits.
    
    Args:
        ticker: Stock symbol
        
    Returns:
        Dict with fundamental data or None if failed
    """
    try:
        print(f"🔄 Fetching {ticker} from Yahoo Finance (backup)...")
        
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or len(info) < 5:
            print(f"⚠️  No data available for {ticker} on Yahoo Finance")
            return None
        
        # Map Yahoo Finance fields to our expected format
        market_cap = info.get('marketCap', 0)
        ebitda = info.get('ebitda', 0)
        trailing_eps = info.get('trailingEps', 0)
        revenue = info.get('totalRevenue', 0)
        name = info.get('longName', ticker)
        roe = info.get('returnOnEquity', 0)
        
        # Convert to percentage if needed
        if roe and roe > 1:
            roe = roe / 100
        
        mapped_data = {
            'Symbol': ticker,
            'Name': name,
            'MarketCapitalization': str(market_cap) if market_cap else '0',
            'EBITDA': str(ebitda) if ebitda else '0',
            'EPS': str(trailing_eps) if trailing_eps else '0',
            'RevenueTTM': str(revenue) if revenue else '0',
            'ReturnOnEquityTTM': str(roe) if roe else '0',
            'Sector': info.get('sector', 'Unknown'),
            'Industry': info.get('industry', 'Unknown')
        }
        
        print(f"✅ Got Yahoo Finance data for {ticker}: {name}")
        return mapped_data
        
    except Exception as e:
        print(f"❌ Error fetching {ticker} from Yahoo Finance: {e}")
        return None

def get_fundamentals_with_fallback(ticker: str, api_key: str) -> Optional[dict]:
    """
    Get fundamental data with Alpha Vantage primary and Yahoo Finance fallback.
    
    Args:
        ticker: Stock symbol
        api_key: Alpha Vantage API key
        
    Returns:
        Fundamental data dict or None
    """
    # Try Alpha Vantage first
    alpha_data = get_alpha_vantage_fundamentals(ticker, api_key)
    
    if alpha_data:
        return alpha_data
    
    # Fall back to Yahoo Finance
    print(f"🔄 Alpha Vantage failed for {ticker}, trying Yahoo Finance...")
    yahoo_data = get_yahoo_finance_fundamentals(ticker)
    
    return yahoo_data
