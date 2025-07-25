#!/usr/bin/env python3
"""
Hybrid fundamentals fetcher combining SEC point-in-time data with current market data.

This module provides:
1. Point-in-time fundamentals from SEC EDGAR API (eliminates look-ahead bias)
2. Current market data from Yahoo Finance (prices, market cap, momentum)
3. Seamless integration with existing ETL pipeline
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import json
import yfinance as yf
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.fetch import get_yahoo_finance_fundamentals, get_6_month_price_data

class HybridFundamentals:
    """Hybrid data fetcher combining SEC fundamentals with Yahoo market data"""
    
    def __init__(self, as_of_date: Optional[datetime] = None):
        """
        Initialize hybrid fundamentals fetcher
        
        Args:
            as_of_date: Point-in-time date for SEC data. If None, uses current date.
        """
        self.as_of_date = as_of_date or datetime.now()
        self.headers = {
            'User-Agent': 'Modern Magic Formula Research contact@example.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov'
        }
        self.rate_limit_delay = 0.1  # SEC allows 10 requests per second
        self.ticker_to_cik_cache = {}
        
    def get_ticker_to_cik_mapping(self) -> Dict[str, str]:
        """Get ticker to CIK mapping from SEC (cached)"""
        
        if self.ticker_to_cik_cache:
            return self.ticker_to_cik_cache
            
        try:
            time.sleep(self.rate_limit_delay)
            url = "https://www.sec.gov/files/company_tickers.json"
            headers = {
                'User-Agent': 'Modern Magic Formula Research contact@example.com',
                'Accept': 'application/json'
            }
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Convert to ticker -> CIK mapping
                for key, company_info in data.items():
                    ticker = company_info.get('ticker', '').upper()
                    cik = f"{company_info.get('cik_str', 0):010d}"  # Pad to 10 digits
                    
                    if ticker and cik != '0000000000':
                        self.ticker_to_cik_cache[ticker] = cik
                        
                return self.ticker_to_cik_cache
                
            else:
                print(f"⚠️  Failed to get ticker mappings: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"⚠️  Error getting ticker mappings: {e}")
            return {}
    
    def get_sec_fundamentals(self, ticker: str) -> Optional[Dict]:
        """
        Get point-in-time fundamentals from SEC EDGAR API
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with SEC fundamental data or None if not available
        """
        # Get CIK for ticker
        ticker_mapping = self.get_ticker_to_cik_mapping()
        cik = ticker_mapping.get(ticker.upper())
        
        if not cik:
            return None
            
        try:
            time.sleep(self.rate_limit_delay)
            url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                company_facts = response.json()
                return self._extract_sec_metrics(company_facts)
            else:
                return None
                
        except Exception as e:
            return None
    
    def _extract_sec_metrics(self, company_facts: Dict) -> Dict:
        """Extract relevant financial metrics from SEC company facts"""
        
        # Define the financial concepts we need
        concepts_mapping = {
            'revenue': ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet'],
            'operating_income': ['OperatingIncomeLoss', 'IncomeLossFromContinuingOperations'],
            'net_income': ['NetIncomeLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic'],
            'total_assets': ['Assets'],
            'current_assets': ['AssetsCurrent'],
            'current_liabilities': ['LiabilitiesCurrent'],
            'long_term_debt': ['LongTermDebt', 'LongTermDebtNoncurrent'],
            'cash_and_equivalents': ['CashAndCashEquivalentsAtCarryingValue', 'CashCashEquivalentsAndShortTermInvestments'],
            'ppe': ['PropertyPlantAndEquipmentNet'],
            'stockholders_equity': ['StockholdersEquity', 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'],
            'operating_cash_flow': ['NetCashProvidedByUsedInOperatingActivities'],
            'capex': ['PaymentsToAcquirePropertyPlantAndEquipment'],
            'total_debt': ['DebtCurrent', 'LongTermDebt'],
            'shares_outstanding': ['CommonStockSharesOutstanding', 'WeightedAverageNumberOfSharesOutstandingBasic']
        }
        
        extracted_data = {}
        
        for metric_name, concept_list in concepts_mapping.items():
            value_found = None
            
            for concept in concept_list:
                result = self._extract_fact_value(company_facts, concept)
                if result:
                    value, filed_date, form_type = result
                    value_found = {
                        'value': value,
                        'concept': concept,
                        'filed_date': filed_date,
                        'form_type': form_type
                    }
                    break
                    
            extracted_data[metric_name] = value_found
        
        return extracted_data
    
    def _extract_fact_value(self, facts_dict: Dict, concept: str) -> Optional[Tuple[float, str, str]]:
        """Extract the most recent value for a concept as of as_of_date"""
        
        try:
            us_gaap = facts_dict.get('facts', {}).get('us-gaap', {})
            
            if concept not in us_gaap:
                return None
                
            concept_data = us_gaap[concept]
            units = concept_data.get('units', {})
            
            # Prefer USD units for financial data
            values_list = None
            if 'USD' in units:
                values_list = units['USD']
            elif units:
                values_list = list(units.values())[0]
                
            if not values_list:
                return None
                
            # Filter to values filed before as_of_date
            valid_values = []
            
            for item in values_list:
                filed_date_str = item.get('filed', '')
                if filed_date_str:
                    filed_date = datetime.strptime(filed_date_str, '%Y-%m-%d')
                    if filed_date <= self.as_of_date:
                        valid_values.append({
                            'value': item.get('val'),
                            'end_date': item.get('end', ''),
                            'filed_date': filed_date_str,
                            'form': item.get('form', ''),
                            'item': item
                        })
            
            if not valid_values:
                return None
                
            # Sort by end date (most recent first)
            valid_values.sort(key=lambda x: x['end_date'], reverse=True)
            
            best_value = valid_values[0]
            return (
                float(best_value['value']),
                best_value['filed_date'],
                best_value['form']
            )
            
        except Exception:
            return None
    
    def get_yahoo_market_data(self, ticker: str) -> Optional[Dict]:
        """Get current market data from Yahoo Finance"""
        
        try:
            # Get current market data
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get 6-month price data for momentum analysis
            price_data = get_6_month_price_data(ticker)
            
            market_data = {
                'market_cap': info.get('marketCap', 0),
                'current_price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                'shares_outstanding': info.get('sharesOutstanding', 0),
                'price_data': price_data,
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'company_name': info.get('longName', info.get('shortName', ticker))
            }
            
            return market_data
            
        except Exception as e:
            return None
    
    def get_hybrid_fundamentals(self, ticker: str) -> Optional[Dict]:
        """
        Get comprehensive fundamental data combining SEC and Yahoo sources
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with combined fundamental data in format compatible with existing pipeline
        """
        
        # Get SEC point-in-time fundamentals
        sec_data = self.get_sec_fundamentals(ticker)
        
        # Get Yahoo market data
        yahoo_data = get_yahoo_finance_fundamentals(ticker)
        market_data = self.get_yahoo_market_data(ticker)
        
        # If we have no data sources, return None
        if not sec_data and not yahoo_data:
            return None
        
        # Create hybrid data structure compatible with existing pipeline
        hybrid_data = {}
        
        # Helper function to safely get values
        def get_sec_value(key: str, default=0) -> float:
            item = sec_data.get(key) if sec_data else None
            if item and isinstance(item, dict):
                return item.get('value', default)
            return default
        
        def get_yahoo_value(key: str, default=0) -> float:
            if yahoo_data and key in yahoo_data:
                value = yahoo_data[key]
                if value not in ['None', 'N/A', '', None]:
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        pass
            return default
        
        def get_market_value(key: str, default=0) -> float:
            if market_data and key in market_data:
                return market_data[key] or default
            return default
        
        # Prioritize SEC data for fundamentals, Yahoo for market data
        hybrid_data.update({
            # Core identifiers
            'Name': get_market_value('company_name', ticker),
            'Sector': get_market_value('sector', 'Unknown'),
            
            # Market data (from Yahoo - current)
            'MarketCapitalization': get_market_value('market_cap', get_yahoo_value('MarketCapitalization')),
            'SharesOutstanding': get_market_value('shares_outstanding', get_yahoo_value('SharesOutstanding')),
            
            # Revenue (prefer SEC point-in-time)
            'RevenueTTM': get_sec_value('revenue', get_yahoo_value('RevenueTTM')),
            
            # Profitability (prefer SEC point-in-time)
            'NetIncomeTTM': get_sec_value('net_income', get_yahoo_value('NetIncomeTTM')),
            'OperatingCashflowTTM': get_sec_value('operating_cash_flow', get_yahoo_value('OperatingCashflowTTM')),
            
            # Use operating income as EBIT proxy (SEC point-in-time)
            'EBIT': get_sec_value('operating_income', get_yahoo_value('EBITDA', 0) * 0.8),  # Rough EBITDA to EBIT conversion
            'EBITDA': get_yahoo_value('EBITDA', get_sec_value('operating_income', 0) * 1.25),  # Rough EBIT to EBITDA conversion
            
            # Balance sheet (prefer SEC point-in-time)
            'TotalAssets': get_sec_value('total_assets', get_yahoo_value('TotalAssets')),
            'TotalCurrentAssets': get_sec_value('current_assets', get_yahoo_value('TotalCurrentAssets')),
            'TotalCurrentLiabilities': get_sec_value('current_liabilities', get_yahoo_value('TotalCurrentLiabilities')),
            'TotalDebt': get_sec_value('total_debt', get_yahoo_value('TotalDebt')),
            'CashAndCashEquivalentsAtCarryingValue': get_sec_value('cash_and_equivalents', get_yahoo_value('CashAndCashEquivalentsAtCarryingValue')),
            'PropertyPlantEquipment': get_sec_value('ppe', get_yahoo_value('PropertyPlantEquipment')),
            'StockholdersEquity': get_sec_value('stockholders_equity', get_yahoo_value('StockholdersEquity')),
            
            # Cash flow (prefer SEC point-in-time)
            'CapitalExpenditures': get_sec_value('capex', get_yahoo_value('CapitalExpenditures')),
            
            # Calculated ratios (use Yahoo if available, otherwise calculate from SEC data)
            'ReturnOnEquityTTM': get_yahoo_value('ReturnOnEquityTTM'),
            'ReturnOnAssetsTTM': get_yahoo_value('ReturnOnAssetsTTM'),
            'CurrentRatio': get_yahoo_value('CurrentRatio'),
            'PERatio': get_yahoo_value('PERatio'),
            'EPS': get_yahoo_value('EPS'),
            'GrossProfitMargin': get_yahoo_value('GrossProfitMargin'),
            
            # Data provenance metadata
            '_data_sources': {
                'sec_available': sec_data is not None,
                'yahoo_available': yahoo_data is not None,
                'market_data_available': market_data is not None,
                'as_of_date': self.as_of_date.isoformat(),
                'sec_filing_dates': self._get_filing_dates(sec_data) if sec_data else {}
            }
        })
        
        # Add price data for momentum analysis
        if market_data and market_data.get('price_data'):
            hybrid_data['_price_data'] = market_data['price_data']
        
        return hybrid_data
    
    def _get_filing_dates(self, sec_data: Dict) -> Dict:
        """Extract filing dates from SEC data for metadata"""
        filing_dates = {}
        
        if not sec_data:
            return filing_dates
            
        for key, value in sec_data.items():
            if isinstance(value, dict) and 'filed_date' in value:
                filing_dates[key] = {
                    'filed_date': value['filed_date'],
                    'form_type': value.get('form_type', 'Unknown')
                }
        
        return filing_dates
    
    def get_batch_fundamentals(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Get hybrid fundamentals for multiple tickers
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Dict mapping ticker to fundamental data
        """
        results = {}
        
        print(f"🔄 Fetching hybrid fundamentals for {len(tickers)} tickers...")
        print(f"📅 Using point-in-time date: {self.as_of_date.date()}")
        
        for i, ticker in enumerate(tickers):
            if i % 25 == 0:  # Progress every 25 tickers
                print(f"   Progress: {i}/{len(tickers)} processed...")
            
            try:
                fundamentals = self.get_hybrid_fundamentals(ticker)
                if fundamentals:
                    results[ticker] = fundamentals
                    
            except Exception as e:
                print(f"⚠️  Error processing {ticker}: {e}")
                continue
        
        print(f"✅ Successfully processed {len(results)}/{len(tickers)} tickers")
        
        # Display data source statistics
        sec_count = sum(1 for data in results.values() if data.get('_data_sources', {}).get('sec_available', False))
        yahoo_count = sum(1 for data in results.values() if data.get('_data_sources', {}).get('yahoo_available', False))
        
        print(f"📊 Data sources used:")
        print(f"   🏛️  SEC EDGAR: {sec_count}/{len(results)} tickers ({sec_count/len(results)*100:.1f}%)")
        print(f"   🌐 Yahoo Finance: {yahoo_count}/{len(results)} tickers ({yahoo_count/len(results)*100:.1f}%)")
        
        return results

def test_hybrid_fundamentals():
    """Test the hybrid fundamentals approach"""
    
    # Test with a specific point-in-time date
    test_date = datetime(2023, 6, 30)
    
    fetcher = HybridFundamentals(as_of_date=test_date)
    
    # Test with Apple
    print(f"Testing hybrid fundamentals for AAPL as of {test_date.date()}")
    
    result = fetcher.get_hybrid_fundamentals('AAPL')
    
    if result:
        print(f"\n📊 Hybrid Data for AAPL:")
        print(f"   Company: {result.get('Name', 'N/A')}")
        print(f"   Market Cap: ${result.get('MarketCapitalization', 0):,.0f}")
        print(f"   Revenue TTM: ${result.get('RevenueTTM', 0):,.0f}")
        print(f"   Net Income TTM: ${result.get('NetIncomeTTM', 0):,.0f}")
        print(f"   Total Assets: ${result.get('TotalAssets', 0):,.0f}")
        
        # Show data sources
        sources = result.get('_data_sources', {})
        print(f"\n📋 Data Sources:")
        print(f"   SEC EDGAR: {'✅' if sources.get('sec_available') else '❌'}")
        print(f"   Yahoo Finance: {'✅' if sources.get('yahoo_available') else '❌'}")
        print(f"   Market Data: {'✅' if sources.get('market_data_available') else '❌'}")
        
        # Show SEC filing dates
        filing_dates = sources.get('sec_filing_dates', {})
        if filing_dates:
            print(f"   SEC Filing Dates:")
            for metric, info in list(filing_dates.items())[:5]:  # Show first 5
                print(f"     {metric}: {info['filed_date']} ({info['form_type']})")
    
    else:
        print("❌ No hybrid data retrieved")

if __name__ == "__main__":
    test_hybrid_fundamentals()