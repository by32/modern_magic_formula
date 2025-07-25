"""
Simple script to run backtesting analysis.

This demonstrates how to use the backtesting framework with our current
Modern Magic Formula screening data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtesting.engine import BacktestEngine, BacktestConfig, load_current_screening_data
from backtesting.metrics import create_performance_summary, format_metrics_for_display
import pandas as pd


def run_simple_backtest():
    """Run a simple backtest example."""
    
    print("🚀 Modern Magic Formula Backtest")
    print("="*50)
    
    # Load current screening data
    screening_data = load_current_screening_data()
    if screening_data.empty:
        print("❌ No screening data available. Please run ETL first.")
        return
    
    # Configure extended backtest
    config = BacktestConfig(
        start_date="2000-01-01",  # 24-year extended backtest
        end_date="2024-01-01",
        portfolio_size=30,  # Top 30 stocks (with risk constraints)
        rebalance_frequency="quarterly",
        initial_capital=100000.0,
        transaction_cost=0.001,  # Will be overridden by realistic costs
        benchmark="SPY",
        min_market_cap=5e9  # $5B minimum for longer history
    )
    
    print(f"📊 Screening data sample:")
    print(screening_data[['ticker', 'company_name', 'magic_formula_rank']].head())
    
    # Show available columns
    print(f"📋 Available columns: {list(screening_data.columns)}")
    
    # Filter for higher market cap stocks for better data availability
    if 'market_cap' in screening_data.columns:
        large_cap = screening_data[screening_data['market_cap'] >= config.min_market_cap]
        print(f"📈 Filtered to {len(large_cap)} large-cap stocks (≥${config.min_market_cap/1e9:.0f}B)")
        if len(large_cap) >= 50:
            screening_data = large_cap
    
    print(f"📊 Backtest Configuration:")
    print(f"   Period: {config.start_date} to {config.end_date}")
    print(f"   Portfolio: Top {config.portfolio_size} stocks")
    print(f"   Rebalancing: {config.rebalance_frequency}")
    print(f"   Min Market Cap: ${config.min_market_cap/1e9:.0f}B")
    print(f"   Benchmark: {config.benchmark}")
    
    # Initialize backtest engine
    engine = BacktestEngine(config)
    
    try:
        # Load universe and fetch price data
        engine.load_universe(screening_data)
        engine.fetch_historical_prices()
        
        # Run backtest
        results = engine.run_backtest()
        
        # Create performance summary
        summary = create_performance_summary(results)
        
        # Display results
        print("\n📈 BACKTEST RESULTS")
        print("="*50)
        
        metrics_df = format_metrics_for_display(summary['metrics'])
        print(metrics_df.to_string(index=False))
        
        # Show portfolio evolution
        print(f"\n📊 Portfolio Evolution ({len(summary['portfolio_history'])} rebalances):")
        for i, period in enumerate(summary['portfolio_history'][:3]):  # Show first 3
            print(f"\n   Rebalance {i+1} ({period['date'].strftime('%Y-%m-%d')}):")
            top_5 = period['portfolio'].head(5)
            for _, stock in top_5.iterrows():
                company_name = stock.get('company_name', 'Unknown')[:30]
                rank = stock.get('magic_formula_rank', 'N/A')
                print(f"      {stock['ticker']:6s} - {company_name:<30} (Rank: {rank})")
        
        if len(summary['portfolio_history']) > 3:
            print(f"      ... and {len(summary['portfolio_history']) - 3} more rebalances")
        
        # Save results
        results_df = pd.DataFrame({
            'date': results['portfolio_returns'].index,
            'portfolio_return': results['portfolio_returns'].values
        })
        
        if results['benchmark_returns'] is not None:
            benchmark_aligned = results['benchmark_returns'].reindex(results['portfolio_returns'].index, method='ffill')
            results_df['benchmark_return'] = benchmark_aligned.values
        
        results_df.to_csv('backtesting/backtest_results.csv', index=False)
        print(f"\n💾 Results saved to backtesting/backtest_results.csv")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    run_simple_backtest()