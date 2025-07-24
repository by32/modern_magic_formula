"""Data-fetching utilities for external APIs."""
import requests, os, time, logging
import yfinance as yf
from datetime import datetime, timedelta
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
        
        # Get additional financial data from cash flow statement if available
        try:
            # Try to get cash flow statement data
            cash_flow = stock.cashflow
            if not cash_flow.empty:
                # Get most recent year's operating cash flow
                operating_cf = cash_flow.loc['Operating Cash Flow'].iloc[0] if 'Operating Cash Flow' in cash_flow.index else 0
                capex = cash_flow.loc['Capital Expenditures'].iloc[0] if 'Capital Expenditures' in cash_flow.index else 0
                
                # CapEx is usually negative in the statement
                if capex > 0:
                    capex = -capex
            else:
                operating_cf = 0
                capex = 0
        except:
            operating_cf = 0
            capex = 0
        
        # Get additional data from financials
        try:
            financials = stock.financials
            if not financials.empty:
                net_income = financials.loc['Net Income'].iloc[0] if 'Net Income' in financials.index else info.get('netIncomeToCommon', 0)
            else:
                net_income = info.get('netIncomeToCommon', 0)
        except:
            net_income = info.get('netIncomeToCommon', 0)
        
        # Get additional balance sheet data
        try:
            balance_sheet = stock.balance_sheet
            if not balance_sheet.empty:
                total_debt = balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_sheet.index else 0
                total_assets = balance_sheet.loc['Total Assets'].iloc[0] if 'Total Assets' in balance_sheet.index else 0
                shareholders_equity = balance_sheet.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in balance_sheet.index else 0
                current_assets = balance_sheet.loc['Current Assets'].iloc[0] if 'Current Assets' in balance_sheet.index else 0
                current_liabilities = balance_sheet.loc['Current Liabilities'].iloc[0] if 'Current Liabilities' in balance_sheet.index else 0
            else:
                total_debt = 0
                total_assets = 0
                shareholders_equity = 0
                current_assets = 0
                current_liabilities = 0
        except:
            total_debt = 0
            total_assets = 0
            shareholders_equity = 0
            current_assets = 0
            current_liabilities = 0
        
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
            'NetIncomeTTM': str(net_income) if net_income else '0',
            'OperatingCashflowTTM': str(operating_cf) if operating_cf else '0',
            'CapitalExpendituresTTM': str(capex) if capex else '0',
            'TotalDebt': str(total_debt) if total_debt else '0',
            'TotalAssets': str(total_assets) if total_assets else '0',
            'TotalShareholderEquity': str(shareholders_equity) if shareholders_equity else '0',
            'TotalCurrentAssets': str(current_assets) if current_assets else '0',
            'TotalCurrentLiabilities': str(current_liabilities) if current_liabilities else '0',
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

def get_6_month_price_data(ticker: str) -> Optional[Dict[str, float]]:
    """
    Fetch 6-month historical price data for momentum analysis.
    
    Args:
        ticker: Stock symbol
        
    Returns:
        Dict with current_price, price_6m_ago, and momentum_6m
    """
    try:
        print(f"📈 Fetching 6-month price data for {ticker}...")
        
        # Get 7 months of data to ensure we have enough history
        end_date = datetime.now()
        start_date = end_date - timedelta(days=210)  # ~7 months
        
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date)
        
        if hist.empty or len(hist) < 120:  # Need at least ~4 months of data
            print(f"⚠️  Insufficient price history for {ticker}")
            return None
        
        # Get current price (most recent close)
        current_price = float(hist['Close'].iloc[-1])
        
        # Get price from approximately 6 months ago
        # Use index position instead of exact date to handle weekends/holidays
        six_months_ago_idx = max(0, len(hist) - 130)  # ~6 months ago (130 trading days)
        price_6m_ago = float(hist['Close'].iloc[six_months_ago_idx])
        
        # Calculate 6-month momentum (percentage return)
        momentum_6m = (current_price - price_6m_ago) / price_6m_ago
        
        # Also get some additional price metrics
        price_52w_high = float(hist['High'].max())
        price_52w_low = float(hist['Low'].min())
        
        result = {
            'current_price': current_price,
            'price_6m_ago': price_6m_ago,
            'momentum_6m': momentum_6m,
            'price_52w_high': price_52w_high,
            'price_52w_low': price_52w_low,
            'price_vs_52w_high': (current_price - price_52w_high) / price_52w_high,
        }
        
        print(f"✅ {ticker}: 6M momentum = {momentum_6m*100:.1f}% (${price_6m_ago:.2f} → ${current_price:.2f})")
        return result
        
    except Exception as e:
        print(f"❌ Error fetching price data for {ticker}: {e}")
        return None

def get_alpha_vantage_price_data(ticker: str, api_key: str) -> Optional[Dict[str, float]]:
    """
    Fetch historical price data from Alpha Vantage for momentum analysis.
    This is an alternative to Yahoo Finance for price data.
    
    Args:
        ticker: Stock symbol
        api_key: Alpha Vantage API key
        
    Returns:
        Dict with price data and momentum calculation
    """
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "outputsize": "full",  # Get full history
            "apikey": api_key
        }
        
        print(f"📈 Fetching Alpha Vantage price data for {ticker}...")
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        
        data = r.json()
        
        # Check for errors
        if "Error Message" in data:
            print(f"❌ Alpha Vantage Error: {data['Error Message']}")
            return None
        elif "Note" in data:
            print(f"⚠️  Alpha Vantage Rate Limit: {data['Note']}")
            return None
        
        time_series = data.get("Time Series (Daily)", {})
        if not time_series:
            print(f"⚠️  No price data available for {ticker}")
            return None
        
        # Sort dates and get recent data
        dates = sorted(time_series.keys(), reverse=True)
        if len(dates) < 130:  # Need at least ~6 months
            print(f"⚠️  Insufficient price history for {ticker}")
            return None
        
        # Current price (most recent)
        current_date = dates[0]
        current_price = float(time_series[current_date]["4. close"])
        
        # Price from ~6 months ago (130 trading days)
        six_months_date = dates[min(130, len(dates)-1)]
        price_6m_ago = float(time_series[six_months_date]["4. close"])
        
        # Calculate momentum
        momentum_6m = (current_price - price_6m_ago) / price_6m_ago
        
        result = {
            'current_price': current_price,
            'price_6m_ago': price_6m_ago,
            'momentum_6m': momentum_6m,
        }
        
        print(f"✅ {ticker}: 6M momentum = {momentum_6m*100:.1f}% (Alpha Vantage)")
        return result
        
    except Exception as e:
        print(f"❌ Error fetching Alpha Vantage price data for {ticker}: {e}")
        return None
