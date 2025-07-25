"""
Core backtesting engine for Modern Magic Formula strategies.

This module implements a hybrid backtesting approach that combines:
1. Current fundamental rankings from our Modern Magic Formula
2. Historical price data for performance simulation
3. Portfolio construction and rebalancing logic
4. Performance metrics calculation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yfinance as yf
from dataclasses import dataclass
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from etl.realistic_costs import RealisticTransactionCosts
from backtesting.risk_constraints import RiskConstraintManager


@dataclass
class BacktestConfig:
    """Configuration for backtesting parameters."""
    start_date: str = "2019-01-01"  # 5-year backtest
    end_date: str = "2024-12-31"
    portfolio_size: int = 50  # Top 50 stocks from rankings
    rebalance_frequency: str = "quarterly"  # monthly, quarterly, annually
    initial_capital: float = 100000.0  # $100k starting capital
    transaction_cost: float = 0.001  # 0.1% transaction cost
    benchmark: str = "SPY"  # S&P 500 benchmark
    min_market_cap: float = 1e9  # $1B minimum market cap
    exclude_sectors: List[str] = None  # Sectors to exclude


class BacktestEngine:
    """Main backtesting engine for strategy simulation."""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.universe_data = None
        self.price_data = {}
        self.benchmark_data = None
        self.results = None
        self.cost_model = RealisticTransactionCosts()  # Initialize realistic cost model
        self.risk_manager = RiskConstraintManager()    # Initialize risk constraint manager
        
    def load_universe(self, screening_data: pd.DataFrame) -> None:
        """
        Load current screening data as our stock universe.
        
        Args:
            screening_data: DataFrame with current Magic Formula rankings
        """
        print(f"📊 Loading universe from screening data...")
        
        # Filter by market cap and sectors
        filtered_data = screening_data.copy()
        
        if self.config.min_market_cap:
            filtered_data = filtered_data[
                filtered_data['market_cap'] >= self.config.min_market_cap
            ]
        
        if self.config.exclude_sectors:
            filtered_data = filtered_data[
                ~filtered_data['sector'].isin(self.config.exclude_sectors)
            ]
        
        # Sort by magic formula rank and take top stocks for backtesting
        self.universe_data = filtered_data.sort_values('magic_formula_rank').head(200)
        
        print(f"✅ Universe loaded: {len(self.universe_data)} stocks")
        print(f"📈 Market cap range: ${self.universe_data['market_cap'].min()/1e9:.1f}B - ${self.universe_data['market_cap'].max()/1e9:.1f}B")
        
    def fetch_historical_prices(self) -> None:
        """Fetch historical price data for all stocks in universe."""
        print(f"📈 Fetching historical price data from {self.config.start_date} to {self.config.end_date}...")
        
        tickers = self.universe_data['ticker'].tolist()
        
        # Add benchmark
        if self.config.benchmark not in tickers:
            tickers.append(self.config.benchmark)
        
        # Fetch data one ticker at a time to handle errors better
        successful_downloads = 0
        failed_tickers = []
        
        for i, ticker in enumerate(tickers):
            if i % 20 == 0:  # Progress update every 20 tickers
                print(f"   Progress: {i}/{len(tickers)} tickers processed...")
            
            try:
                # Fetch data for single ticker
                stock = yf.Ticker(ticker)
                data = stock.history(
                    start=self.config.start_date,
                    end=self.config.end_date,
                    auto_adjust=True,
                    actions=False
                )
                
                if not data.empty and len(data) > 50:  # Need at least ~2 months of data
                    self.price_data[ticker] = data['Close']
                    successful_downloads += 1
                else:
                    failed_tickers.append(ticker)
                    
            except Exception as e:
                failed_tickers.append(ticker)
                if len(failed_tickers) <= 5:  # Only show first 5 errors
                    print(f"⚠️  Error fetching {ticker}: {str(e)[:100]}...")
        
        print(f"   Progress: {len(tickers)}/{len(tickers)} tickers processed...")
        
        if failed_tickers:
            print(f"⚠️  Failed to fetch data for {len(failed_tickers)} tickers: {failed_tickers[:10]}{'...' if len(failed_tickers) > 10 else ''}")
        
        # Extract benchmark data
        if self.config.benchmark in self.price_data:
            self.benchmark_data = self.price_data[self.config.benchmark]
            print(f"✅ Benchmark data loaded: {len(self.benchmark_data)} data points")
        
        successful_tickers = len(self.price_data) - (1 if self.config.benchmark in self.price_data else 0)
        print(f"✅ Price data loaded for {successful_tickers}/{len(self.universe_data)} stocks")
        
        # Check if we have enough data to proceed
        if successful_tickers < 10:
            print(f"⚠️  Warning: Only {successful_tickers} stocks have price data. Consider adjusting date range or stock selection.")
        
    def create_portfolio_rankings(self, as_of_date: datetime) -> pd.DataFrame:
        """
        Create portfolio rankings as of a specific date using our Modern Magic Formula.
        
        For this hybrid approach, we'll use current fundamental rankings but could
        enhance this with historical fundamental data in the future.
        
        Args:
            as_of_date: Date for portfolio construction
            
        Returns:
            DataFrame with stocks ranked by our Modern Magic Formula
        """
        # For now, use current rankings but could add time-based adjustments
        rankings = self.universe_data.copy()
        
        # Filter to stocks with available price data at the given date
        available_stocks = []
        for ticker in rankings['ticker']:
            if ticker in self.price_data:
                prices = self.price_data[ticker]
                # Convert as_of_date to pandas timestamp and handle timezone
                as_of_ts = pd.Timestamp(as_of_date)
                if prices.index.tz is not None:
                    # If prices have timezone, localize our timestamp
                    as_of_ts = as_of_ts.tz_localize(prices.index.tz)
                elif as_of_ts.tz is not None:
                    # If our timestamp has timezone but prices don't, remove it
                    as_of_ts = as_of_ts.tz_localize(None)
                
                try:
                    # Check if we have any price data around the date
                    if len(prices) > 0 and (as_of_ts in prices.index or any(prices.index <= as_of_ts)):
                        available_stocks.append(ticker)
                    elif len(prices) > 0:
                        # If we have price data but date comparison fails, include it anyway
                        available_stocks.append(ticker)
                except (TypeError, ValueError):
                    # If comparison still fails, just include the stock if it has data
                    if len(prices) > 0:
                        available_stocks.append(ticker)
        
        rankings = rankings[rankings['ticker'].isin(available_stocks)]
        
        # Could add momentum adjustment based on historical performance up to as_of_date
        # For now, use the current quality rankings
        
        return rankings.sort_values('magic_formula_rank').head(self.config.portfolio_size)
        
    def get_rebalance_dates(self) -> List[datetime]:
        """Generate rebalancing dates based on frequency setting."""
        start = pd.to_datetime(self.config.start_date)
        end = pd.to_datetime(self.config.end_date)
        
        if self.config.rebalance_frequency == "monthly":
            freq = "MS"  # Month start
        elif self.config.rebalance_frequency == "quarterly":
            freq = "QS"  # Quarter start
        elif self.config.rebalance_frequency == "annually":
            freq = "YS"  # Year start
        else:
            raise ValueError(f"Unsupported rebalance frequency: {self.config.rebalance_frequency}")
            
        dates = pd.date_range(start=start, end=end, freq=freq)
        return [date.to_pydatetime() for date in dates]
        
    def calculate_portfolio_returns(self, portfolio: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.Series:
        """
        Calculate equal-weighted portfolio returns for a given period.
        
        Args:
            portfolio: DataFrame with portfolio stocks
            start_date: Start date for return calculation
            end_date: End date for return calculation
            
        Returns:
            Series of daily portfolio returns
        """
        tickers = portfolio['ticker'].tolist()
        
        if len(tickers) == 0:
            print(f"   ⚠️  No stocks available for portfolio on {start_date}")
            return pd.Series(dtype=float)
            
        weights = 1.0 / len(tickers)  # Equal weighting
        portfolio_returns = pd.Series(dtype=float)
        
        # Get price data for the period
        all_prices = pd.DataFrame()
        start_ts = pd.Timestamp(start_date)
        end_ts = pd.Timestamp(end_date)
        
        for ticker in tickers:
            if ticker in self.price_data:
                prices = self.price_data[ticker]
                
                # Handle timezone compatibility
                if prices.index.tz is not None:
                    start_ts_adj = start_ts.tz_localize(prices.index.tz) if start_ts.tz is None else start_ts
                    end_ts_adj = end_ts.tz_localize(prices.index.tz) if end_ts.tz is None else end_ts
                else:
                    start_ts_adj = start_ts.tz_localize(None) if start_ts.tz is not None else start_ts
                    end_ts_adj = end_ts.tz_localize(None) if end_ts.tz is not None else end_ts
                
                try:
                    mask = (prices.index >= start_ts_adj) & (prices.index <= end_ts_adj)
                    ticker_prices = prices[mask]
                    if len(ticker_prices) > 0:
                        all_prices[ticker] = ticker_prices
                except (TypeError, ValueError):
                    # If comparison fails, include all prices for this ticker
                    all_prices[ticker] = prices
        
        if all_prices.empty:
            return pd.Series(dtype=float)
            
        # Calculate returns for each stock
        returns = all_prices.pct_change().dropna()
        
        # Equal-weighted portfolio returns
        portfolio_returns = returns.mean(axis=1)
        
        return portfolio_returns
        
    def run_backtest(self) -> Dict:
        """
        Run the complete backtesting simulation.
        
        Returns:
            Dict with backtest results including returns, metrics, and portfolio history
        """
        print(f"🚀 Starting backtest simulation...")
        print(f"   📅 Period: {self.config.start_date} to {self.config.end_date}")
        print(f"   📊 Portfolio size: {self.config.portfolio_size} stocks")
        print(f"   🔄 Rebalancing: {self.config.rebalance_frequency}")
        
        if self.universe_data is None:
            raise ValueError("Universe data not loaded. Call load_universe() first.")
            
        if not self.price_data:
            raise ValueError("Price data not loaded. Call fetch_historical_prices() first.")
        
        rebalance_dates = self.get_rebalance_dates()
        print(f"   📅 Rebalancing {len(rebalance_dates)} times")
        
        # Track portfolio performance
        all_returns = pd.Series(dtype=float)
        portfolio_history = []
        transaction_costs = 0.0
        
        for i, rebalance_date in enumerate(rebalance_dates):
            print(f"\n📊 Rebalance {i+1}/{len(rebalance_dates)}: {rebalance_date.strftime('%Y-%m-%d')}")
            
            # Create portfolio for this period with risk constraints
            initial_portfolio = self.create_portfolio_rankings(rebalance_date)
            print(f"   📊 Initial selection: {len(initial_portfolio)} stocks")
            
            # Apply risk constraints
            try:
                constrained_portfolio = self.risk_manager.apply_risk_constraints(
                    initial_portfolio, target_size=self.config.portfolio_size
                )
                portfolio = constrained_portfolio
                print(f"   🛡️  Risk-constrained portfolio: {len(portfolio)} stocks")
            except Exception as e:
                print(f"   ⚠️  Risk constraint failed, using unconstrained: {e}")
                portfolio = initial_portfolio.head(self.config.portfolio_size)
            
            # Calculate end date for this period
            if i < len(rebalance_dates) - 1:
                end_date = rebalance_dates[i + 1]
            else:
                end_date = pd.to_datetime(self.config.end_date)
            
            # Calculate returns for this period
            period_returns = self.calculate_portfolio_returns(portfolio, rebalance_date, end_date)
            
            if len(period_returns) > 0:
                # Apply realistic transaction costs (only on rebalancing)
                if i > 0:  # No transaction cost for initial portfolio
                    period_transaction_cost = self.calculate_realistic_transaction_costs(portfolio)
                    # Reduce first return by transaction cost
                    if len(period_returns) > 0:
                        period_returns.iloc[0] -= period_transaction_cost
                        transaction_costs += period_transaction_cost
                        print(f"   💰 Transaction cost: {period_transaction_cost*100:.2f}%")
                
                all_returns = pd.concat([all_returns, period_returns])
                
                print(f"   📈 Period return: {period_returns.sum()*100:.2f}%")
            
            # Store portfolio for analysis - use available columns
            portfolio_cols = ['ticker', 'magic_formula_rank']
            if 'company_name' in portfolio.columns:
                portfolio_cols.append('company_name')
            if 'overall_quality_score' in portfolio.columns:
                portfolio_cols.append('overall_quality_score')
            if 'value_trap_avoidance_score' in portfolio.columns:
                portfolio_cols.append('value_trap_avoidance_score')
                
            portfolio_history.append({
                'date': rebalance_date,
                'portfolio': portfolio[portfolio_cols].copy()
            })
        
        # Calculate benchmark returns
        benchmark_returns = None
        if self.benchmark_data is not None:
            try:
                start_dt = pd.to_datetime(self.config.start_date)
                end_dt = pd.to_datetime(self.config.end_date)
                
                # Handle timezone compatibility
                if self.benchmark_data.index.tz is not None:
                    start_dt = start_dt.tz_localize(self.benchmark_data.index.tz)
                    end_dt = end_dt.tz_localize(self.benchmark_data.index.tz)
                
                mask = (self.benchmark_data.index >= start_dt) & (self.benchmark_data.index <= end_dt)
                benchmark_prices = self.benchmark_data[mask]
                benchmark_returns = benchmark_prices.pct_change().dropna()
            except (TypeError, ValueError):
                # If timezone handling fails, use all benchmark data
                benchmark_returns = self.benchmark_data.pct_change().dropna()
        
        # Store results
        self.results = {
            'portfolio_returns': all_returns,
            'benchmark_returns': benchmark_returns,
            'portfolio_history': portfolio_history,
            'config': self.config,
            'transaction_costs': transaction_costs
        }
        
        print(f"\n✅ Backtest complete!")
        print(f"   📊 Total returns: {len(all_returns)} data points")
        print(f"   💰 Total transaction costs: {transaction_costs*100:.3f}%")
        
        return self.results
    
    def calculate_realistic_transaction_costs(self, portfolio: pd.DataFrame) -> float:
        """
        Calculate realistic transaction costs for portfolio rebalancing.
        
        Args:
            portfolio: DataFrame with portfolio holdings
            
        Returns:
            Average transaction cost as fraction of portfolio value
        """
        try:
            # Equal weight allocation
            position_size = self.config.initial_capital / len(portfolio)
            
            # Get transaction costs for each stock
            costs = []
            for _, stock in portfolio.iterrows():
                ticker = stock['ticker']
                cost_data = self.cost_model.estimate_total_cost(ticker, position_size)
                if cost_data['data_available']:
                    costs.append(cost_data['total_cost'])
                else:
                    # Use fallback cost for missing data
                    costs.append(self.config.transaction_cost)
            
            # Return weighted average cost
            avg_cost = np.mean(costs) if costs else self.config.transaction_cost
            return avg_cost
            
        except Exception as e:
            print(f"⚠️  Error calculating realistic costs: {e}")
            return self.config.transaction_cost  # Fallback to simple cost


def load_current_screening_data() -> pd.DataFrame:
    """Load the current screening data for backtesting."""
    try:
        data = pd.read_csv('data/latest_screening.csv')
        print(f"📊 Loaded screening data: {len(data)} stocks")
        return data
    except FileNotFoundError:
        print("❌ Screening data not found. Run ETL process first.")
        return pd.DataFrame()