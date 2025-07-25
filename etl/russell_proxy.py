#!/usr/bin/env python3
"""
Russell 1000 Proxy Implementation

Since historical Russell 1000 constituents data requires expensive subscriptions,
this module implements a practical proxy approach:

1. Start with S&P 500 as core large-cap universe
2. Expand with additional mid-cap stocks based on market cap
3. Apply Russell-like selection criteria to reach ~1000 stocks
4. Track changes over time as companies grow/shrink

This approach provides a reasonable approximation for backtesting purposes
while acknowledging it won't match the exact Russell 1000 timing.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import requests
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')


class RussellProxyBuilder:
    """Build Russell 1000-like universe using free data sources"""
    
    def __init__(self):
        self.sp500_list = None
        self.market_cap_data = {}
        self.russell_proxy = None
        
    def get_sp500_constituents(self) -> pd.DataFrame:
        """Get current S&P 500 constituents from Wikipedia"""
        try:
            print("📊 Fetching S&P 500 constituents from Wikipedia...")
            
            # Wikipedia table of S&P 500 companies
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            tables = pd.read_html(url)
            
            # The first table contains the S&P 500 list
            sp500_df = tables[0].copy()
            
            # Clean up column names
            sp500_df.columns = ['ticker', 'company_name', 'gics_sector', 
                               'gics_sub_industry', 'headquarters', 'date_added', 
                               'cik', 'founded']
            
            # Clean ticker symbols (remove dots and special characters)
            sp500_df['ticker'] = sp500_df['ticker'].str.replace('.', '-')
            
            print(f"✅ Found {len(sp500_df)} S&P 500 companies")
            return sp500_df
            
        except Exception as e:
            print(f"❌ Error fetching S&P 500 data: {e}")
            return pd.DataFrame()
    
    def get_market_cap_data(self, tickers: List[str], 
                           batch_size: int = 20) -> Dict[str, float]:
        """Get market cap data for list of tickers"""
        
        market_caps = {}
        
        print(f"💰 Fetching market cap data for {len(tickers)} tickers...")
        
        # Process in batches to avoid overwhelming yfinance
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i + batch_size]
            
            if i % (batch_size * 2) == 0:
                print(f"   Progress: {i}/{len(tickers)} processed...")
            
            try:
                # Get batch data
                tickers_str = ' '.join(batch)
                data = yf.Tickers(tickers_str)
                
                for ticker in batch:
                    try:
                        info = data.tickers[ticker].info
                        market_cap = info.get('marketCap', 0)
                        
                        if market_cap and market_cap > 0:
                            market_caps[ticker] = market_cap
                        else:
                            # Try alternative field names
                            market_cap = info.get('marketCapitalization', 0)
                            if market_cap and market_cap > 0:
                                market_caps[ticker] = market_cap
                                
                    except Exception as e:
                        print(f"   ⚠️  Failed to get market cap for {ticker}: {e}")
                        continue
                        
            except Exception as e:
                print(f"   ⚠️  Batch error: {e}")
                continue
        
        print(f"✅ Retrieved market cap for {len(market_caps)} companies")
        return market_caps
    
    def get_additional_tickers(self, target_count: int = 1000, 
                              min_market_cap: float = 1e9) -> List[str]:
        """Get additional tickers beyond S&P 500 to reach target count"""
        
        print(f"🎯 Finding additional tickers to reach {target_count} companies...")
        
        # Comprehensive list of mid-cap and large-cap tickers likely in Russell 1000
        additional_candidates = [
            # Technology & Software
            'SNOW', 'PLTR', 'U', 'DDOG', 'CRWD', 'ZS', 'OKTA', 'NET', 'TEAM', 'WDAY',
            'NOW', 'SPLK', 'TWLO', 'ZM', 'DOCU', 'ESTC', 'MDB', 'VEEV', 'CRM',
            'ADBE', 'INTU', 'ORCL', 'VMW', 'ANSS', 'CDNS', 'SNPS', 'ADSK', 'FTNT',
            
            # Healthcare & Biotech  
            'MRNA', 'BNTX', 'REGN', 'VRTX', 'GILD', 'BIIB', 'ILMN', 'AMGN', 'CELG',
            'BMRN', 'ALNY', 'PTCT', 'RARE', 'BLUE', 'SAGE', 'ARWR', 'IONS', 'EXAS',
            'VEEV', 'TDOC', 'DXCM', 'ISRG', 'ALGN', 'HOLX', 'TECH', 'PODD',
            
            # Financial Services & Fintech
            'SOFI', 'AFRM', 'COIN', 'HOOD', 'SQ', 'PYPL', 'V', 'MA', 'AXP',
            'BX', 'KKR', 'APO', 'ARES', 'OWL', 'CG', 'TPG', 'BLUE', 'TROW',
            'SCHW', 'IBKR', 'NDAQ', 'ICE', 'CME', 'CBOE', 'MKTX',
            
            # Consumer & E-commerce
            'ABNB', 'UBER', 'LYFT', 'DASH', 'ROKU', 'SPOT', 'NFLX', 'DIS',
            'COST', 'HD', 'LOW', 'TJX', 'ROST', 'ULTA', 'LULU', 'NKE',
            'SBUX', 'MCD', 'CMG', 'QSR', 'YUM', 'DPZ', 'WING',
            
            # Energy & Utilities
            'FANG', 'OVV', 'DVN', 'COG', 'EQT', 'CNX', 'RRC', 'SM', 'MRO',
            'HES', 'APA', 'EOG', 'PXD', 'COP', 'XOM', 'CVX', 'SLB', 'HAL',
            'NEE', 'SO', 'DUK', 'AEP', 'EXC', 'XEL', 'ED', 'PPL',
            
            # Materials & Industrials
            'FCX', 'NEM', 'SCCO', 'MP', 'ALB', 'SQM', 'LIN', 'APD', 'ECL',
            'DOW', 'DD', 'LYB', 'CE', 'VMC', 'MLM', 'NUE', 'STLD',
            'BA', 'CAT', 'DE', 'MMM', 'HON', 'GE', 'RTX', 'LMT', 'NOC',
            
            # REITs & Real Estate
            'AMT', 'CCI', 'EQIX', 'DLR', 'PSA', 'EXR', 'AVB', 'EQR', 'UDR',
            'WELL', 'VTR', 'PEAK', 'O', 'STAG', 'PLD', 'EXR', 'CUBE',
            
            # Communication & Media
            'T', 'VZ', 'TMUS', 'CHTR', 'CMCSA', 'NFLX', 'DIS', 'WBD',
            'PARA', 'FOX', 'FOXA', 'NYT', 'SIRI',
            
            # Transportation
            'UPS', 'FDX', 'DAL', 'AAL', 'UAL', 'LUV', 'JBLU', 'ALK',
            'CSX', 'UNP', 'NSC', 'KSU', 'CNI', 'CP',
            
            # Retail & Consumer Staples
            'WMT', 'TGT', 'KR', 'WBA', 'CVS', 'PG', 'JNJ', 'KO', 'PEP',
            'CL', 'MDLZ', 'GIS', 'K', 'CPB', 'CAG', 'HSY', 'SJM',
            
            # Additional Growth/Mid-caps
            'ZI', 'BILL', 'COUP', 'GTLB', 'S', 'RBLX', 'RIVN', 'LCID',
            'NKLA', 'BLDE', 'ENPH', 'SEDG', 'RUN', 'NOVA', 'PLUG',
        ]
        
        # Add more systematic approach - get Russell ETF holdings
        try:
            print("   📈 Getting IWB (Russell 1000 ETF) holdings as reference...")
            iwb = yf.Ticker('IWB')
            
            # Try to get holdings - this is limited but gives us some reference
            info = iwb.info
            top_holdings = info.get('holdings', [])
            
            if top_holdings:
                for holding in top_holdings[:50]:  # Top 50 holdings
                    symbol = holding.get('symbol', '')
                    if symbol and symbol not in additional_candidates:
                        additional_candidates.append(symbol)
                        
        except Exception as e:
            print(f"   ⚠️  Could not get IWB holdings: {e}")
        
        # Add mid-cap ETF holdings for broader coverage
        try:
            print("   📈 Getting IJH (Mid-cap ETF) holdings...")
            ijh = yf.Ticker('IJH')
            info = ijh.info
            holdings = info.get('holdings', [])
            
            if holdings:
                for holding in holdings[:100]:  # Top 100 mid-cap holdings
                    symbol = holding.get('symbol', '')
                    if symbol and symbol not in additional_candidates:
                        additional_candidates.append(symbol)
                        
        except Exception as e:
            print(f"   ⚠️  Could not get IJH holdings: {e}")
        
        print(f"   📋 Identified {len(additional_candidates)} additional candidates")
        return additional_candidates
    
    def build_russell_proxy(self, target_date: str = None) -> pd.DataFrame:
        """Build Russell 1000 proxy universe"""
        
        target_date = target_date or datetime.now().strftime('%Y-%m-%d')
        print(f"🏗️  Building Russell 1000 proxy for date: {target_date}")
        
        # Step 1: Get S&P 500 as foundation
        sp500_df = self.get_sp500_constituents()
        if sp500_df.empty:
            raise ValueError("Could not fetch S&P 500 data")
        
        # Step 2: Get additional candidates
        additional_tickers = self.get_additional_tickers()
        
        # Combine all tickers
        all_tickers = list(sp500_df['ticker'].unique()) + additional_tickers
        all_tickers = list(set(all_tickers))  # Remove duplicates
        
        print(f"📊 Total candidate universe: {len(all_tickers)} tickers")
        
        # Step 3: Get market cap data for all candidates
        market_caps = self.get_market_cap_data(all_tickers)
        
        # Step 4: Create comprehensive dataset
        russell_proxy_data = []
        
        for ticker in market_caps:
            market_cap = market_caps[ticker]
            
            # Get company info
            is_sp500 = ticker in sp500_df['ticker'].values
            
            if is_sp500:
                sp500_row = sp500_df[sp500_df['ticker'] == ticker].iloc[0]
                company_name = sp500_row['company_name']
                sector = sp500_row['gics_sector']
            else:
                # Get basic info for non-S&P 500 companies
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    company_name = info.get('longName', ticker)
                    sector = info.get('sector', 'Unknown')
                except:
                    company_name = ticker
                    sector = 'Unknown'
            
            russell_proxy_data.append({
                'ticker': ticker,
                'company_name': company_name,
                'market_cap': market_cap,
                'sector': sector,
                'is_sp500': is_sp500,
                'market_cap_rank': 0,  # Will be filled after sorting
                'proxy_date': target_date
            })
        
        # Step 5: Create DataFrame and rank by market cap
        russell_proxy_df = pd.DataFrame(russell_proxy_data)
        russell_proxy_df = russell_proxy_df.sort_values('market_cap', ascending=False)
        russell_proxy_df['market_cap_rank'] = range(1, len(russell_proxy_df) + 1)
        
        # Step 6: Apply Russell 1000-like filters
        # - Top 1000 by market cap
        # - Minimum liquidity requirements (simplified)
        # - US-traded equities
        
        russell_1000_proxy = russell_proxy_df.head(1000).copy()
        
        print(f"🎯 Russell 1000 Proxy Summary:")
        print(f"   📊 Total companies: {len(russell_1000_proxy)}")
        print(f"   💰 Market cap range: ${russell_1000_proxy['market_cap'].min()/1e9:.1f}B - ${russell_1000_proxy['market_cap'].max()/1e9:.1f}B")
        print(f"   🏢 S&P 500 overlap: {russell_1000_proxy['is_sp500'].sum()}/500 ({russell_1000_proxy['is_sp500'].sum()/500*100:.1f}%)")
        
        # Sector breakdown
        sector_counts = russell_1000_proxy['sector'].value_counts()
        print(f"   📈 Top sectors:")
        for sector, count in sector_counts.head(5).items():
            print(f"      {sector}: {count} companies")
        
        self.russell_proxy = russell_1000_proxy
        return russell_1000_proxy
    
    def save_russell_proxy(self, filename: str = None):
        """Save Russell 1000 proxy to CSV"""
        
        if self.russell_proxy is None:
            raise ValueError("Must build Russell proxy first")
        
        filename = filename or f"data/russell_1000_proxy_{datetime.now().strftime('%Y%m%d')}.csv"
        
        self.russell_proxy.to_csv(filename, index=False)
        print(f"💾 Russell 1000 proxy saved to: {filename}")
        
        return filename

def test_russell_proxy_simple():
    """Test with smaller universe first"""
    
    print("🧪 Testing Russell 1000 Proxy Builder (Simple)")
    print("=" * 60)
    
    builder = RussellProxyBuilder()
    
    # Override additional tickers with smaller list for testing
    builder.get_additional_tickers = lambda target_count=1000, min_market_cap=1e9: [
        'SNOW', 'PLTR', 'UBER', 'ABNB', 'ROKU', 'MRNA', 'COIN', 'RIVN',
        'DASH', 'DDOG', 'CRWD', 'NET', 'ZM', 'DOCU', 'TEAM', 'FANG'
    ]
    
    try:
        # Build proxy
        russell_proxy = builder.build_russell_proxy()
        
        # Save results
        filename = builder.save_russell_proxy()
        
        # Display sample
        print(f"\n📊 Sample of Russell 1000 Proxy:")
        sample = russell_proxy.head(10)[['ticker', 'company_name', 'market_cap', 'sector', 'market_cap_rank']]
        sample['market_cap'] = sample['market_cap'].apply(lambda x: f"${x/1e9:.1f}B")
        print(sample.to_string(index=False))
        
        return russell_proxy
        
    except Exception as e:
        print(f"❌ Error building Russell proxy: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_russell_proxy():
    """Test the Russell 1000 proxy builder"""
    
    print("🧪 Testing Russell 1000 Proxy Builder")
    print("=" * 60)
    
    builder = RussellProxyBuilder()
    
    try:
        # Build proxy
        russell_proxy = builder.build_russell_proxy()
        
        # Save results
        filename = builder.save_russell_proxy()
        
        # Display sample
        print(f"\n📊 Sample of Russell 1000 Proxy:")
        sample = russell_proxy.head(10)[['ticker', 'company_name', 'market_cap', 'sector', 'market_cap_rank']]
        sample['market_cap'] = sample['market_cap'].apply(lambda x: f"${x/1e9:.1f}B")
        print(sample.to_string(index=False))
        
        return russell_proxy
        
    except Exception as e:
        print(f"❌ Error building Russell proxy: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_russell_proxy_simple()