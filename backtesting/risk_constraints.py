#!/usr/bin/env python3
"""
Risk Constraints Module for Modern Magic Formula

This module implements various risk constraints to ensure portfolio diversification
and risk management across key factors:

1. Beta constraints - Limit portfolio beta vs. market
2. Sector constraints - Maximum allocation per sector  
3. Size constraints - Balance across market cap segments
4. Concentration limits - Maximum position sizes

These constraints help prevent the Magic Formula from concentrating too heavily
in specific risk factors that could lead to poor performance.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class RiskConstraintManager:
    """Manage portfolio risk constraints for backtesting"""
    
    def __init__(self):
        self.sector_limits = {
            'Information Technology': 0.35,    # Max 35% in tech (reflects market reality)
            'Health Care': 0.25,               # Max 25% in healthcare
            'Financials': 0.25,                # Max 25% in financials
            'Consumer Discretionary': 0.20,    # Max 20% in consumer disc
            'Industrials': 0.20,               # Max 20% in industrials
            'Communication Services': 0.15,    # Max 15% in communications
            'Consumer Staples': 0.15,          # Max 15% in consumer staples
            'Energy': 0.15,                    # Max 15% in energy
            'Materials': 0.12,                 # Max 12% in materials
            'Real Estate': 0.12,               # Max 12% in real estate
            'Utilities': 0.10                  # Max 10% in utilities
        }
        
        self.size_limits = {
            'large_cap': (0.30, 0.70),    # 30-70% in large cap (>$50B)
            'mid_cap': (0.20, 0.50),      # 20-50% in mid cap ($5B-$50B)
            'small_cap': (0.05, 0.30)     # 5-30% in small cap ($1B-$5B)
        }
        
        self.beta_limits = (0.5, 1.5)        # Portfolio beta between 0.5-1.5
        self.max_position_size = 0.08         # Max 8% in any single stock
        self.min_position_count = 15          # Minimum 15 stocks in portfolio
        
    def get_stock_beta(self, ticker: str, days: int = 252) -> float:
        """Calculate stock beta vs. SPY over specified period"""
        try:
            # Get stock and market data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 50)  # Extra buffer
            
            stock = yf.Ticker(ticker)
            spy = yf.Ticker('SPY')
            
            stock_data = stock.history(start=start_date, end=end_date)
            spy_data = spy.history(start=start_date, end=end_date)
            
            if len(stock_data) < 100 or len(spy_data) < 100:
                return 1.0  # Default beta if insufficient data
            
            # Align dates and calculate returns
            common_dates = stock_data.index.intersection(spy_data.index)[-days:]
            
            if len(common_dates) < 100:
                return 1.0
                
            stock_prices = stock_data.loc[common_dates, 'Close']
            spy_prices = spy_data.loc[common_dates, 'Close']
            
            # Calculate daily returns
            stock_returns = stock_prices.pct_change().dropna()
            spy_returns = spy_prices.pct_change().dropna()
            
            # Calculate beta using covariance
            aligned_data = pd.DataFrame({
                'stock': stock_returns,
                'spy': spy_returns
            }).dropna()
            
            if len(aligned_data) < 50:
                return 1.0
                
            covariance = aligned_data['stock'].cov(aligned_data['spy'])
            spy_variance = aligned_data['spy'].var()
            
            beta = covariance / spy_variance if spy_variance > 0 else 1.0
            
            # Apply reasonable bounds
            beta = np.clip(beta, 0.1, 3.0)
            
            return float(beta)
            
        except Exception as e:
            print(f"   ⚠️  Error calculating beta for {ticker}: {e}")
            return 1.0  # Default beta
    
    def get_market_cap_segment(self, market_cap: float) -> str:
        """Classify stock by market cap segment"""
        if market_cap >= 50e9:         # $50B+
            return 'large_cap'
        elif market_cap >= 5e9:        # $5B-$50B
            return 'mid_cap'
        elif market_cap >= 1e9:        # $1B-$5B
            return 'small_cap'
        else:                          # <$1B
            return 'micro_cap'
    
    def enrich_portfolio_data(self, portfolio: pd.DataFrame) -> pd.DataFrame:
        """Add risk factor data to portfolio DataFrame"""
        
        enriched_portfolio = portfolio.copy()
        
        print(f"🔍 Enriching portfolio data with risk factors...")
        
        # Add columns for risk factors
        enriched_portfolio['beta'] = 1.0
        enriched_portfolio['market_cap_segment'] = 'unknown'
        
        for i, row in enriched_portfolio.iterrows():
            ticker = row['ticker']
            
            try:
                # Get beta
                beta = self.get_stock_beta(ticker)
                enriched_portfolio.at[i, 'beta'] = beta
                
                # Get market cap segment
                market_cap = row.get('market_cap', 0)
                if market_cap > 0:
                    segment = self.get_market_cap_segment(market_cap)
                    enriched_portfolio.at[i, 'market_cap_segment'] = segment
                
                if i % 10 == 0:
                    print(f"   Progress: {i}/{len(enriched_portfolio)} stocks processed...")
                    
            except Exception as e:
                print(f"   ⚠️  Error enriching {ticker}: {e}")
                continue
        
        print(f"✅ Portfolio enrichment complete")
        return enriched_portfolio
    
    def check_sector_constraints(self, portfolio: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Check if portfolio violates sector concentration limits"""
        
        violations = []
        
        if 'sector' not in portfolio.columns:
            return True, ['Missing sector data']
        
        # Calculate sector weights (assuming equal weighting)
        sector_counts = portfolio['sector'].value_counts()
        total_positions = len(portfolio)
        
        for sector, count in sector_counts.items():
            weight = count / total_positions
            limit = self.sector_limits.get(sector, 0.15)  # Default 15% limit
            
            if weight > limit:
                violations.append(f"{sector}: {weight:.1%} > {limit:.1%} limit")
        
        return len(violations) == 0, violations
    
    def check_size_constraints(self, portfolio: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Check if portfolio violates market cap segment limits"""
        
        violations = []
        
        if 'market_cap_segment' not in portfolio.columns:
            return True, ['Missing market cap segment data']
        
        # Calculate size weights
        size_counts = portfolio['market_cap_segment'].value_counts()
        total_positions = len(portfolio)
        
        for segment, (min_weight, max_weight) in self.size_limits.items():
            count = size_counts.get(segment, 0)
            weight = count / total_positions
            
            if weight < min_weight:
                violations.append(f"{segment}: {weight:.1%} < {min_weight:.1%} minimum")
            elif weight > max_weight:
                violations.append(f"{segment}: {weight:.1%} > {max_weight:.1%} maximum")
        
        return len(violations) == 0, violations
    
    def check_beta_constraints(self, portfolio: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Check if portfolio beta is within acceptable range"""
        
        violations = []
        
        if 'beta' not in portfolio.columns:
            return True, ['Missing beta data']
        
        # Calculate portfolio beta (equal weighted)
        portfolio_beta = portfolio['beta'].mean()
        
        min_beta, max_beta = self.beta_limits
        
        if portfolio_beta < min_beta:
            violations.append(f"Portfolio beta {portfolio_beta:.2f} < {min_beta:.2f} minimum")
        elif portfolio_beta > max_beta:
            violations.append(f"Portfolio beta {portfolio_beta:.2f} > {max_beta:.2f} maximum")
        
        return len(violations) == 0, violations
    
    def check_concentration_constraints(self, portfolio: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Check concentration limits"""
        
        violations = []
        
        # Check minimum number of positions
        if len(portfolio) < self.min_position_count:
            violations.append(f"Only {len(portfolio)} positions < {self.min_position_count} minimum")
        
        # Check maximum position size (equal weighting assumed)
        position_weight = 1.0 / len(portfolio) if len(portfolio) > 0 else 1.0
        
        if position_weight > self.max_position_size:
            violations.append(f"Position size {position_weight:.1%} > {self.max_position_size:.1%} maximum")
        
        return len(violations) == 0, violations
    
    def apply_risk_constraints(self, ranked_portfolio: pd.DataFrame, 
                              target_size: int = 50) -> pd.DataFrame:
        """Apply risk constraints to create final portfolio"""
        
        print(f"🛡️  Applying risk constraints to portfolio...")
        print(f"   Input: {len(ranked_portfolio)} ranked stocks")
        print(f"   Target: {target_size} final positions")
        
        # Enrich with risk factor data
        enriched_portfolio = self.enrich_portfolio_data(ranked_portfolio.head(target_size * 2))  # Use 2x buffer
        
        # Start with top-ranked stocks and iteratively build portfolio
        final_portfolio = []
        sector_weights = {}
        size_weights = {}
        beta_sum = 0.0
        
        for i, row in enriched_portfolio.iterrows():
            if len(final_portfolio) >= target_size:
                break
                
            ticker = row['ticker']
            sector = row.get('sector', 'Unknown')
            size_segment = row.get('market_cap_segment', 'unknown')
            beta = row.get('beta', 1.0)
            
            # Calculate weights if we add this stock
            new_portfolio_size = len(final_portfolio) + 1
            new_position_weight = 1.0 / new_portfolio_size
            
            # Check sector constraint (only enforce after minimum portfolio size)
            sector_count = sector_weights.get(sector, 0) + 1
            new_sector_weight = sector_count / new_portfolio_size
            sector_limit = self.sector_limits.get(sector, 0.15)
            
            # Allow flexibility for first 15 stocks, then enforce constraints
            if new_portfolio_size > 15 and new_sector_weight > sector_limit:
                print(f"   🚫 Skipping {ticker}: sector {sector} would exceed {sector_limit:.1%} limit")
                continue
            
            # Check size constraint (only enforce after minimum portfolio size)
            size_count = size_weights.get(size_segment, 0) + 1
            new_size_weight = size_count / new_portfolio_size
            
            if new_portfolio_size > 15 and size_segment in self.size_limits:
                _, max_size_weight = self.size_limits[size_segment]
                if new_size_weight > max_size_weight:
                    print(f"   🚫 Skipping {ticker}: {size_segment} would exceed {max_size_weight:.1%} limit")
                    continue
            
            # Check beta constraint
            new_portfolio_beta = (beta_sum + beta) / new_portfolio_size
            min_beta, max_beta = self.beta_limits
            
            if new_portfolio_beta > max_beta and len(final_portfolio) > 10:  # Allow flexibility initially
                print(f"   🚫 Skipping {ticker}: portfolio beta would exceed {max_beta:.2f}")
                continue
            
            # Add stock to portfolio
            final_portfolio.append(row)
            sector_weights[sector] = sector_weights.get(sector, 0) + 1
            size_weights[size_segment] = size_weights.get(size_segment, 0) + 1
            beta_sum += beta
            
            if len(final_portfolio) % 10 == 0:
                print(f"   ✅ Added {len(final_portfolio)} stocks to constrained portfolio")
        
        # Convert back to DataFrame
        constrained_portfolio = pd.DataFrame(final_portfolio)
        
        # Report final portfolio characteristics
        print(f"\n📊 Risk-Constrained Portfolio Summary:")
        print(f"   📈 Portfolio size: {len(constrained_portfolio)} stocks")
        
        if len(constrained_portfolio) > 0:
            portfolio_beta = constrained_portfolio['beta'].mean()
            print(f"   📊 Portfolio beta: {portfolio_beta:.2f}")
            
            # Sector breakdown
            sector_dist = constrained_portfolio['sector'].value_counts()
            print(f"   🏢 Sector distribution:")
            for sector, count in sector_dist.head(5).items():
                weight = count / len(constrained_portfolio)
                print(f"      {sector}: {count} stocks ({weight:.1%})")
            
            # Size breakdown
            size_dist = constrained_portfolio['market_cap_segment'].value_counts()
            print(f"   📏 Size distribution:")
            for segment, count in size_dist.items():
                weight = count / len(constrained_portfolio)
                print(f"      {segment}: {count} stocks ({weight:.1%})")
        
        return constrained_portfolio
    
    def validate_portfolio_constraints(self, portfolio: pd.DataFrame) -> Dict[str, any]:
        """Validate all portfolio constraints and return summary"""
        
        validation_results = {
            'sector_valid': True,
            'size_valid': True,
            'beta_valid': True,
            'concentration_valid': True,
            'violations': [],
            'portfolio_beta': None,
            'sector_weights': {},
            'size_weights': {}
        }
        
        if len(portfolio) == 0:
            validation_results['violations'].append('Empty portfolio')
            return validation_results
        
        # Check each constraint type
        sector_valid, sector_violations = self.check_sector_constraints(portfolio)
        size_valid, size_violations = self.check_size_constraints(portfolio)
        beta_valid, beta_violations = self.check_beta_constraints(portfolio)
        concentration_valid, concentration_violations = self.check_concentration_constraints(portfolio)
        
        # Update results
        validation_results['sector_valid'] = sector_valid
        validation_results['size_valid'] = size_valid
        validation_results['beta_valid'] = beta_valid
        validation_results['concentration_valid'] = concentration_valid
        
        validation_results['violations'].extend(sector_violations)
        validation_results['violations'].extend(size_violations)
        validation_results['violations'].extend(beta_violations)
        validation_results['violations'].extend(concentration_violations)
        
        # Calculate portfolio characteristics
        if 'beta' in portfolio.columns:
            validation_results['portfolio_beta'] = portfolio['beta'].mean()
        
        if 'sector' in portfolio.columns:
            sector_counts = portfolio['sector'].value_counts()
            total = len(portfolio)
            validation_results['sector_weights'] = {
                sector: count / total for sector, count in sector_counts.items()
            }
        
        if 'market_cap_segment' in portfolio.columns:
            size_counts = portfolio['market_cap_segment'].value_counts()
            total = len(portfolio)
            validation_results['size_weights'] = {
                segment: count / total for segment, count in size_counts.items()
            }
        
        return validation_results


def test_risk_constraints():
    """Test risk constraint management"""
    
    print("🧪 Testing Risk Constraint Manager")
    print("=" * 60)
    
    # Load sample portfolio data
    try:
        sample_data = pd.read_csv('data/russell_1000_proxy_20250724.csv')
        print(f"📊 Loaded {len(sample_data)} stocks from Russell proxy")
        
        # Create sample ranked portfolio (top 100 by mock ranking)
        sample_data['mock_rank'] = range(1, len(sample_data) + 1)
        top_100 = sample_data.head(100).copy()
        
        print(f"🎯 Testing with top {len(top_100)} stocks")
        
        # Initialize risk manager
        risk_manager = RiskConstraintManager()
        
        # Apply constraints
        constrained_portfolio = risk_manager.apply_risk_constraints(top_100, target_size=30)
        
        # Validate final portfolio
        validation = risk_manager.validate_portfolio_constraints(constrained_portfolio)
        
        print(f"\n✅ Risk Constraint Test Results:")
        print(f"   Valid Portfolio: {all([validation['sector_valid'], validation['size_valid'], validation['beta_valid'], validation['concentration_valid']])}")
        
        if validation['violations']:
            print(f"   ⚠️  Violations found:")
            for violation in validation['violations']:
                print(f"      {violation}")
        else:
            print(f"   ✅ No constraint violations")
        
        return constrained_portfolio
        
    except Exception as e:
        print(f"❌ Error testing risk constraints: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_risk_constraints()