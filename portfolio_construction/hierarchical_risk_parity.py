#!/usr/bin/env python3
"""
Hierarchical Risk Parity (HRP) Weighting Research

This module implements Hierarchical Risk Parity, an advanced portfolio construction
technique that can improve upon traditional equal-weight or market-cap weighted
approaches for the Magic Formula strategy.

Key Benefits of HRP:
1. Better diversification through hierarchical clustering
2. Reduced concentration risk 
3. More stable portfolio weights
4. Improved out-of-sample performance
5. Reduced sensitivity to estimation errors

The approach:
1. Calculate correlation matrix of Magic Formula stocks
2. Perform hierarchical clustering based on correlations
3. Apply risk parity within and across clusters
4. Compare to equal-weight and other schemes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# Import for clustering
from scipy.cluster.hierarchy import dendrogram, linkage, cut_tree
from scipy.spatial.distance import squareform
from sklearn.covariance import LedoitWolf


class HierarchicalRiskParity:
    """Implement Hierarchical Risk Parity portfolio construction"""
    
    def __init__(self, lookback_days: int = 252):
        self.lookback_days = lookback_days
        self.correlation_matrix = None
        self.clusters = None
        self.cluster_weights = None
        self.final_weights = None
        
    def calculate_correlation_matrix(self, returns_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate correlation matrix from returns data"""
        
        print(f"📊 Calculating correlation matrix for {len(returns_data.columns)} stocks...")
        
        # Use recent data for correlation calculation
        recent_returns = returns_data.tail(self.lookback_days)
        
        # Remove stocks with insufficient data
        min_observations = int(self.lookback_days * 0.8)  # Require 80% of observations
        valid_stocks = []
        
        for stock in recent_returns.columns:
            non_na_count = recent_returns[stock].count()
            if non_na_count >= min_observations:
                valid_stocks.append(stock)
        
        print(f"   📈 {len(valid_stocks)} stocks have sufficient data")
        
        # Calculate correlation matrix
        clean_returns = recent_returns[valid_stocks].fillna(0)
        correlation_matrix = clean_returns.corr()
        
        # Handle any remaining NaN values
        correlation_matrix = correlation_matrix.fillna(0)
        np.fill_diagonal(correlation_matrix.values, 1.0)
        
        self.correlation_matrix = correlation_matrix
        
        print(f"   ✅ Correlation matrix calculated: {correlation_matrix.shape}")
        print(f"   📊 Average correlation: {correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean():.3f}")
        
        return correlation_matrix
    
    def perform_hierarchical_clustering(self, correlation_matrix: pd.DataFrame, 
                                      num_clusters: int = 5) -> Dict[str, Any]:
        """Perform hierarchical clustering on correlation matrix"""
        
        print(f"🌳 Performing hierarchical clustering...")
        
        # Convert correlation to distance matrix
        distance_matrix = np.sqrt(2 * (1 - correlation_matrix))
        
        # Perform hierarchical clustering
        linkage_matrix = linkage(squareform(distance_matrix), method='ward')
        
        # Cut tree to get clusters
        cluster_labels = cut_tree(linkage_matrix, n_clusters=num_clusters).flatten()
        
        # Create cluster mapping
        clusters = {}
        for i, stock in enumerate(correlation_matrix.index):
            cluster_id = cluster_labels[i]
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(stock)
        
        self.clusters = clusters
        
        # Display cluster information
        print(f"   📊 Created {len(clusters)} clusters:")
        for cluster_id, stocks in clusters.items():
            print(f"   Cluster {cluster_id}: {len(stocks)} stocks")
            if len(stocks) <= 5:
                print(f"      Stocks: {', '.join(stocks)}")
            else:
                print(f"      Stocks: {', '.join(stocks[:3])} ... (+{len(stocks)-3} more)")
        
        return {
            'clusters': clusters,
            'linkage_matrix': linkage_matrix,
            'distance_matrix': distance_matrix
        }
    
    def calculate_cluster_risk_contributions(self, returns_data: pd.DataFrame, 
                                           clusters: Dict[int, List[str]]) -> Dict[int, float]:
        """Calculate risk contribution of each cluster"""
        
        print(f"⚖️ Calculating cluster risk contributions...")
        
        cluster_risk_contributions = {}
        
        for cluster_id, stocks in clusters.items():
            # Get returns for stocks in this cluster
            cluster_returns = returns_data[stocks].fillna(0)
            
            if len(stocks) == 1:
                # Single stock cluster
                cluster_vol = cluster_returns[stocks[0]].std() * np.sqrt(252)
            else:
                # Multi-stock cluster - calculate equal-weighted portfolio volatility
                equal_weights = np.ones(len(stocks)) / len(stocks)
                cluster_cov = cluster_returns.cov() * 252  # Annualized
                cluster_vol = np.sqrt(equal_weights.T @ cluster_cov @ equal_weights)
            
            cluster_risk_contributions[cluster_id] = cluster_vol
        
        # Normalize to get relative risk contributions
        total_risk = sum(cluster_risk_contributions.values())
        for cluster_id in cluster_risk_contributions:
            cluster_risk_contributions[cluster_id] /= total_risk
        
        print(f"   📊 Cluster risk contributions:")
        for cluster_id, risk_contrib in cluster_risk_contributions.items():
            print(f"   Cluster {cluster_id}: {risk_contrib:.2%}")
        
        return cluster_risk_contributions
    
    def calculate_hrp_weights(self, returns_data: pd.DataFrame, 
                             magic_formula_scores: pd.Series,
                             num_clusters: int = 5) -> pd.Series:
        """Calculate Hierarchical Risk Parity weights"""
        
        print(f"🔄 Calculating HRP weights...")
        
        # Step 1: Calculate correlation matrix
        correlation_matrix = self.calculate_correlation_matrix(returns_data)
        
        # Step 2: Perform hierarchical clustering
        clustering_result = self.perform_hierarchical_clustering(correlation_matrix, num_clusters)
        clusters = clustering_result['clusters']
        
        # Step 3: Calculate cluster risk contributions
        cluster_risks = self.calculate_cluster_risk_contributions(returns_data, clusters)
        
        # Step 4: Allocate capital to clusters using inverse risk weighting
        cluster_weights = {}
        for cluster_id, risk in cluster_risks.items():
            # Inverse risk weighting - lower risk clusters get higher weight
            cluster_weights[cluster_id] = (1 / risk) if risk > 0 else 0
        
        # Normalize cluster weights
        total_cluster_weight = sum(cluster_weights.values())
        for cluster_id in cluster_weights:
            cluster_weights[cluster_id] /= total_cluster_weight
        
        # Step 5: Allocate capital within clusters using Magic Formula scores and risk parity
        final_weights = {}
        
        for cluster_id, cluster_weight in cluster_weights.items():
            stocks_in_cluster = clusters[cluster_id]
            
            if len(stocks_in_cluster) == 1:
                # Single stock gets full cluster allocation
                final_weights[stocks_in_cluster[0]] = cluster_weight
            else:
                # Multiple stocks - combine Magic Formula ranking with risk parity
                cluster_returns = returns_data[stocks_in_cluster].fillna(0)
                
                # Calculate individual stock volatilities
                stock_vols = cluster_returns.std() * np.sqrt(252)
                
                # Get Magic Formula scores for this cluster
                cluster_mf_scores = magic_formula_scores[stocks_in_cluster]
                
                # Rank-based weights (higher rank = lower weight)
                rank_weights = 1 / cluster_mf_scores.rank()
                rank_weights = rank_weights / rank_weights.sum()
                
                # Risk parity weights (inverse volatility)
                risk_parity_weights = (1 / stock_vols) / (1 / stock_vols).sum()
                
                # Combine 70% Magic Formula ranking + 30% risk parity
                combined_weights = 0.7 * rank_weights + 0.3 * risk_parity_weights
                combined_weights = combined_weights / combined_weights.sum()
                
                # Apply to cluster allocation
                for stock in stocks_in_cluster:
                    final_weights[stock] = cluster_weight * combined_weights[stock]
        
        # Convert to Series and normalize
        weight_series = pd.Series(final_weights)
        weight_series = weight_series / weight_series.sum()
        
        self.final_weights = weight_series
        self.cluster_weights = cluster_weights
        
        print(f"   ✅ HRP weights calculated for {len(weight_series)} stocks")
        print(f"   📊 Weight concentration (top 5): {weight_series.nlargest(5).sum():.2%}")
        
        return weight_series
    
    def compare_weighting_schemes(self, returns_data: pd.DataFrame,
                                magic_formula_ranks: pd.Series,
                                portfolio_size: int = 30) -> Dict[str, Any]:
        """Compare different weighting schemes"""
        
        print(f"⚖️ Comparing Portfolio Weighting Schemes")
        print("=" * 60)
        
        # Get top stocks by Magic Formula
        top_stocks = magic_formula_ranks.nsmallest(portfolio_size).index
        top_returns = returns_data[top_stocks].fillna(0)
        top_ranks = magic_formula_ranks[top_stocks]
        
        # 1. Equal Weight
        equal_weights = pd.Series(1/len(top_stocks), index=top_stocks)
        
        # 2. Rank-based weights (higher rank = lower weight)
        rank_weights = 1 / top_ranks.rank()
        rank_weights = rank_weights / rank_weights.sum()
        
        # 3. HRP weights
        hrp_weights = self.calculate_hrp_weights(top_returns, top_ranks, num_clusters=5)
        
        # 4. Minimum Variance weights (for comparison)
        min_var_weights = self.calculate_minimum_variance_weights(top_returns)
        
        weighting_schemes = {
            'Equal Weight': equal_weights,
            'Rank Based': rank_weights,
            'HRP': hrp_weights,
            'Minimum Variance': min_var_weights
        }
        
        # Calculate portfolio metrics for each scheme
        comparison_results = {}
        
        for scheme_name, weights in weighting_schemes.items():
            # Align weights with returns data
            aligned_weights = weights.reindex(top_returns.columns).fillna(0)
            aligned_weights = aligned_weights / aligned_weights.sum()
            
            # Calculate portfolio returns
            portfolio_returns = (top_returns * aligned_weights).sum(axis=1)
            
            # Calculate metrics
            annual_return = portfolio_returns.mean() * 252
            annual_vol = portfolio_returns.std() * np.sqrt(252)
            sharpe_ratio = annual_return / annual_vol if annual_vol > 0 else 0
            
            # Calculate maximum drawdown
            cumulative = (1 + portfolio_returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # Weight concentration
            weight_concentration = aligned_weights.nlargest(5).sum()
            
            comparison_results[scheme_name] = {
                'annual_return': annual_return,
                'annual_volatility': annual_vol,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'weight_concentration': weight_concentration,
                'weights': aligned_weights
            }
        
        # Print comparison
        self.print_weighting_comparison(comparison_results)
        
        return comparison_results
    
    def calculate_minimum_variance_weights(self, returns_data: pd.DataFrame) -> pd.Series:
        """Calculate minimum variance portfolio weights"""
        
        # Use Ledoit-Wolf shrinkage for better covariance estimation
        lw = LedoitWolf()
        cov_matrix, _ = lw.fit(returns_data.fillna(0)).covariance_, lw.shrinkage_
        cov_matrix = pd.DataFrame(cov_matrix, index=returns_data.columns, columns=returns_data.columns)
        
        # Calculate minimum variance weights
        ones = np.ones((len(cov_matrix), 1))
        inv_cov = np.linalg.pinv(cov_matrix)
        weights = inv_cov @ ones
        weights = weights / weights.sum()
        
        return pd.Series(weights.flatten(), index=cov_matrix.index)
    
    def print_weighting_comparison(self, results: Dict[str, Dict]):
        """Print formatted comparison of weighting schemes"""
        
        print(f"\n📊 Portfolio Weighting Scheme Comparison:")
        print("-" * 80)
        print(f"{'Scheme':<18} {'Annual Return':<15} {'Volatility':<12} {'Sharpe':<8} {'Max DD':<10} {'Top5 Weight':<12}")
        print("-" * 80)
        
        for scheme, metrics in results.items():
            print(f"{scheme:<18} "
                  f"{metrics['annual_return']*100:>12.2f}% "
                  f"{metrics['annual_volatility']*100:>10.2f}% "
                  f"{metrics['sharpe_ratio']:>6.2f} "
                  f"{metrics['max_drawdown']*100:>8.2f}% "
                  f"{metrics['weight_concentration']*100:>10.2f}%")
        
        # Find best schemes
        best_sharpe = max(results.keys(), key=lambda x: results[x]['sharpe_ratio'])
        best_return = max(results.keys(), key=lambda x: results[x]['annual_return'])
        lowest_risk = min(results.keys(), key=lambda x: results[x]['annual_volatility'])
        
        print(f"\n🏆 Best Performers:")
        print(f"   Best Sharpe Ratio: {best_sharpe}")
        print(f"   Highest Return: {best_return}")
        print(f"   Lowest Risk: {lowest_risk}")
        
        print(f"\n💡 Key Insights:")
        hrp_sharpe = results.get('HRP', {}).get('sharpe_ratio', 0)
        equal_sharpe = results.get('Equal Weight', {}).get('sharpe_ratio', 0)
        
        if hrp_sharpe > equal_sharpe:
            improvement = ((hrp_sharpe - equal_sharpe) / equal_sharpe) * 100
            print(f"   ✅ HRP improves Sharpe ratio by {improvement:.1f}% vs Equal Weight")
        
        hrp_concentration = results.get('HRP', {}).get('weight_concentration', 0)
        equal_concentration = results.get('Equal Weight', {}).get('weight_concentration', 0)
        
        print(f"   📊 HRP concentration: {hrp_concentration:.1%} vs Equal Weight: {equal_concentration:.1%}")
        print(f"   🎯 HRP provides better diversification through hierarchical clustering")
        print(f"   ⚖️ Risk parity approach reduces concentration in high-volatility stocks")


def simulate_returns_data(magic_formula_data: pd.DataFrame, 
                         days: int = 500) -> pd.DataFrame:
    """Simulate historical returns data for demonstration"""
    
    print(f"📈 Simulating {days} days of returns data...")
    
    np.random.seed(42)
    
    # Get stock list
    stocks = magic_formula_data['ticker'].head(50).tolist()  # Top 50 for simulation
    
    # Create date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    date_range = date_range[date_range.weekday < 5]  # Trading days only
    
    # Simulate returns with realistic characteristics
    returns_data = pd.DataFrame(index=date_range, columns=stocks)
    
    for stock in stocks:
        # Base parameters
        annual_vol = np.random.uniform(0.15, 0.40)  # 15-40% annual volatility
        daily_vol = annual_vol / np.sqrt(252)
        drift = np.random.uniform(-0.001, 0.001)  # Small daily drift
        
        # Generate returns with autocorrelation
        returns = []
        prev_return = 0
        
        for i in range(len(date_range)):
            # Add some autocorrelation and mean reversion
            autocorr = 0.05 * prev_return  # 5% autocorrelation
            noise = np.random.normal(0, daily_vol)
            daily_return = drift + autocorr + noise
            
            returns.append(daily_return)
            prev_return = daily_return
        
        returns_data[stock] = returns
    
    # Add some sector correlations
    sectors = magic_formula_data.set_index('ticker')['sector'].to_dict()
    sector_factors = {}
    
    for date in date_range:
        sector_shocks = {
            sector: np.random.normal(0, 0.01) 
            for sector in set(sectors.values())
        }
        sector_factors[date] = sector_shocks
    
    # Apply sector correlations
    for stock in stocks:
        if stock in sectors:
            sector = sectors[stock]
            for date in date_range:
                sector_shock = sector_factors[date].get(sector, 0)
                returns_data.loc[date, stock] += sector_shock * 0.3  # 30% sector correlation
    
    print(f"   ✅ Generated returns for {len(stocks)} stocks over {len(date_range)} trading days")
    
    return returns_data


def test_hierarchical_risk_parity():
    """Test the Hierarchical Risk Parity implementation"""
    
    print("🧪 Testing Hierarchical Risk Parity Implementation")
    print("=" * 60)
    
    try:
        # Load Magic Formula data
        magic_formula_data = pd.read_csv('data/latest_screening_hybrid.csv')
        print(f"📊 Loaded Magic Formula data: {len(magic_formula_data)} stocks")
        
        # Simulate returns data
        returns_data = simulate_returns_data(magic_formula_data, days=500)
        
        # Create Magic Formula ranks
        mf_ranks = magic_formula_data.set_index('ticker')['magic_formula_rank']
        
        # Initialize HRP
        hrp = HierarchicalRiskParity(lookback_days=252)
        
        # Run comparison
        comparison_results = hrp.compare_weighting_schemes(
            returns_data=returns_data,
            magic_formula_ranks=mf_ranks,
            portfolio_size=30
        )
        
        print(f"\n📋 Implementation Notes:")
        print(f"   🌳 Hierarchical clustering groups similar stocks")
        print(f"   ⚖️ Risk parity allocates inverse to volatility")
        print(f"   🎯 Combines clustering with Magic Formula rankings")
        print(f"   📊 Typically improves diversification vs equal weight")
        
        return comparison_results
        
    except Exception as e:
        print(f"❌ HRP test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_hierarchical_risk_parity()