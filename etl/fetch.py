"""Data-fetching utilities for external APIs."""
import requests, os, time, logging

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
