"""
Performance metrics calculation for backtesting results.

This module calculates various performance metrics including:
- Total returns, annualized returns
- Volatility and Sharpe ratio
- Maximum drawdown and recovery time
- Alpha and beta vs benchmark
- Win rate and other statistics
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from scipy import stats


def calculate_returns_metrics(returns: pd.Series) -> Dict:
    """
    Calculate comprehensive return metrics.
    
    Args:
        returns: Series of daily returns
        
    Returns:
        Dict with return metrics
    """
    if len(returns) == 0:
        return {}
    
    # Basic return metrics
    total_return = (1 + returns).prod() - 1
    
    # Annualized metrics (assuming daily returns)
    trading_days = 252
    years = len(returns) / trading_days
    annualized_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
    
    # Volatility
    daily_vol = returns.std()
    annualized_vol = daily_vol * np.sqrt(trading_days)
    
    # Sharpe ratio (assuming risk-free rate of 2%)
    risk_free_rate = 0.02
    excess_return = annualized_return - risk_free_rate
    sharpe_ratio = excess_return / annualized_vol if annualized_vol > 0 else 0
    
    # Win rate
    win_rate = (returns > 0).mean()
    
    # Best and worst periods
    best_day = returns.max()
    worst_day = returns.min()
    
    return {
        'total_return': total_return,
        'annualized_return': annualized_return,
        'annualized_volatility': annualized_vol,
        'sharpe_ratio': sharpe_ratio,
        'win_rate': win_rate,
        'best_day': best_day,
        'worst_day': worst_day,
        'total_days': len(returns)
    }


def calculate_drawdown_metrics(returns: pd.Series) -> Dict:
    """
    Calculate drawdown metrics.
    
    Args:
        returns: Series of daily returns
        
    Returns:
        Dict with drawdown metrics
    """
    if len(returns) == 0:
        return {}
    
    # Calculate cumulative returns
    cumulative = (1 + returns).cumprod()
    
    # Calculate running maximum (peak)
    running_max = cumulative.expanding().max()
    
    # Calculate drawdown
    drawdown = (cumulative - running_max) / running_max
    
    # Maximum drawdown
    max_drawdown = drawdown.min()
    
    # Find maximum drawdown period
    max_dd_idx = drawdown.idxmin()
    
    # Calculate recovery time (days to recover from max drawdown)
    recovery_time = None
    if max_dd_idx is not None:
        peak_before_dd = running_max.loc[max_dd_idx]
        recovery_series = cumulative[cumulative.index > max_dd_idx]
        recovery_idx = recovery_series[recovery_series >= peak_before_dd].index
        
        if len(recovery_idx) > 0:
            recovery_time = (recovery_idx[0] - max_dd_idx).days
    
    # Average drawdown
    negative_dd = drawdown[drawdown < 0]
    avg_drawdown = negative_dd.mean() if len(negative_dd) > 0 else 0
    
    return {
        'max_drawdown': max_drawdown,
        'max_drawdown_date': max_dd_idx,
        'recovery_time_days': recovery_time,
        'avg_drawdown': avg_drawdown,
        'drawdown_series': drawdown
    }


def calculate_benchmark_metrics(returns: pd.Series, benchmark_returns: pd.Series) -> Dict:
    """
    Calculate metrics relative to benchmark.
    
    Args:
        returns: Portfolio returns
        benchmark_returns: Benchmark returns
        
    Returns:
        Dict with benchmark comparison metrics
    """
    if len(returns) == 0 or len(benchmark_returns) == 0:
        return {}
    
    # Align dates
    aligned_data = pd.DataFrame({
        'portfolio': returns,
        'benchmark': benchmark_returns
    }).dropna()
    
    if len(aligned_data) < 30:  # Need minimum data points
        return {}
    
    portfolio_aligned = aligned_data['portfolio']
    benchmark_aligned = aligned_data['benchmark']
    
    # Calculate beta and alpha
    covariance = np.cov(portfolio_aligned, benchmark_aligned)[0, 1]
    benchmark_variance = np.var(benchmark_aligned)
    beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
    
    # Alpha calculation
    portfolio_return = calculate_returns_metrics(portfolio_aligned)['annualized_return']
    benchmark_return = calculate_returns_metrics(benchmark_aligned)['annualized_return']
    risk_free_rate = 0.02
    
    alpha = portfolio_return - (risk_free_rate + beta * (benchmark_return - risk_free_rate))
    
    # Correlation
    correlation = portfolio_aligned.corr(benchmark_aligned)
    
    # Information ratio (excess return / tracking error)
    excess_returns = portfolio_aligned - benchmark_aligned
    tracking_error = excess_returns.std() * np.sqrt(252)  # Annualized
    information_ratio = excess_returns.mean() * 252 / tracking_error if tracking_error > 0 else 0
    
    # Up/down capture ratios
    up_periods = benchmark_aligned > 0
    down_periods = benchmark_aligned < 0
    
    up_capture = (portfolio_aligned[up_periods].mean() / benchmark_aligned[up_periods].mean()) if up_periods.sum() > 0 else 0
    down_capture = (portfolio_aligned[down_periods].mean() / benchmark_aligned[down_periods].mean()) if down_periods.sum() > 0 else 0
    
    return {
        'alpha': alpha,
        'beta': beta,
        'correlation': correlation,
        'information_ratio': information_ratio,
        'tracking_error': tracking_error,
        'up_capture_ratio': up_capture,
        'down_capture_ratio': down_capture,
        'excess_return': portfolio_return - benchmark_return
    }


def calculate_comprehensive_metrics(returns: pd.Series, benchmark_returns: Optional[pd.Series] = None) -> Dict:
    """
    Calculate comprehensive performance metrics.
    
    Args:
        returns: Portfolio returns series
        benchmark_returns: Optional benchmark returns for comparison
        
    Returns:
        Dict with all performance metrics
    """
    metrics = {}
    
    # Basic return metrics
    metrics.update(calculate_returns_metrics(returns))
    
    # Drawdown metrics
    metrics.update(calculate_drawdown_metrics(returns))
    
    # Benchmark comparison (if available)
    if benchmark_returns is not None:
        benchmark_metrics = calculate_benchmark_metrics(returns, benchmark_returns)
        metrics.update(benchmark_metrics)
        
        # Also calculate benchmark standalone metrics
        benchmark_standalone = calculate_returns_metrics(benchmark_returns)
        metrics['benchmark_return'] = benchmark_standalone['annualized_return']
        metrics['benchmark_volatility'] = benchmark_standalone['annualized_volatility']
        metrics['benchmark_sharpe'] = benchmark_standalone['sharpe_ratio']
    
    return metrics


def format_metrics_for_display(metrics: Dict) -> pd.DataFrame:
    """
    Format metrics for nice display in Streamlit or reports.
    
    Args:
        metrics: Dict of calculated metrics
        
    Returns:
        DataFrame formatted for display
    """
    display_data = []
    
    # Return metrics
    if 'total_return' in metrics:
        display_data.append(['Total Return', f"{metrics['total_return']*100:.2f}%"])
    if 'annualized_return' in metrics:
        display_data.append(['Annualized Return', f"{metrics['annualized_return']*100:.2f}%"])
    if 'annualized_volatility' in metrics:
        display_data.append(['Annualized Volatility', f"{metrics['annualized_volatility']*100:.2f}%"])
    if 'sharpe_ratio' in metrics:
        display_data.append(['Sharpe Ratio', f"{metrics['sharpe_ratio']:.2f}"])
    if 'win_rate' in metrics:
        display_data.append(['Win Rate', f"{metrics['win_rate']*100:.1f}%"])
    
    # Drawdown metrics
    if 'max_drawdown' in metrics:
        display_data.append(['Max Drawdown', f"{metrics['max_drawdown']*100:.2f}%"])
    if 'recovery_time_days' in metrics and metrics['recovery_time_days']:
        display_data.append(['Recovery Time', f"{metrics['recovery_time_days']} days"])
    
    # Benchmark metrics
    if 'alpha' in metrics:
        display_data.append(['Alpha', f"{metrics['alpha']*100:.2f}%"])
    if 'beta' in metrics:
        display_data.append(['Beta', f"{metrics['beta']:.2f}"])
    if 'information_ratio' in metrics:
        display_data.append(['Information Ratio', f"{metrics['information_ratio']:.2f}"])
    if 'correlation' in metrics:
        display_data.append(['Correlation to Benchmark', f"{metrics['correlation']:.2f}"])
    
    # Benchmark comparison
    if 'benchmark_return' in metrics:
        display_data.append(['Benchmark Return', f"{metrics['benchmark_return']*100:.2f}%"])
        display_data.append(['Excess Return', f"{metrics['excess_return']*100:.2f}%"])
    
    return pd.DataFrame(display_data, columns=['Metric', 'Value'])


def create_performance_summary(backtest_results: Dict) -> Dict:
    """
    Create a performance summary from backtest results.
    
    Args:
        backtest_results: Results from BacktestEngine.run_backtest()
        
    Returns:
        Dict with performance summary
    """
    returns = backtest_results['portfolio_returns']
    benchmark_returns = backtest_results.get('benchmark_returns')
    config = backtest_results['config']
    
    # Calculate comprehensive metrics
    metrics = calculate_comprehensive_metrics(returns, benchmark_returns)
    
    # Add configuration info
    summary = {
        'config': {
            'period': f"{config.start_date} to {config.end_date}",
            'portfolio_size': config.portfolio_size,
            'rebalance_frequency': config.rebalance_frequency,
            'benchmark': config.benchmark,
            'transaction_cost': f"{config.transaction_cost*100:.2f}%"
        },
        'metrics': metrics,
        'portfolio_history': backtest_results['portfolio_history']
    }
    
    return summary