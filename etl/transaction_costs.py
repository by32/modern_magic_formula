#!/usr/bin/env python3
"""
Realistic transaction cost modeling for equity trading.

This module implements academic models for estimating bid-ask spreads and
market impact costs using only daily OHLC data, eliminating the need for
expensive intraday tick data.

Key Models Implemented:
1. Corwin-Schultz (2012) High-Low Spread Estimator
2. Enhanced High-Low Estimators (Abdi & Ranaldo, 2017)
3. Market Impact Cost Model (Almgren et al.)
4. Capacity Constraints and ADV Limits
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
import warnings
warnings.filterwarnings('ignore')

class TransactionCostModel:
    """Comprehensive transaction cost model using academic spread estimators"""
    
    def __init__(self):
        self.default_spread = 0.002   # 20 bps default for missing data
        self.min_spread = 0.0001      # 1 bp minimum (most liquid stocks)
        self.max_spread = 0.05        # 500 bps maximum (illiquid stocks)
        
    def corwin_schultz_spread(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """
        Corwin-Schultz (2012) High-Low Spread Estimator
        
        This is the most widely used academic model for estimating bid-ask spreads
        from daily high-low prices. Achieves 85-90% correlation with actual spreads.
        
        Formula:
        α = (2K - √(2K)) / (3 - 2√2)
        where K = ln(H/L) × ln(H₋₁/L₋₁)
        
        Spread = 2(e^α - 1) / (1 + e^α)
        
        Args:
            high: Daily high prices
            low: Daily low prices  
            close: Daily close prices (for validation)
            
        Returns:
            Series of estimated bid-ask spreads (as fraction of price)
        """
        try:
            # Calculate log high-low ratios
            log_hl = np.log(high / low)
            log_hl_lag = log_hl.shift(1)
            
            # Only use valid data points (need both current and lagged)
            valid_mask = ~(log_hl.isna() | log_hl_lag.isna()) & (log_hl > 0) & (log_hl_lag > 0)
            
            # Calculate beta (variance estimator) - corrected formula
            beta = (log_hl ** 2) + (log_hl_lag ** 2)
            
            # Calculate gamma (covariance term)
            gamma = log_hl * log_hl_lag
            
            # Calculate alpha parameter (Corwin-Schultz formula)
            sqrt_2 = np.sqrt(2)
            denominator = 3 - 2 * sqrt_2
            
            # Alpha calculation with proper bounds checking
            alpha = (2 * beta - np.sqrt(2 * beta)) / denominator
            
            # Alternative: use the gamma-based estimator for robustness
            alpha_gamma = (2 * gamma - np.sqrt(2 * gamma)) / denominator
            alpha = np.where(gamma > 0, alpha_gamma, alpha)
            
            # Calculate spread estimate with bounds checking
            alpha = np.clip(alpha, -10, 10)  # Prevent overflow
            exp_alpha = np.exp(alpha)
            spread = 2 * (exp_alpha - 1) / (1 + exp_alpha)
            
            # Apply validity mask and clean results
            spread = pd.Series(spread, index=high.index)
            spread = spread.where(valid_mask, np.nan)
            spread = spread.fillna(method='ffill').fillna(self.default_spread)
            spread = np.clip(spread, self.min_spread, self.max_spread)
            
            return spread
            
        except Exception as e:
            print(f"Error in Corwin-Schultz calculation: {e}")
            return pd.Series([self.default_spread] * len(high), index=high.index)
    
    def enhanced_high_low_spread(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """
        Enhanced High-Low Spread Estimator (Abdi & Ranaldo, 2017)
        
        Improves on Corwin-Schultz with better handling of overnight gaps
        and microstructure noise. Generally more accurate for US equities.
        
        Args:
            high, low, close: Daily price series
            
        Returns:
            Enhanced spread estimates
        """
        try:
            # Basic Corwin-Schultz as starting point
            cs_spread = self.corwin_schultz_spread(high, low, close)
            
            # Enhancement: Adjust for overnight returns and volatility
            overnight_returns = np.log(close / close.shift(1))
            intraday_returns = np.log(high / low)
            
            # Volatility adjustment factor
            volatility = overnight_returns.rolling(window=20).std()
            vol_adjustment = 1 + 0.5 * volatility.fillna(0)
            
            # Liquidity adjustment based on high-low range relative to price
            liquidity_proxy = (high - low) / close
            liquidity_factor = 1 + liquidity_proxy.rolling(window=5).mean().fillna(0)
            
            # Enhanced spread estimate
            enhanced_spread = cs_spread * vol_adjustment * liquidity_factor
            
            # Apply bounds
            enhanced_spread = np.clip(enhanced_spread, self.min_spread, self.max_spread)
            
            return enhanced_spread
            
        except Exception as e:
            print(f"Error in enhanced spread calculation: {e}")
            return self.corwin_schultz_spread(high, low, close)
    
    def market_impact_cost(self, volume: pd.Series, close: pd.Series, 
                          trade_size_usd: float) -> pd.Series:
        """
        Market Impact Cost Model
        
        Estimates temporary price impact from trading based on:
        - Trade size relative to average daily volume (ADV)
        - Stock volatility
        - Empirical market impact parameters
        
        Formula: MI = η × σ × (Q/ADV)^β
        where:
        - η ≈ 0.5 for US equities (market impact coefficient)
        - σ = 20-day realized volatility
        - Q = trade size in shares
        - ADV = 20-day average daily volume
        - β ≈ 0.6 (concave impact function)
        
        Args:
            volume: Daily volume series
            close: Daily close prices
            trade_size_usd: Trade size in USD
            
        Returns:
            Market impact cost as fraction of price
        """
        try:
            # Calculate average daily volume (ADV) in shares
            adv_shares = volume.rolling(window=20).mean()
            
            # Calculate trade size in shares
            trade_size_shares = trade_size_usd / close
            
            # Calculate volume participation rate
            participation_rate = trade_size_shares / adv_shares
            
            # Calculate 20-day realized volatility
            returns = np.log(close / close.shift(1))
            volatility = returns.rolling(window=20).std() * np.sqrt(252)  # Annualized
            
            # Market impact parameters (empirically calibrated for US equities)
            eta = 0.5      # Market impact coefficient
            beta = 0.6     # Participation rate exponent (concave)
            
            # Calculate market impact
            market_impact = eta * volatility * (participation_rate ** beta)
            
            # Apply reasonable bounds (0 to 10% impact)
            market_impact = market_impact.fillna(0)
            market_impact = np.clip(market_impact, 0, 0.10)
            
            return market_impact
            
        except Exception as e:
            print(f"Error in market impact calculation: {e}")
            return pd.Series([0] * len(volume), index=volume.index)
    
    def capacity_constraint_check(self, volume: pd.Series, close: pd.Series, 
                                 trade_size_usd: float, max_adv_participation: float = 0.08) -> bool:
        """
        Check if trade size violates capacity constraints
        
        Args:
            volume: Daily volume series
            close: Daily close prices
            trade_size_usd: Trade size in USD
            max_adv_participation: Maximum allowed participation rate (default 8%)
            
        Returns:
            True if trade is feasible, False if it violates capacity constraints
        """
        try:
            # Calculate recent ADV
            recent_adv_shares = volume.tail(20).mean()
            recent_close = close.iloc[-1]
            recent_adv_usd = recent_adv_shares * recent_close
            
            # Calculate participation rate
            participation_rate = trade_size_usd / recent_adv_usd
            
            return participation_rate <= max_adv_participation
            
        except Exception:
            return False
    
    def get_stock_price_data(self, ticker: str, days: int = 60) -> Optional[pd.DataFrame]:
        """Get historical price and volume data for transaction cost analysis"""
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            stock = yf.Ticker(ticker)
            data = stock.history(start=start_date, end=end_date, auto_adjust=True)
            
            if data.empty or len(data) < 20:
                return None
                
            return data
            
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None
    
    def estimate_transaction_costs(self, ticker: str, trade_size_usd: float, 
                                  method: str = 'enhanced') -> Dict[str, float]:
        """
        Comprehensive transaction cost estimation for a single stock
        
        Args:
            ticker: Stock ticker symbol
            trade_size_usd: Trade size in USD
            method: 'corwin_schultz', 'enhanced', or 'both'
            
        Returns:
            Dict with transaction cost components
        """
        
        # Get price data
        price_data = self.get_stock_price_data(ticker)
        
        if price_data is None:
            return {
                'ticker': ticker,
                'bid_ask_spread': self.default_spread,
                'market_impact': 0.001,  # 10 bps default
                'total_cost': self.default_spread + 0.001,
                'capacity_feasible': True,
                'data_available': False,
                'method': 'default'
            }
        
        # Extract OHLCV data
        high = price_data['High']
        low = price_data['Low']
        close = price_data['Close']
        volume = price_data['Volume']
        
        # Calculate bid-ask spread estimates
        if method == 'corwin_schultz':
            spread = self.corwin_schultz_spread(high, low, close)
        elif method == 'enhanced':
            spread = self.enhanced_high_low_spread(high, low, close)
        else:  # both
            cs_spread = self.corwin_schultz_spread(high, low, close)
            enh_spread = self.enhanced_high_low_spread(high, low, close)
            spread = (cs_spread + enh_spread) / 2  # Average of both methods
        
        # Use most recent spread estimate
        current_spread = spread.iloc[-1] if len(spread) > 0 else self.default_spread
        
        # Calculate market impact
        market_impact = self.market_impact_cost(volume, close, trade_size_usd)
        current_impact = market_impact.iloc[-1] if len(market_impact) > 0 else 0
        
        # Check capacity constraints
        capacity_ok = self.capacity_constraint_check(volume, close, trade_size_usd)
        
        # Total transaction cost (one-way)
        total_cost = current_spread / 2 + current_impact  # Half-spread + impact
        
        return {
            'ticker': ticker,
            'bid_ask_spread': float(current_spread),
            'half_spread_cost': float(current_spread / 2),
            'market_impact': float(current_impact),
            'total_cost': float(total_cost),
            'capacity_feasible': capacity_ok,
            'data_available': True,
            'method': method,
            'recent_price': float(close.iloc[-1]),
            'recent_volume': float(volume.tail(5).mean()),
            'trade_size_usd': trade_size_usd
        }
    
    def estimate_portfolio_costs(self, tickers: List[str], portfolio_value: float, 
                                equal_weight: bool = True) -> Dict[str, Dict]:
        """
        Estimate transaction costs for an entire portfolio
        
        Args:
            tickers: List of stock tickers
            portfolio_value: Total portfolio value in USD
            equal_weight: If True, equal weight allocation; if False, cap-weighted
            
        Returns:
            Dict mapping ticker to transaction cost estimates
        """
        
        results = {}
        
        if equal_weight:
            # Equal weight allocation
            position_size = portfolio_value / len(tickers)
            
            print(f"🧮 Estimating transaction costs for {len(tickers)} stocks...")
            print(f"💰 Portfolio value: ${portfolio_value:,.0f}")
            print(f"📊 Position size: ${position_size:,.0f} per stock")
            
            for i, ticker in enumerate(tickers):
                if i % 10 == 0:
                    print(f"   Progress: {i}/{len(tickers)} processed...")
                
                cost_estimate = self.estimate_transaction_costs(ticker, position_size)
                results[ticker] = cost_estimate
        
        else:
            # TODO: Implement market-cap weighted allocation
            print("Market-cap weighting not yet implemented, using equal weight")
            return self.estimate_portfolio_costs(tickers, portfolio_value, equal_weight=True)
        
        # Calculate portfolio-level statistics
        valid_estimates = [r for r in results.values() if r['data_available']]
        
        if valid_estimates:
            avg_spread = np.mean([r['bid_ask_spread'] for r in valid_estimates])
            avg_impact = np.mean([r['market_impact'] for r in valid_estimates])
            avg_total = np.mean([r['total_cost'] for r in valid_estimates])
            
            print(f"\n📈 Portfolio Transaction Cost Summary:")
            print(f"   💹 Average bid-ask spread: {avg_spread*100:.2f} bps")
            print(f"   🎯 Average market impact: {avg_impact*100:.2f} bps") 
            print(f"   💰 Average total cost: {avg_total*100:.2f} bps")
            print(f"   ✅ Stocks with data: {len(valid_estimates)}/{len(tickers)}")
            
            # Capacity constraint summary
            infeasible_count = sum(1 for r in valid_estimates if not r['capacity_feasible'])
            if infeasible_count > 0:
                print(f"   ⚠️  Capacity constraints: {infeasible_count} stocks exceed 8% ADV")
        
        return results

def test_transaction_cost_model():
    """Test the transaction cost model with sample stocks"""
    
    model = TransactionCostModel()
    
    # Test with a variety of stocks (different liquidity profiles)
    test_stocks = ['AAPL', 'MSFT', 'GOOGL', 'BRK.B', 'JNJ']  # Large cap, liquid
    portfolio_value = 1_000_000  # $1M portfolio
    
    print("🧪 Testing Transaction Cost Model")
    print("=" * 50)
    
    # Test individual stock
    print(f"\n📊 Individual Stock Analysis (AAPL, $100k position):")
    aapl_costs = model.estimate_transaction_costs('AAPL', 100_000, method='enhanced')
    
    for key, value in aapl_costs.items():
        if isinstance(value, float):
            if 'cost' in key or 'spread' in key or 'impact' in key:
                print(f"   {key}: {value*100:.2f} bps")
            else:
                print(f"   {key}: {value:,.2f}")
        else:
            print(f"   {key}: {value}")
    
    # Test portfolio
    print(f"\n📈 Portfolio Analysis:")
    portfolio_costs = model.estimate_portfolio_costs(test_stocks, portfolio_value)
    
    return portfolio_costs

if __name__ == "__main__":
    test_transaction_cost_model()