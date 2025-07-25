#!/usr/bin/env python3
"""
Point-in-time fundamentals extractor using edgartools and SEC EDGAR API

This module provides functionality to extract historical financial data
with proper point-in-time accuracy, eliminating look-ahead bias.
"""

import os
import edgar
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import json
from edgar import Company, set_identity

# Set SEC compliance user agent
USER_AGENT = "Modern Magic Formula Research contact@example.com"
os.environ['SEC_EDGAR_USER_AGENT'] = USER_AGENT
set_identity(USER_AGENT)

class PointInTimeFundamentals:
    """Extract point-in-time fundamental data from SEC EDGAR"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': USER_AGENT,
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov'
        }
        self.rate_limit_delay = 0.1  # SEC allows 10 requests per second
        
    def get_company_filings(self, ticker: str, as_of_date: datetime) -> Optional[Dict]:
        """
        Get company filings available as of a specific date
        
        Args:
            ticker: Stock ticker symbol
            as_of_date: Date for point-in-time analysis
            
        Returns:
            Dict with filing information or None if not found
        """
        try:
            # Use edgartools for company lookup
            company = Company(ticker)
            
            # Get all 10-K and 10-Q filings
            filings_10k = company.get_filings(form='10-K')
            filings_10q = company.get_filings(form='10-Q')
            
            # Find the most recent filing before as_of_date
            available_filings = []
            
            # Process 10-K filings
            for filing in filings_10k:
                filing_date = filing.filing_date  # This is a datetime.date object
                if filing_date <= as_of_date.date():  # Convert datetime to date for comparison
                    available_filings.append({
                        'form': '10-K',
                        'date': filing_date,
                        'filing': filing,
                        'period_type': 'annual'
                    })
            
            # Process 10-Q filings
            for filing in filings_10q:
                filing_date = filing.filing_date  # This is a datetime.date object
                if filing_date <= as_of_date.date():  # Convert datetime to date for comparison
                    available_filings.append({
                        'form': '10-Q',
                        'date': filing_date,
                        'filing': filing,
                        'period_type': 'quarterly'
                    })
            
            # Sort by date and return most recent
            if available_filings:
                available_filings.sort(key=lambda x: x['date'], reverse=True)
                return available_filings[0]
            
            return None
            
        except Exception as e:
            print(f"Error getting filings for {ticker}: {e}")
            return None
    
    def extract_financial_data(self, filing_info: Dict) -> Optional[Dict]:
        """
        Extract financial statement data from a filing using XBRL
        
        Args:
            filing_info: Filing information from get_company_filings
            
        Returns:
            Dict with financial metrics or None if extraction fails
        """
        try:
            filing = filing_info['filing']
            
            # Get XBRL data
            xbrl = filing.xbrl()
            
            # Extract key metrics for Magic Formula
            financial_data = {}
            
            # Get financial statements from XBRL
            statements = xbrl.statements
            
            # Find income statement (operations)
            income_stmt = xbrl.find_statement('CONSOLIDATEDSTATEMENTSOFOPERATIONS')
            if income_stmt:
                # Extract revenue and operating income
                financial_data['revenue'] = self._extract_xbrl_value(income_stmt, ['Revenue', 'NetSales', 'TotalRevenues'])
                financial_data['operating_income'] = self._extract_xbrl_value(income_stmt, ['OperatingIncomeLoss', 'OperatingIncome'])
                financial_data['net_income'] = self._extract_xbrl_value(income_stmt, ['NetIncomeLoss', 'NetIncome'])
                financial_data['interest_expense'] = self._extract_xbrl_value(income_stmt, ['InterestExpense'])
                
                # EBIT is typically operating income
                financial_data['ebit'] = financial_data['operating_income']
            
            # Find balance sheet
            balance_sheet = xbrl.find_statement('CONSOLIDATEDBALANCESHEETS')
            if balance_sheet:
                financial_data['total_assets'] = self._extract_xbrl_value(balance_sheet, ['Assets', 'AssetsCurrent', 'TotalAssets'])
                financial_data['current_assets'] = self._extract_xbrl_value(balance_sheet, ['AssetsCurrent', 'CurrentAssets'])
                financial_data['current_liabilities'] = self._extract_xbrl_value(balance_sheet, ['LiabilitiesCurrent', 'CurrentLiabilities'])
                financial_data['total_debt'] = self._extract_xbrl_value(balance_sheet, ['LongTermDebt', 'DebtLongTerm'])
                financial_data['cash_and_equivalents'] = self._extract_xbrl_value(balance_sheet, ['CashAndCashEquivalentsAtCarryingValue', 'CashCashEquivalentsAndShortTermInvestments'])
                financial_data['ppe'] = self._extract_xbrl_value(balance_sheet, ['PropertyPlantAndEquipmentNet', 'PropertyPlantAndEquipment'])
                financial_data['total_equity'] = self._extract_xbrl_value(balance_sheet, ['StockholdersEquity', 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'])
            
            # Find cash flow statement
            cash_flow_stmt = xbrl.find_statement('CONSOLIDATEDSTATEMENTSOFCASHFLOWS')
            if cash_flow_stmt:
                financial_data['operating_cash_flow'] = self._extract_xbrl_value(cash_flow_stmt, ['NetCashProvidedByUsedInOperatingActivities', 'NetCashProvidedByOperatingActivities'])
                financial_data['capex'] = self._extract_xbrl_value(cash_flow_stmt, ['PaymentsToAcquirePropertyPlantAndEquipment', 'CapitalExpenditures'])
            
            # Add metadata
            financial_data['filing_date'] = filing_info['date']
            financial_data['form_type'] = filing_info['form']
            financial_data['period_type'] = filing_info['period_type']
            
            return financial_data
            
        except Exception as e:
            print(f"Error extracting financial data: {e}")
            return None
    
    def _extract_xbrl_value(self, statement, field_names: List[str]) -> Optional[float]:
        """
        Extract a financial metric from XBRL statement
        
        Args:
            statement: XBRL statement object
            field_names: List of possible field names to try
            
        Returns:
            Float value or None if not found
        """
        if not statement:
            return None
            
        try:
            # Get the most recent period data (usually the first row)
            df = statement.df
            if df is not None and not df.empty:
                for field_name in field_names:
                    if field_name in df.columns:
                        # Get the most recent value (first row, first column with this name)
                        value = df[field_name].iloc[0] if not df[field_name].empty else None
                        if value is not None and pd.notna(value):
                            return float(value)
                            
        except Exception as e:
            print(f"Error extracting XBRL value: {e}")
            
        return None
    
    def _safe_extract(self, statement, field_names: List[str]) -> Optional[float]:
        """
        Safely extract a financial metric from a statement (legacy method)
        
        Args:
            statement: Financial statement object
            field_names: List of possible field names to try
            
        Returns:
            Float value or None if not found
        """
        for field_name in field_names:
            try:
                if hasattr(statement, field_name):
                    value = getattr(statement, field_name)
                    if value is not None:
                        return float(value)
                        
                # Try as dictionary access
                if isinstance(statement, dict) and field_name in statement:
                    value = statement[field_name]
                    if value is not None:
                        return float(value)
                        
            except (ValueError, TypeError, AttributeError):
                continue
                
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
        # Add rate limiting
        time.sleep(self.rate_limit_delay)
        
        # Get available filings as of the date
        filing_info = self.get_company_filings(ticker, as_of_date)
        
        if not filing_info:
            print(f"No filings found for {ticker} as of {as_of_date}")
            return None
            
        # Extract financial data
        financial_data = self.extract_financial_data(filing_info)
        
        if financial_data:
            print(f"✅ {ticker}: Found {filing_info['form']} filed on {filing_info['date']}")
            
        return financial_data
        
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
        
        print(f"🔄 Processing {len(tickers)} tickers for date {as_of_date}")
        
        for i, ticker in enumerate(tickers):
            if i % 10 == 0:
                print(f"   Progress: {i}/{len(tickers)} processed...")
                
            try:
                fundamentals = self.get_point_in_time_fundamentals(ticker, as_of_date)
                
                if fundamentals:
                    fundamentals['ticker'] = ticker
                    results.append(fundamentals)
                else:
                    # Add record with missing data
                    results.append({
                        'ticker': ticker,
                        'filing_date': None,
                        'form_type': None,
                        'error': 'No data available'
                    })
                    
            except Exception as e:
                print(f"⚠️  Error processing {ticker}: {e}")
                results.append({
                    'ticker': ticker,
                    'error': str(e)
                })
        
        print(f"✅ Completed processing {len(results)} tickers")
        return pd.DataFrame(results)

def test_point_in_time_extraction():
    """Test the point-in-time fundamentals extraction"""
    
    extractor = PointInTimeFundamentals()
    
    # Test with Apple for a specific date
    test_date = datetime(2023, 6, 30)  # End of Q2 2023
    
    print(f"Testing point-in-time extraction for AAPL as of {test_date}")
    
    fundamentals = extractor.get_point_in_time_fundamentals('AAPL', test_date)
    
    if fundamentals:
        print("\n📊 Extracted Financial Data:")
        for key, value in fundamentals.items():
            if isinstance(value, (int, float)) and value is not None:
                print(f"   {key}: ${value:,.0f}")
            else:
                print(f"   {key}: {value}")
    else:
        print("❌ No data extracted")

if __name__ == "__main__":
    test_point_in_time_extraction()