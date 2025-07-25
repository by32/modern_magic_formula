#!/usr/bin/env python3
"""
Direct SEC EDGAR API point-in-time fundamentals extractor

This module bypasses complex XBRL parsing libraries and uses the SEC's
structured JSON API to extract financial data with point-in-time accuracy.
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import json
import os

class SECDirectFundamentals:
    """Extract point-in-time fundamental data directly from SEC API"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Modern Magic Formula Research contact@example.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov'
        }
        self.rate_limit_delay = 0.1  # SEC allows 10 requests per second
        self.ticker_to_cik_cache = {}
        
    def get_ticker_to_cik_mapping(self) -> Dict[str, str]:
        """Get ticker to CIK mapping from SEC"""
        
        if self.ticker_to_cik_cache:
            return self.ticker_to_cik_cache
            
        try:
            time.sleep(self.rate_limit_delay)
            url = "https://www.sec.gov/files/company_tickers.json"
            # Update headers for this specific request
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
                        
                print(f"✅ Loaded {len(self.ticker_to_cik_cache)} ticker-to-CIK mappings")
                return self.ticker_to_cik_cache
                
            else:
                print(f"❌ Failed to get ticker mappings: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Error getting ticker mappings: {e}")
            return {}
    
    def get_company_facts(self, ticker: str) -> Optional[Dict]:
        """
        Get all company facts for a ticker from SEC CompanyFacts API
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with company facts or None if not found
        """
        # Get CIK for ticker
        ticker_mapping = self.get_ticker_to_cik_mapping()
        cik = ticker_mapping.get(ticker.upper())
        
        if not cik:
            print(f"❌ CIK not found for ticker {ticker}")
            return None
            
        try:
            time.sleep(self.rate_limit_delay)
            url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get company facts for {ticker}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting company facts for {ticker}: {e}")
            return None
    
    def extract_fact_value(self, facts_dict: Dict, concept: str, as_of_date: datetime) -> Optional[Tuple[float, str, str]]:
        """
        Extract the most recent value for a concept as of a specific date
        
        Args:
            facts_dict: Company facts dictionary from SEC API
            concept: The accounting concept to look for
            as_of_date: Point-in-time date
            
        Returns:
            Tuple of (value, filing_date, form_type) or None if not found
        """
        try:
            # Look in US-GAAP taxonomy first
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
                # Take first available unit if USD not available
                values_list = list(units.values())[0]
                
            if not values_list:
                return None
                
            # Filter to values filed before as_of_date and sort by end date
            valid_values = []
            
            for item in values_list:
                # Check if this value was filed before our as_of_date
                filed_date_str = item.get('filed', '')
                if filed_date_str:
                    filed_date = datetime.strptime(filed_date_str, '%Y-%m-%d')
                    if filed_date <= as_of_date:
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
            
            # Return the most recent value
            best_value = valid_values[0]
            return (
                float(best_value['value']),
                best_value['filed_date'],
                best_value['form']
            )
            
        except Exception as e:
            print(f"Error extracting {concept}: {e}")
            return None
    
    def get_point_in_time_fundamentals(self, ticker: str, as_of_date: datetime) -> Optional[Dict]:
        """
        Get point-in-time fundamental data for a ticker
        
        Args:
            ticker: Stock ticker symbol
            as_of_date: Date for point-in-time analysis
            
        Returns:
            Dict with financial data or None if not available
        """
        
        print(f"🔄 Processing {ticker} as of {as_of_date.date()}")
        
        # Get company facts from SEC API
        company_facts = self.get_company_facts(ticker)
        
        if not company_facts:
            return None
            
        # Define the financial concepts we need for Magic Formula
        concepts_mapping = {
            # Revenue concepts
            'revenue': ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet'],
            
            # Operating income / EBIT concepts  
            'operating_income': ['OperatingIncomeLoss', 'IncomeLossFromContinuingOperations'],
            
            # Net income
            'net_income': ['NetIncomeLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic'],
            
            # Assets
            'total_assets': ['Assets'],
            'current_assets': ['AssetsCurrent'],
            
            # Liabilities  
            'current_liabilities': ['LiabilitiesCurrent'],
            
            # Debt
            'long_term_debt': ['LongTermDebt', 'LongTermDebtNoncurrent'],
            
            # Cash
            'cash_and_equivalents': ['CashAndCashEquivalentsAtCarryingValue', 'CashCashEquivalentsAndShortTermInvestments'],
            
            # PPE
            'ppe': ['PropertyPlantAndEquipmentNet'],
            
            # Equity
            'stockholders_equity': ['StockholdersEquity', 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'],
            
            # Cash flow
            'operating_cash_flow': ['NetCashProvidedByUsedInOperatingActivities'],
            'capex': ['PaymentsToAcquirePropertyPlantAndEquipment']
        }
        
        # Extract all financial metrics
        financial_data = {'ticker': ticker, 'as_of_date': as_of_date}
        
        for metric_name, concept_list in concepts_mapping.items():
            value_found = None
            
            # Try each concept until we find a value
            for concept in concept_list:
                result = self.extract_fact_value(company_facts, concept, as_of_date)
                if result:
                    value, filed_date, form_type = result
                    value_found = {
                        'value': value,
                        'concept': concept,
                        'filed_date': filed_date,
                        'form_type': form_type
                    }
                    break
                    
            financial_data[metric_name] = value_found
        
        # Calculate derived metrics for Magic Formula
        self._calculate_magic_formula_metrics(financial_data)
        
        return financial_data
    
    def _calculate_magic_formula_metrics(self, financial_data: Dict):
        """Calculate Magic Formula specific metrics"""
        
        try:
            # Extract values safely
            revenue = self._get_value(financial_data, 'revenue')
            operating_income = self._get_value(financial_data, 'operating_income')
            total_assets = self._get_value(financial_data, 'total_assets')
            current_assets = self._get_value(financial_data, 'current_assets')
            current_liabilities = self._get_value(financial_data, 'current_liabilities')
            long_term_debt = self._get_value(financial_data, 'long_term_debt') or 0
            cash = self._get_value(financial_data, 'cash_and_equivalents') or 0
            ppe = self._get_value(financial_data, 'ppe')
            
            # Calculate Magic Formula components
            financial_data['ebit'] = operating_income  # EBIT approximation
            
            # Net Working Capital
            if current_assets and current_liabilities:
                financial_data['net_working_capital'] = current_assets - current_liabilities
            
            # Invested Capital (for ROC calculation)
            if financial_data.get('net_working_capital') and ppe:
                financial_data['invested_capital'] = financial_data['net_working_capital'] + ppe
            
            # Calculate market cap placeholder (will need price data)
            financial_data['market_cap'] = None  # Need to get from market data
            
            # Enterprise Value components
            financial_data['total_debt'] = long_term_debt
            financial_data['cash_and_cash_equivalents'] = cash
            
        except Exception as e:
            print(f"Error calculating Magic Formula metrics: {e}")
    
    def _get_value(self, financial_data: Dict, key: str) -> Optional[float]:
        """Safely extract numeric value from financial data"""
        item = financial_data.get(key)
        if item and isinstance(item, dict):
            return item.get('value')
        return None
    
    def get_historical_fundamentals_batch(self, tickers: List[str], as_of_date: datetime) -> pd.DataFrame:
        """
        Get point-in-time fundamentals for multiple tickers
        
        Args:
            tickers: List of ticker symbols
            as_of_date: Date for point-in-time analysis
            
        Returns:
            DataFrame with fundamental data for all tickers
        """
        results = []
        
        print(f"🔄 Processing {len(tickers)} tickers for date {as_of_date.date()}")
        
        for i, ticker in enumerate(tickers):
            if i % 10 == 0:
                print(f"   Progress: {i}/{len(tickers)} processed...")
                
            try:
                fundamentals = self.get_point_in_time_fundamentals(ticker, as_of_date)
                
                if fundamentals:
                    # Flatten the nested structure for DataFrame
                    flattened = {'ticker': ticker, 'as_of_date': as_of_date}
                    
                    for key, value in fundamentals.items():
                        if isinstance(value, dict) and 'value' in value:
                            flattened[f"{key}_value"] = value['value']
                            flattened[f"{key}_filed_date"] = value['filed_date']
                            flattened[f"{key}_form"] = value['form_type']
                        else:
                            flattened[key] = value
                            
                    results.append(flattened)
                else:
                    # Add record with missing data
                    results.append({
                        'ticker': ticker,
                        'as_of_date': as_of_date,
                        'error': 'No data available'
                    })
                    
            except Exception as e:
                print(f"⚠️  Error processing {ticker}: {e}")
                results.append({
                    'ticker': ticker,
                    'as_of_date': as_of_date,
                    'error': str(e)
                })
        
        print(f"✅ Completed processing {len(results)} tickers")
        return pd.DataFrame(results)

def test_sec_direct_extraction():
    """Test the direct SEC API fundamentals extractor"""
    
    extractor = SECDirectFundamentals()
    
    # Test with Apple for a specific date
    test_date = datetime(2023, 6, 30)  # End of Q2 2023
    
    print(f"Testing SEC direct extraction for AAPL as of {test_date}")
    
    fundamentals = extractor.get_point_in_time_fundamentals('AAPL', test_date)
    
    if fundamentals:
        print("\n📊 Extracted Financial Data:")
        for key, value in fundamentals.items():
            if isinstance(value, dict) and 'value' in value:
                print(f"   {key}: ${value['value']:,.0f} (filed: {value['filed_date']}, form: {value['form_type']})")
            elif key not in ['ticker', 'as_of_date']:
                print(f"   {key}: {value}")
    else:
        print("❌ No data extracted")

if __name__ == "__main__":
    test_sec_direct_extraction()