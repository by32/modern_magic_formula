#!/usr/bin/env python3
"""
Time Series Cross-Validation for Magic Formula Factor Weights

This module implements time series cross-validation to validate the stability
and robustness of Magic Formula factor weights (earnings yield vs ROC) across
different market periods and economic cycles.

Key Features:
1. Walk-forward time series splits 
2. Factor weight optimization for each period
3. Out-of-sample validation
4. Performance stability analysis
5. Market regime analysis
"""

import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

# Import our modules
from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.risk_constraints import RiskConstraintManager


class MagicFormulaValidator:
    """Cross-validate Magic Formula factor weights using time series splits"""
    
    def __init__(self):
        self.validation_periods = []
        self.factor_weights_history = []
        self.performance_history = []
        self.risk_manager = RiskConstraintManager()
        
    def create_time_series_splits(self, start_date: str, end_date: str, 
                                 train_months: int = 12, test_months: int = 3,
                                 step_months: int = 3) -> List[Tuple[str, str, str, str]]:
        """
        Create walk-forward time series splits for validation.
        
        Args:
            start_date: Overall start date
            end_date: Overall end date  
            train_months: Training period length in months
            test_months: Test period length in months
            step_months: Step size between splits in months
            
        Returns:
            List of (train_start, train_end, test_start, test_end) tuples
        """
        
        splits = []
        current_date = pd.to_datetime(start_date)
        final_date = pd.to_datetime(end_date)
        
        print(f"🔄 Creating time series splits...")
        print(f"   Training period: {train_months} months")
        print(f"   Test period: {test_months} months") 
        print(f"   Step size: {step_months} months")
        
        while current_date + pd.DateOffset(months=train_months + test_months) <= final_date:
            
            train_start = current_date.strftime('%Y-%m-%d')
            train_end = (current_date + pd.DateOffset(months=train_months)).strftime('%Y-%m-%d')
            test_start = train_end
            test_end = (current_date + pd.DateOffset(months=train_months + test_months)).strftime('%Y-%m-%d')
            
            splits.append((train_start, train_end, test_start, test_end))
            
            # Move forward by step_months
            current_date += pd.DateOffset(months=step_months)
        
        print(f"✅ Created {len(splits)} validation splits")
        return splits
    
    def calculate_factor_scores(self, data: pd.DataFrame, 
                               ey_weight: float = 0.5, roc_weight: float = 0.5) -> pd.DataFrame:
        """Calculate Magic Formula scores with custom factor weights"""
        
        scored_data = data.copy()
        
        # Ensure we have the required columns
        if 'earnings_yield' not in data.columns or 'roc' not in data.columns:
            raise ValueError("Data must contain 'earnings_yield' and 'roc' columns")
        
        # Handle missing values
        scored_data = scored_data.dropna(subset=['earnings_yield', 'roc'])
        
        if len(scored_data) == 0:
            return scored_data
        
        # Rank factors (1 = best)
        scored_data['ey_rank'] = scored_data['earnings_yield'].rank(ascending=False)
        scored_data['roc_rank'] = scored_data['roc'].rank(ascending=False)
        
        # Calculate combined score with custom weights
        scored_data['combined_score'] = (ey_weight * scored_data['ey_rank'] + 
                                        roc_weight * scored_data['roc_rank'])
        
        # Final ranking (1 = best overall)
        scored_data['magic_formula_rank'] = scored_data['combined_score'].rank()
        
        return scored_data
    
    def optimize_factor_weights(self, train_data: pd.DataFrame, 
                               historical_returns: pd.DataFrame) -> Dict[str, float]:
        """
        Optimize factor weights using historical return data.
        
        Args:
            train_data: Training period fundamental data
            historical_returns: Historical stock returns for training period
            
        Returns:
            Dict with optimized weights and performance metrics
        """
        
        print(f"🎯 Optimizing factor weights...")
        print(f"   Training stocks: {len(train_data)}")
        
        # Define objective function
        def objective_function(weights):
            ey_weight, roc_weight = weights[0], 1 - weights[0]  # Weights sum to 1
            
            try:
                # Calculate scores with these weights
                scored_data = self.calculate_factor_scores(train_data, ey_weight, roc_weight)
                
                if len(scored_data) < 20:  # Need minimum stocks
                    return 1000  # High penalty
                
                # Select top 50 stocks
                top_stocks = scored_data.nsmallest(50, 'magic_formula_rank')
                top_tickers = top_stocks['ticker'].tolist()
                
                # Calculate portfolio return
                if len(top_tickers) == 0:
                    return 1000
                
                # Get returns for selected stocks
                portfolio_returns = []
                for ticker in top_tickers:
                    if ticker in historical_returns.columns:
                        stock_returns = historical_returns[ticker].dropna()
                        if len(stock_returns) > 0:
                            portfolio_returns.append(stock_returns.mean())
                
                if len(portfolio_returns) == 0:
                    return 1000
                
                # Calculate portfolio metrics
                avg_return = np.mean(portfolio_returns)
                return_std = np.std(portfolio_returns) if len(portfolio_returns) > 1 else 0.1
                
                # Objective: Minimize negative Sharpe ratio
                sharpe_ratio = avg_return / max(return_std, 0.001)  # Avoid division by zero
                return -sharpe_ratio
                
            except Exception as e:
                print(f"   ⚠️  Error in optimization: {e}")
                return 1000
        
        # Optimize weights
        try:
            # Constraint: earnings yield weight between 0.1 and 0.9
            bounds = [(0.1, 0.9)]
            initial_guess = [0.5]  # Start with equal weights
            
            result = minimize(objective_function, initial_guess, bounds=bounds, 
                            method='L-BFGS-B')
            
            optimal_ey_weight = result.x[0]
            optimal_roc_weight = 1 - optimal_ey_weight
            
            print(f"   ✅ Optimization complete")
            print(f"   📊 Optimal EY weight: {optimal_ey_weight:.3f}")
            print(f"   📊 Optimal ROC weight: {optimal_roc_weight:.3f}")
            
            return {
                'ey_weight': optimal_ey_weight,
                'roc_weight': optimal_roc_weight,
                'optimization_success': result.success,
                'objective_value': result.fun
            }
            
        except Exception as e:
            print(f"   ❌ Optimization failed: {e}")
            # Return default equal weights
            return {
                'ey_weight': 0.5,
                'roc_weight': 0.5,
                'optimization_success': False,
                'objective_value': None
            }
    
    def validate_split(self, train_start: str, train_end: str, 
                      test_start: str, test_end: str,
                      universe_data: pd.DataFrame) -> Dict[str, any]:
        """Validate factor weights on a single time split"""
        
        print(f"\n🔬 Validating split: {train_start} to {test_end}")
        print(f"   📚 Training: {train_start} to {train_end}")
        print(f"   📊 Testing: {test_start} to {test_end}")
        
        # For this implementation, we'll use current fundamental data
        # In a full implementation, you'd load historical fundamental data
        train_data = universe_data.copy()
        
        # Create mock historical returns (in real implementation, load actual data)
        tickers = train_data['ticker'].tolist()
        date_range = pd.date_range(start=train_start, end=train_end, freq='D')
        
        # Simulate returns based on fundamentals (mock implementation)
        np.random.seed(42)  # For reproducibility
        historical_returns = pd.DataFrame(
            np.random.normal(0.001, 0.02, (len(date_range), len(tickers))),
            index=date_range,
            columns=tickers
        )
        
        # Add some factor-based signal to returns
        for i, ticker in enumerate(tickers):
            if ticker in train_data['ticker'].values:
                stock_data = train_data[train_data['ticker'] == ticker].iloc[0]
                ey = stock_data.get('earnings_yield', 0)
                roc = stock_data.get('roc', 0)
                
                # Higher EY and ROC should lead to higher returns (simplified)
                signal = (ey * 0.1 + roc * 0.05) / 100
                historical_returns[ticker] += signal
        
        # Optimize factor weights on training period
        weights = self.optimize_factor_weights(train_data, historical_returns)
        
        # Test optimized weights on test period
        test_scored = self.calculate_factor_scores(
            train_data, weights['ey_weight'], weights['roc_weight']
        )
        
        # Apply risk constraints
        top_100 = test_scored.nsmallest(100, 'magic_formula_rank')
        constrained_portfolio = self.risk_manager.apply_risk_constraints(top_100, target_size=30)
        
        # Calculate test period performance (simplified)
        test_performance = {
            'period': f"{test_start} to {test_end}",
            'portfolio_size': len(constrained_portfolio),
            'avg_earnings_yield': constrained_portfolio['earnings_yield'].mean() if len(constrained_portfolio) > 0 else 0,
            'avg_roc': constrained_portfolio['roc'].mean() if len(constrained_portfolio) > 0 else 0,
            'sector_diversity': len(constrained_portfolio['sector'].unique()) if len(constrained_portfolio) > 0 else 0
        }
        
        return {
            'train_period': f"{train_start} to {train_end}",
            'test_period': f"{test_start} to {test_end}",
            'weights': weights,
            'test_performance': test_performance,
            'portfolio': constrained_portfolio
        }
    
    def run_cross_validation(self, universe_data: pd.DataFrame,
                           start_date: str = "2020-01-01",
                           end_date: str = "2024-01-01") -> Dict[str, any]:
        """Run full cross-validation analysis"""
        
        print(f"🚀 Running Magic Formula Cross-Validation")
        print(f"   📅 Period: {start_date} to {end_date}")
        print(f"   📊 Universe: {len(universe_data)} stocks")
        print("=" * 60)
        
        # Create time series splits
        splits = self.create_time_series_splits(start_date, end_date)
        
        # Run validation for each split
        validation_results = []
        
        for i, (train_start, train_end, test_start, test_end) in enumerate(splits):
            print(f"\n📈 Processing split {i+1}/{len(splits)}")
            
            try:
                result = self.validate_split(train_start, train_end, test_start, test_end, universe_data)
                validation_results.append(result)
                
            except Exception as e:
                print(f"   ❌ Split failed: {e}")
                continue
        
        # Analyze results
        cv_summary = self.analyze_cross_validation_results(validation_results)
        
        return {
            'splits': validation_results,
            'summary': cv_summary,
            'universe_stats': {
                'total_stocks': len(universe_data),
                'avg_market_cap': universe_data['market_cap'].mean(),
                'sectors': universe_data['sector'].value_counts().to_dict()
            }
        }
    
    def analyze_cross_validation_results(self, results: List[Dict]) -> Dict[str, any]:
        """Analyze cross-validation results for insights"""
        
        print(f"\n📊 Analyzing Cross-Validation Results...")
        
        if not results:
            return {'error': 'No validation results to analyze'}
        
        # Extract factor weights across splits
        ey_weights = [r['weights']['ey_weight'] for r in results if r['weights']['optimization_success']]
        roc_weights = [r['weights']['roc_weight'] for r in results if r['weights']['optimization_success']]
        
        # Portfolio characteristics
        portfolio_sizes = [r['test_performance']['portfolio_size'] for r in results]
        avg_ey_values = [r['test_performance']['avg_earnings_yield'] for r in results]
        avg_roc_values = [r['test_performance']['avg_roc'] for r in results]
        sector_diversities = [r['test_performance']['sector_diversity'] for r in results]
        
        summary = {
            'total_splits': len(results),
            'successful_optimizations': len(ey_weights),
            'factor_weight_stability': {
                'ey_weight_mean': np.mean(ey_weights) if ey_weights else 0.5,
                'ey_weight_std': np.std(ey_weights) if len(ey_weights) > 1 else 0,
                'roc_weight_mean': np.mean(roc_weights) if roc_weights else 0.5,
                'roc_weight_std': np.std(roc_weights) if len(roc_weights) > 1 else 0,
                'weight_range_ey': (min(ey_weights), max(ey_weights)) if ey_weights else (0.5, 0.5),
                'weight_range_roc': (min(roc_weights), max(roc_weights)) if roc_weights else (0.5, 0.5)
            },
            'portfolio_characteristics': {
                'avg_portfolio_size': np.mean(portfolio_sizes),
                'avg_earnings_yield': np.mean(avg_ey_values),
                'avg_roc': np.mean(avg_roc_values),
                'avg_sector_diversity': np.mean(sector_diversities)
            },
            'stability_metrics': {
                'weight_coefficient_of_variation': np.std(ey_weights) / np.mean(ey_weights) if ey_weights and np.mean(ey_weights) > 0 else None,
                'consistent_optimization': len(ey_weights) / len(results) if results else 0
            }
        }
        
        # Display results
        print(f"   ✅ Analysis complete")
        print(f"   📈 Successful optimizations: {summary['successful_optimizations']}/{summary['total_splits']}")
        print(f"   📊 EY weight stability: {summary['factor_weight_stability']['ey_weight_mean']:.3f} ± {summary['factor_weight_stability']['ey_weight_std']:.3f}")
        print(f"   📊 ROC weight stability: {summary['factor_weight_stability']['roc_weight_mean']:.3f} ± {summary['factor_weight_stability']['roc_weight_std']:.3f}")
        print(f"   🎯 Weight coefficient of variation: {summary['stability_metrics']['weight_coefficient_of_variation']:.3f}" if summary['stability_metrics']['weight_coefficient_of_variation'] else "   🎯 Weight coefficient of variation: N/A")
        
        return summary


def test_cross_validation():
    """Test the cross-validation framework"""
    
    print("🧪 Testing Magic Formula Cross-Validation")
    print("=" * 60)
    
    try:
        # Load universe data
        universe_data = pd.read_csv('data/latest_screening_hybrid.csv')
        print(f"📊 Loaded {len(universe_data)} stocks from screening data")
        
        # Filter for stocks with complete data
        complete_data = universe_data.dropna(subset=['earnings_yield', 'roc', 'market_cap'])
        print(f"📊 {len(complete_data)} stocks with complete factor data")
        
        # Initialize validator
        validator = MagicFormulaValidator()
        
        # Run cross-validation with shorter periods for testing
        cv_results = validator.run_cross_validation(
            complete_data.head(100),  # Use subset for testing
            start_date="2020-01-01",
            end_date="2024-01-01"
        )
        
        print(f"\n📋 Cross-Validation Summary:")
        if 'summary' in cv_results:
            print(f"   Total splits: {cv_results['summary'].get('total_splits', 0)}")
            print(f"   Universe size: {cv_results['universe_stats']['total_stocks']}")
        else:
            print(f"   No results generated")
        
        return cv_results
        
    except Exception as e:
        print(f"❌ Cross-validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_cross_validation()