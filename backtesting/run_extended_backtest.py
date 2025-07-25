#!/usr/bin/env python3
"""
Extended Backtesting Script for Modern Magic Formula

This script runs a comprehensive 20+ year backtest with enhanced features:
1. Risk-constrained portfolio construction
2. Realistic transaction costs
3. Russell 1000 proxy universe
4. Multiple market cycles validation
5. Detailed performance attribution
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtesting.engine import BacktestEngine, BacktestConfig, load_current_screening_data
from backtesting.metrics import create_performance_summary, format_metrics_for_display
from backtesting.risk_constraints import RiskConstraintManager
import pandas as pd


def run_extended_backtest():
    """Run comprehensive extended backtest from 2000-2024"""
    
    print("🚀 Modern Magic Formula Extended Backtest (2000-2024)")
    print("="*70)
    
    # Load universe data
    screening_data = load_current_screening_data()
    if screening_data.empty:
        print("❌ No screening data available. Please run ETL first.")
        return
    
    # Configure extended backtest
    config = BacktestConfig(
        start_date="2000-01-01",  # 24-year comprehensive backtest
        end_date="2024-01-01",
        portfolio_size=30,        # 30-stock risk-managed portfolio
        rebalance_frequency="quarterly",
        initial_capital=1000000.0,  # $1M for institutional-scale analysis
        transaction_cost=0.001,     # Will be overridden by realistic costs
        benchmark="SPY",
        min_market_cap=2e9          # $2B minimum for longer data history
    )
    
    print(f"📊 Extended Backtest Configuration:")
    print(f"   📅 Period: {config.start_date} to {config.end_date} (24 years)")
    print(f"   💰 Starting capital: ${config.initial_capital:,.0f}")
    print(f"   📈 Portfolio size: {config.portfolio_size} stocks")
    print(f"   🔄 Rebalancing: {config.rebalance_frequency}")
    print(f"   📊 Benchmark: {config.benchmark}")
    print(f"   💼 Min market cap: ${config.min_market_cap/1e9:.1f}B")
    
    # Filter universe for extended backtest
    print(f"\n📊 Universe Analysis:")
    print(f"   📈 Total screening data: {len(screening_data)} stocks")
    
    # Apply market cap filter
    if 'market_cap' in screening_data.columns:
        large_cap = screening_data[screening_data['market_cap'] >= config.min_market_cap]
        print(f"   💼 Large cap stocks (≥${config.min_market_cap/1e9:.1f}B): {len(large_cap)}")
        if len(large_cap) >= 100:  # Need sufficient universe
            screening_data = large_cap
    
    # Sector diversification analysis
    if 'sector' in screening_data.columns:
        sector_counts = screening_data['sector'].value_counts()
        print(f"   🏢 Sector distribution:")
        for sector, count in sector_counts.head(5).items():
            print(f"      {sector}: {count} stocks")
    
    print(f"   🎯 Final universe: {len(screening_data)} stocks")
    
    # Initialize enhanced backtest engine
    engine = BacktestEngine(config)
    
    try:
        print(f"\n🔄 Loading universe and historical data...")
        
        # Load universe
        engine.load_universe(screening_data)
        
        # Fetch extended historical price data
        print(f"📈 Fetching 24-year historical data (this may take several minutes)...")
        engine.fetch_historical_prices()
        
        print(f"\n🚀 Running extended backtest simulation...")
        print(f"   📊 Expected rebalances: ~{24 * 4} quarterly rebalances")
        print(f"   🛡️  Risk constraints: Enabled")
        print(f"   💰 Transaction costs: Realistic (20-30 bps)")
        
        # Run comprehensive backtest
        results = engine.run_backtest()
        
        # Create detailed performance analysis
        summary = create_performance_summary(results)
        
        # Display comprehensive results
        print_extended_results(summary, config)
        
        # Save detailed results
        save_extended_results(results, summary)
        
        return results
        
    except Exception as e:
        print(f"\n❌ Extended backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def print_extended_results(summary: dict, config: BacktestConfig):
    """Print comprehensive backtest results"""
    
    print(f"\n📈 EXTENDED BACKTEST RESULTS (24 Years)")
    print("="*70)
    
    # Core performance metrics
    metrics_df = format_metrics_for_display(summary['metrics'])
    print(f"\n📊 Performance Summary:")
    print(metrics_df.to_string(index=False))
    
    # Market cycle analysis
    print(f"\n📈 Market Cycle Performance:")
    portfolio_returns = summary.get('portfolio_returns', pd.Series())
    benchmark_returns = summary.get('benchmark_returns', pd.Series())
    
    if len(portfolio_returns) > 0:
        # Analyze major market periods
        market_periods = {
            'Dot-com Crash (2000-2002)': ('2000-01-01', '2002-12-31'),
            'Recovery (2003-2006)': ('2003-01-01', '2006-12-31'),
            'Financial Crisis (2007-2009)': ('2007-01-01', '2009-12-31'),
            'Bull Market (2010-2019)': ('2010-01-01', '2019-12-31'),
            'COVID Era (2020-2024)': ('2020-01-01', '2024-01-01')
        }
        
        for period_name, (start, end) in market_periods.items():
            try:
                period_portfolio = portfolio_returns[start:end]
                period_benchmark = benchmark_returns[start:end] if len(benchmark_returns) > 0 else None
                
                if len(period_portfolio) > 0:
                    period_return = (1 + period_portfolio).prod() - 1
                    period_vol = period_portfolio.std() * np.sqrt(252)
                    
                    benchmark_return = (1 + period_benchmark).prod() - 1 if period_benchmark is not None and len(period_benchmark) > 0 else 0
                    alpha = period_return - benchmark_return
                    
                    print(f"   {period_name}:")
                    print(f"      Portfolio: {period_return*100:+.1f}% | Benchmark: {benchmark_return*100:+.1f}% | Alpha: {alpha*100:+.1f}%")
                    
            except Exception as e:
                print(f"   {period_name}: Analysis failed ({e})")
    
    # Risk and drawdown analysis
    print(f"\n🛡️  Risk Analysis:")
    if 'Max Drawdown' in summary['metrics']:
        max_dd = summary['metrics']['Max Drawdown']
        print(f"   📉 Maximum drawdown: {max_dd}")
    
    if 'Sharpe Ratio' in summary['metrics']:
        sharpe = summary['metrics']['Sharpe Ratio']
        print(f"   📊 Sharpe ratio: {sharpe}")
    
    # Transaction cost impact
    total_costs = summary.get('transaction_costs', 0)
    print(f"\n💰 Transaction Cost Analysis:")
    print(f"   📊 Total transaction costs: {total_costs*100:.2f}%")
    print(f"   📅 Cost per year: {(total_costs/24)*100:.2f}%")
    print(f"   🔄 Cost per rebalance: ~{(total_costs/96)*100:.2f}%")
    
    # Portfolio evolution summary
    portfolio_history = summary.get('portfolio_history', [])
    if portfolio_history:
        print(f"\n📊 Portfolio Evolution:")
        print(f"   🔄 Total rebalances: {len(portfolio_history)}")
        print(f"   📈 Average portfolio size: {np.mean([len(p['portfolio']) for p in portfolio_history]):.1f} stocks")
        
        # Sector analysis across time
        all_sectors = []
        for period in portfolio_history:
            if 'sector' in period['portfolio'].columns:
                all_sectors.extend(period['portfolio']['sector'].tolist())
        
        if all_sectors:
            sector_freq = pd.Series(all_sectors).value_counts()
            print(f"   🏢 Most frequent sectors:")
            for sector, count in sector_freq.head(3).items():
                pct = count / len(portfolio_history) * 100
                print(f"      {sector}: {pct:.1f}% of rebalances")


def save_extended_results(results: dict, summary: dict):
    """Save comprehensive results to files"""
    
    print(f"\n💾 Saving Extended Backtest Results...")
    
    # Save main results
    portfolio_returns = results.get('portfolio_returns', pd.Series())
    benchmark_returns = results.get('benchmark_returns', pd.Series())
    
    if len(portfolio_returns) > 0:
        results_df = pd.DataFrame({
            'date': portfolio_returns.index,
            'portfolio_return': portfolio_returns.values
        })
        
        if len(benchmark_returns) > 0:
            benchmark_aligned = benchmark_returns.reindex(portfolio_returns.index, method='ffill')
            results_df['benchmark_return'] = benchmark_aligned.values
        
        # Calculate cumulative returns
        results_df['portfolio_cumulative'] = (1 + results_df['portfolio_return']).cumprod()
        if 'benchmark_return' in results_df.columns:
            results_df['benchmark_cumulative'] = (1 + results_df['benchmark_return']).cumprod()
        
        # Save to CSV
        filename = f"backtesting/extended_backtest_results_{pd.Timestamp.now().strftime('%Y%m%d')}.csv"
        results_df.to_csv(filename, index=False)
        print(f"   📊 Results saved to: {filename}")
        
        # Save summary statistics
        summary_filename = f"backtesting/extended_backtest_summary_{pd.Timestamp.now().strftime('%Y%m%d')}.json"
        import json
        
        # Convert non-serializable objects to strings
        serializable_summary = {}
        for key, value in summary.items():
            if isinstance(value, (pd.Series, pd.DataFrame)):
                serializable_summary[key] = str(value)
            elif key == 'metrics':
                serializable_summary[key] = {k: str(v) for k, v in value.items()}
            else:
                serializable_summary[key] = str(value)
        
        with open(summary_filename, 'w') as f:
            json.dump(serializable_summary, f, indent=2)
        print(f"   📋 Summary saved to: {summary_filename}")


if __name__ == "__main__":
    run_extended_backtest()