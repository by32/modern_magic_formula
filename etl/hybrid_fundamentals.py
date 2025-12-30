#!/usr/bin/env python3
"""
Hybrid fundamentals fetcher combining SEC point-in-time data with current market data.

This module provides:
1. Point-in-time fundamentals from SEC EDGAR API (eliminates look-ahead bias)
2. Current market data from Yahoo Finance (prices, market cap, momentum)
3. Seamless integration with existing ETL pipeline
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Tuple

import pandas as pd
import requests
import yfinance as yf

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
        self.offline_mode = False
        self.consecutive_failures = 0
        self.max_consecutive_failures = 10  # Only go offline after 10 consecutive failures
        self.cached_results = self._load_cached_results()
        self.cached_lookup = {
            row.get('ticker'): row for row in self.cached_results if row.get('ticker')
        }
        self.used_cached_results = False

    def _load_cached_results(self) -> List[Dict]:
        """Load the most recent screening output as an offline fallback."""

        fallback_path = Path(__file__).resolve().parent.parent / "data" / "latest_screening_hybrid.csv"
        if not fallback_path.exists():
            return []

        try:
            df = pd.read_csv(fallback_path)
            records: List[Dict] = df.to_dict(orient="records")
            return records
        except Exception as exc:  # pragma: no cover - defensive guardrail
            print(f"⚠️  Unable to load cached screening dataset: {exc}")
            return []

    def has_cached_results(self) -> bool:
        """Return True if a cached screening dataset is available."""

        return bool(self.cached_results)

    def get_cached_screening_results(self) -> List[Dict]:
        """Return a copy of the cached screening output."""

        if not self.cached_results:
            print("⚠️  No cached screening dataset available for fallback.")
            return []

        self.used_cached_results = True
        # Return shallow copies so downstream mutations do not affect cache
        return [dict(row) for row in self.cached_results]

    def _get_cached_hybrid(self, ticker: str) -> Optional[Dict]:
        """Return cached hybrid fundamentals for a ticker if available."""

        cached_row = self.cached_lookup.get(ticker)
        if not cached_row:
            return None

        data = dict(cached_row)
        data.setdefault('_data_sources', {})
        data['_data_sources'].update({
            'sec_available': False,
            'yahoo_available': False,
            'market_data_available': False,
            'as_of_date': self.as_of_date.isoformat(),
            'sec_filing_dates': {}
        })
        return data
        
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

            print(f"⚠️  Failed to get ticker mappings: {response.status_code}")
            # Only go offline for rate limiting or server errors on critical endpoint
            if response.status_code in {403, 429, 500, 502, 503}:
                self.offline_mode = True
            return {}

        except requests.exceptions.ConnectionError as e:
            print(f"⚠️  Network error getting ticker mappings: {e}")
            self.offline_mode = True
            return {}
        except Exception as e:
            print(f"⚠️  Error getting ticker mappings: {e}")
            # Don't go offline for other errors - might be temporary
            return {}
    
    def get_sec_fundamentals(self, ticker: str) -> Optional[Dict]:
        """
        Get point-in-time fundamentals from SEC EDGAR API

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dict with SEC fundamental data or None if not available
        """
        if self.offline_mode:
            return None

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
                self.consecutive_failures = 0  # Reset on success
                return self._extract_sec_metrics(company_facts)

            # 404 = ticker not found (normal for some stocks) - don't go offline
            if response.status_code == 404:
                return None

            # Rate limiting or server errors - track consecutive failures
            if response.status_code in {403, 429, 500, 502, 503}:
                self.consecutive_failures += 1
                if self.consecutive_failures >= self.max_consecutive_failures:
                    print(f"⚠️  {self.consecutive_failures} consecutive SEC failures - entering offline mode")
                    self.offline_mode = True
            return None

        except requests.exceptions.ConnectionError:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.max_consecutive_failures:
                print(f"⚠️  {self.consecutive_failures} consecutive network failures - entering offline mode")
                self.offline_mode = True
            return None
        except Exception:
            # Don't go offline for parsing errors etc
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

        if self.offline_mode:
            return None

        try:
            stock = yf.Ticker(ticker)

            # Use fast_info for quick market data (it doesn't have sector/name)
            fast_info = getattr(stock, "fast_info", None) or {}

            # Get full info for metadata like sector and company name
            # These fields are not available in fast_info
            full_info = stock.info or {}

            market_data = {
                'market_cap': fast_info.get('market_cap') or fast_info.get('marketCap') or full_info.get('marketCap', 0),
                'current_price': fast_info.get('last_price')
                or fast_info.get('currentPrice')
                or full_info.get('currentPrice')
                or full_info.get('regularMarketPrice', 0),
                'shares_outstanding': fast_info.get('shares_outstanding')
                or fast_info.get('sharesOutstanding')
                or full_info.get('sharesOutstanding', 0),
                # These metadata fields only exist in full .info, not fast_info
                'sector': full_info.get('sector', 'Unknown'),
                'industry': full_info.get('industry', 'Unknown'),
                'company_name': full_info.get('longName') or full_info.get('shortName') or ticker
            }

            # Best effort attempt at momentum using local price history
            try:
                history = stock.history(period="6mo")
                if not history.empty:
                    start_price = float(history["Close"].iloc[0])
                    end_price = float(history["Close"].iloc[-1])
                    if start_price > 0:
                        momentum = (end_price - start_price) / start_price
                    else:
                        momentum = None
                    market_data['price_data'] = {
                        'momentum_6m': momentum,
                        'price_vs_52w_high': 0,
                        'current_price': market_data['current_price'],
                    }
            except Exception:
                # Ignore price history issues – treated as unavailable in offline mode
                pass

            self.consecutive_failures = 0  # Reset on success
            return market_data

        except requests.exceptions.ConnectionError:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.max_consecutive_failures:
                print(f"⚠️  {self.consecutive_failures} consecutive Yahoo failures - entering offline mode")
                self.offline_mode = True
            return None
        except Exception:
            # Don't go offline for individual ticker errors (e.g., delisted stocks)
            return None
    
    def get_hybrid_fundamentals(self, ticker: str) -> Optional[Dict]:
        """
        Get comprehensive fundamental data combining SEC and Yahoo sources
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with combined fundamental data in format compatible with existing pipeline
        """
        
        # Offline fallback – reuse cached screening result if available
        if self.offline_mode and self.has_cached_results():
            cached_data = self._get_cached_hybrid(ticker)
            if cached_data:
                return cached_data

        # Get SEC point-in-time fundamentals
        sec_data = self.get_sec_fundamentals(ticker)

        if self.offline_mode and self.has_cached_results():
            cached_data = self._get_cached_hybrid(ticker)
            if cached_data:
                return cached_data

        # Get Yahoo market data
        market_data = self.get_yahoo_market_data(ticker)
        yahoo_data: Dict = {}

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
            if self.offline_mode:
                break

            if i % 25 == 0:  # Progress every 25 tickers
                print(f"   Progress: {i}/{len(tickers)} processed...")

            try:
                fundamentals = self.get_hybrid_fundamentals(ticker)
                if fundamentals:
                    results[ticker] = fundamentals

            except Exception as e:
                print(f"⚠️  Error processing {ticker}: {e}")
                continue

        if self.offline_mode and not results:
            print("📴 Offline mode detected during hybrid fetch – skipping remote lookups.")

        print(f"✅ Successfully processed {len(results)}/{len(tickers)} tickers")

        # Display data source statistics
        sec_count = sum(
            1 for data in results.values()
            if data.get('_data_sources', {}).get('sec_available', False)
        )
        yahoo_count = sum(
            1 for data in results.values()
            if data.get('_data_sources', {}).get('yahoo_available', False)
        )

        print("📊 Data sources used:")
        total = len(results) or 1
        print(f"   🏛️  SEC EDGAR: {sec_count}/{len(results)} tickers ({sec_count/total*100:.1f}%)")
        print(f"   🌐 Yahoo Finance: {yahoo_count}/{len(results)} tickers ({yahoo_count/total*100:.1f}%)")

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