#!/usr/bin/env python3
"""
Empirically-calibrated transaction cost model for US equities.

This module implements a practical transaction cost model based on:
1. Academic research on bid-ask spreads
2. Empirical observations from institutional trading
3. Market microstructure patterns
4. Realistic cost estimates for backtesting
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import warnings
warnings.filterwarnings('ignore')

class RealisticTransactionCosts:
    """Empirically-calibrated transaction cost model"""
    
    def __init__(self):
        # Empirical cost parameters based on institutional trading data
        # Updated to reflect realistic trading costs observed in practice
        self.base_costs = {
            'large_cap': 0.0020,    # 20 bps (>$10B market cap) - realistic for S&P 100
            'mid_cap': 0.0035,      # 35 bps ($2B-$10B market cap)  
            'small_cap': 0.0065,    # 65 bps ($500M-$2B market cap)
            'micro_cap': 0.0120     # 120 bps (<$500M market cap)
        }
        
        # Additional cost factors
        self.volatility_multiplier = 2.0   # High vol stocks cost more
        self.volume_discount = 0.5          # High volume stocks cost less
        self.min_cost = 0.0015             # 15 bps minimum (very liquid)
        self.max_cost = 0.04               # 400 bps maximum (very illiquid)
        
    def get_market_cap_tier(self, market_cap: float) -> str:
        """Classify stock by market cap tier"""
        if market_cap >= 10e9:         # $10B+
            return 'large_cap'
        elif market_cap >= 2e9:        # $2B-$10B
            return 'mid_cap'
        elif market_cap >= 500e6:      # $500M-$2B
            return 'small_cap'
        else:                          # <$500M
            return 'micro_cap'
    
    def get_stock_info(self, ticker: str) -> Optional[Dict]:
        """Get basic stock information for cost calculation"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get recent price data for volatility
            hist = stock.history(period="3mo", auto_adjust=True)
            if hist.empty:
                return None
                
            # Calculate key metrics
            market_cap = info.get('marketCap', 0)
            avg_volume = hist['Volume'].tail(20).mean()
            avg_dollar_volume = avg_volume * hist['Close'].tail(20).mean()
            
            # Calculate volatility (annualized)
            returns = np.log(hist['Close'] / hist['Close'].shift(1))
            volatility = returns.std() * np.sqrt(252)
            
            current_price = hist['Close'].iloc[-1]
            
            return {
                'ticker': ticker,
                'market_cap': market_cap,
                'current_price': current_price,
                'avg_volume': avg_volume,
                'avg_dollar_volume': avg_dollar_volume,
                'volatility': volatility,
                'data_points': len(hist)
            }
            
        except Exception as e:
            print(f"Error getting info for {ticker}: {e}")
            return None
    
    def calculate_base_cost(self, stock_info: Dict) -> float:
        """Calculate base transaction cost based on stock characteristics"""
        
        # Get market cap tier
        market_cap = stock_info['market_cap']
        tier = self.get_market_cap_tier(market_cap)
        base_cost = self.base_costs[tier]
        
        # Volatility adjustment
        volatility = stock_info.get('volatility', 0.2)  # Default 20% vol
        vol_adjustment = 1 + (volatility - 0.2) * self.volatility_multiplier
        vol_adjustment = max(0.5, min(3.0, vol_adjustment))  # Cap between 0.5x and 3x
        
        # Volume/liquidity adjustment
        avg_dollar_volume = stock_info.get('avg_dollar_volume', 1e6)  # Default $1M ADV
        
        # Liquidity buckets - adjusted for more realistic cost impact
        if avg_dollar_volume >= 100e6:      # $100M+ ADV (very liquid)
            liquidity_factor = 0.9
        elif avg_dollar_volume >= 20e6:     # $20M-$100M ADV (liquid)
            liquidity_factor = 1.0
        elif avg_dollar_volume >= 5e6:      # $5M-$20M ADV (medium)
            liquidity_factor = 1.2
        elif avg_dollar_volume >= 1e6:      # $1M-$5M ADV (low)
            liquidity_factor = 1.8
        else:                              # <$1M ADV (very low)
            liquidity_factor = 3.0
        
        # Calculate final cost
        adjusted_cost = base_cost * vol_adjustment * liquidity_factor
        
        
        # Apply bounds
        final_cost = np.clip(adjusted_cost, self.min_cost, self.max_cost)
        
        return final_cost
    
    def calculate_market_impact(self, stock_info: Dict, trade_size_usd: float) -> float:
        """Calculate market impact based on trade size relative to ADV"""
        
        avg_dollar_volume = stock_info.get('avg_dollar_volume', 1e6)
        participation_rate = trade_size_usd / avg_dollar_volume
        
        # Market impact model: sqrt(participation_rate) * volatility * coefficient
        volatility = stock_info.get('volatility', 0.2)
        impact_coefficient = 0.3  # Empirical parameter
        
        market_impact = impact_coefficient * np.sqrt(participation_rate) * volatility
        
        # Apply reasonable bounds
        market_impact = np.clip(market_impact, 0, 0.05)  # Max 500 bps impact
        
        return market_impact
    
    def estimate_total_cost(self, ticker: str, trade_size_usd: float) -> Dict:
        """Estimate total transaction cost for a stock trade"""
        
        # Get stock information
        stock_info = self.get_stock_info(ticker)
        
        if stock_info is None:
            # Use default costs for missing data
            return {
                'ticker': ticker,
                'base_cost': 0.003,      # 30 bps default
                'market_impact': 0.001,  # 10 bps default
                'total_cost': 0.004,     # 40 bps total
                'data_available': False,
                'market_cap_tier': 'unknown',
                'capacity_feasible': True
            }
        
        # Calculate cost components
        base_cost = self.calculate_base_cost(stock_info)
        market_impact = self.calculate_market_impact(stock_info, trade_size_usd)
        total_cost = base_cost + market_impact
        
        # Check capacity constraints (max 10% of ADV)
        adv = stock_info.get('avg_dollar_volume', 1e6)
        capacity_feasible = (trade_size_usd / adv) <= 0.10
        
        return {
            'ticker': ticker,
            'base_cost': base_cost,
            'market_impact': market_impact,
            'total_cost': total_cost,
            'data_available': True,
            'market_cap': stock_info['market_cap'],
            'market_cap_tier': self.get_market_cap_tier(stock_info['market_cap']),
            'avg_dollar_volume': stock_info.get('avg_dollar_volume', 0),
            'volatility': stock_info.get('volatility', 0),
            'participation_rate': trade_size_usd / stock_info.get('avg_dollar_volume', 1e6),
            'capacity_feasible': capacity_feasible,
            'current_price': stock_info.get('current_price', 0)
        }
    
    def estimate_portfolio_costs(self, tickers: List[str], portfolio_value: float) -> Dict:
        """Estimate transaction costs for entire portfolio"""
        
        position_size = portfolio_value / len(tickers)
        results = {}
        
        print(f"💰 Calculating realistic transaction costs...")
        print(f"📊 Portfolio value: ${portfolio_value:,.0f}")
        print(f"🎯 Position size: ${position_size:,.0f} per stock")
        
        valid_results = []
        
        for i, ticker in enumerate(tickers):
            if i % 10 == 0:
                print(f"   Progress: {i}/{len(tickers)} processed...")
            
            cost_data = self.estimate_total_cost(ticker, position_size)
            results[ticker] = cost_data
            
            if cost_data['data_available']:
                valid_results.append(cost_data)
        
        # Calculate summary statistics
        if valid_results:
            avg_base_cost = np.mean([r['base_cost'] for r in valid_results])
            avg_impact = np.mean([r['market_impact'] for r in valid_results])
            avg_total = np.mean([r['total_cost'] for r in valid_results])
            
            # Cost distribution by market cap
            large_cap_costs = [r['total_cost'] for r in valid_results if r['market_cap_tier'] == 'large_cap']
            mid_cap_costs = [r['total_cost'] for r in valid_results if r['market_cap_tier'] == 'mid_cap']
            small_cap_costs = [r['total_cost'] for r in valid_results if r['market_cap_tier'] == 'small_cap']
            
            print(f"\n📈 Portfolio Cost Analysis:")
            print(f"   💹 Average base cost: {avg_base_cost*10000:.1f} bps")
            print(f"   🎯 Average market impact: {avg_impact*10000:.1f} bps")
            print(f"   💰 Average total cost: {avg_total*10000:.1f} bps")
            print(f"   ✅ Stocks with data: {len(valid_results)}/{len(tickers)}")
            
            if large_cap_costs:
                print(f"   🏢 Large cap average: {np.mean(large_cap_costs)*10000:.1f} bps ({len(large_cap_costs)} stocks)")
            if mid_cap_costs:
                print(f"   🏬 Mid cap average: {np.mean(mid_cap_costs)*10000:.1f} bps ({len(mid_cap_costs)} stocks)")
            if small_cap_costs:
                print(f"   🏪 Small cap average: {np.mean(small_cap_costs)*10000:.1f} bps ({len(small_cap_costs)} stocks)")
            
            # Capacity warnings
            infeasible = [r for r in valid_results if not r['capacity_feasible']]
            if infeasible:
                print(f"   ⚠️  Capacity warnings: {len(infeasible)} stocks exceed 10% ADV")
                for stock in infeasible[:3]:  # Show first 3
                    print(f"      {stock['ticker']}: {stock['participation_rate']*100:.1f}% of ADV")
        
        return results

def test_realistic_costs():
    """Test the realistic transaction cost model"""
    
    model = RealisticTransactionCosts()
    
    # Test with diverse stock universe across market caps
    test_stocks = [
        'AAPL',   # Large cap, high volume ($3T+ market cap)
        'MSFT',   # Large cap, high volume ($3T+ market cap)
        'JNJ',    # Large cap, healthcare ($400B market cap)
        'RTX',    # Mid cap aerospace (~$150B market cap)
        'CAT',    # Mid cap industrial (~$170B market cap)
        'SBUX',   # Mid-to-large cap consumer (~$110B market cap)
    ]
    
    print("🧪 Testing Realistic Transaction Cost Model")
    print("=" * 60)
    
    # Individual stock analysis
    print(f"\n📊 Individual Stock Analysis:")
    for ticker in test_stocks[:3]:
        cost_data = model.estimate_total_cost(ticker, 200_000)  # $200k position
        
        print(f"\n{ticker}:")
        print(f"   Market Cap: ${cost_data.get('market_cap', 0)/1e9:.1f}B ({cost_data.get('market_cap_tier', 'unknown')})")
        print(f"   Base Cost: {cost_data['base_cost']*10000:.1f} bps")
        print(f"   Market Impact: {cost_data['market_impact']*10000:.1f} bps")
        print(f"   Total Cost: {cost_data['total_cost']*10000:.1f} bps")
        print(f"   ADV: ${cost_data.get('avg_dollar_volume', 0)/1e6:.1f}M")
        print(f"   Volatility: {cost_data.get('volatility', 0)*100:.1f}%")
        print(f"   Participation: {cost_data.get('participation_rate', 0)*100:.1f}%")
    
    # Portfolio analysis
    print(f"\n📈 Portfolio Analysis (${1_000_000:,} portfolio):")
    portfolio_costs = model.estimate_portfolio_costs(test_stocks, 1_000_000)
    
    return portfolio_costs

if __name__ == "__main__":
    test_realistic_costs()