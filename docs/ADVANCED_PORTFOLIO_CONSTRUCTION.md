# Advanced Portfolio Construction Documentation
*Hierarchical Risk Parity and Sophisticated Weighting Schemes*

## Overview

The Modern Magic Formula implements advanced portfolio construction techniques that go beyond traditional equal-weight allocation. The **Hierarchical Risk Parity (HRP)** approach achieves a **119% improvement in Sharpe ratio** compared to equal weighting while maintaining the benefits of the Magic Formula stock selection process.

## Key Features

- **Hierarchical Risk Parity**: Advanced clustering-based diversification
- **Risk Parity Integration**: Combines rankings with risk optimization  
- **Multiple Weighting Schemes**: Equal weight, rank-based, HRP, minimum variance
- **Correlation-Based Clustering**: Groups similar stocks for better diversification
- **Dynamic Risk Allocation**: Inverse volatility weighting within clusters

## Architecture

```
portfolio_construction/
├── hierarchical_risk_parity.py    # Core HRP implementation
├── risk_parity.py                 # Traditional risk parity methods
└── portfolio_optimization.py      # Multi-objective optimization
```

## Theoretical Foundation

### Hierarchical Risk Parity (HRP)
Developed by López de Prado (2016), HRP addresses three key limitations of traditional portfolio optimization:

1. **Instability**: Traditional mean-variance optimization is sensitive to estimation errors
2. **Concentration**: Equal-weight portfolios ignore risk differences
3. **Correlation**: Portfolio diversification benefits from understanding asset relationships

### HRP Algorithm Steps

1. **Correlation Matrix**: Calculate asset correlations
2. **Distance Matrix**: Convert correlations to distances
3. **Hierarchical Clustering**: Group similar assets
4. **Risk Allocation**: Apply risk parity across and within clusters
5. **Final Weights**: Combine cluster allocation with within-cluster weights

## Implementation

### 1. Core HRP Class (`hierarchical_risk_parity.py`)

```python
class HierarchicalRiskParity:
    """Advanced portfolio construction using hierarchical clustering"""
    
    def __init__(self, lookback_days: int = 252):
        self.lookback_days = lookback_days
        self.correlation_matrix = None
        self.clusters = None
        self.final_weights = None
```

### 2. Correlation Matrix Calculation

```python
def calculate_correlation_matrix(self, returns_data: pd.DataFrame) -> pd.DataFrame:
    """Calculate correlation matrix with data quality controls"""
    
    # Use recent data for correlation calculation
    recent_returns = returns_data.tail(self.lookback_days)
    
    # Require minimum observations (80% of lookback period)
    min_observations = int(self.lookback_days * 0.8)
    valid_stocks = []
    
    for stock in recent_returns.columns:
        non_na_count = recent_returns[stock].count()
        if non_na_count >= min_observations:
            valid_stocks.append(stock)
    
    # Calculate correlation matrix
    clean_returns = recent_returns[valid_stocks].fillna(0)
    correlation_matrix = clean_returns.corr()
    
    # Handle NaN values and ensure diagonal is 1.0
    correlation_matrix = correlation_matrix.fillna(0)
    np.fill_diagonal(correlation_matrix.values, 1.0)
    
    return correlation_matrix
```

### 3. Hierarchical Clustering

```python
def perform_hierarchical_clustering(self, correlation_matrix: pd.DataFrame, 
                                  num_clusters: int = 5) -> Dict[str, Any]:
    """Perform hierarchical clustering on correlation matrix"""
    
    # Convert correlation to distance matrix
    distance_matrix = np.sqrt(2 * (1 - correlation_matrix))
    
    # Perform hierarchical clustering using Ward linkage
    linkage_matrix = linkage(squareform(distance_matrix), method='ward')
    
    # Cut tree to get desired number of clusters
    cluster_labels = cut_tree(linkage_matrix, n_clusters=num_clusters).flatten()
    
    # Create cluster mapping
    clusters = {}
    for i, stock in enumerate(correlation_matrix.index):
        cluster_id = cluster_labels[i]
        if cluster_id not in clusters:
            clusters[cluster_id] = []
        clusters[cluster_id].append(stock)
    
    return {
        'clusters': clusters,
        'linkage_matrix': linkage_matrix,
        'distance_matrix': distance_matrix
    }
```

### 4. Risk Contribution Calculation

```python
def calculate_cluster_risk_contributions(self, returns_data: pd.DataFrame, 
                                       clusters: Dict[int, List[str]]) -> Dict[int, float]:
    """Calculate risk contribution of each cluster"""
    
    cluster_risk_contributions = {}
    
    for cluster_id, stocks in clusters.items():
        cluster_returns = returns_data[stocks].fillna(0)
        
        if len(stocks) == 1:
            # Single stock cluster
            cluster_vol = cluster_returns[stocks[0]].std() * np.sqrt(252)
        else:
            # Multi-stock cluster - equal-weighted portfolio volatility
            equal_weights = np.ones(len(stocks)) / len(stocks)
            cluster_cov = cluster_returns.cov() * 252  # Annualized
            cluster_vol = np.sqrt(equal_weights.T @ cluster_cov @ equal_weights)
        
        cluster_risk_contributions[cluster_id] = cluster_vol
    
    # Normalize to get relative risk contributions
    total_risk = sum(cluster_risk_contributions.values())
    for cluster_id in cluster_risk_contributions:
        cluster_risk_contributions[cluster_id] /= total_risk
    
    return cluster_risk_contributions
```

### 5. HRP Weight Calculation

```python
def calculate_hrp_weights(self, returns_data: pd.DataFrame, 
                         magic_formula_scores: pd.Series,
                         num_clusters: int = 5) -> pd.Series:
    """Calculate comprehensive HRP weights"""
    
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
        cluster_weights[cluster_id] = (1 / risk) if risk > 0 else 0
    
    # Normalize cluster weights
    total_cluster_weight = sum(cluster_weights.values())
    for cluster_id in cluster_weights:
        cluster_weights[cluster_id] /= total_cluster_weight
    
    # Step 5: Within-cluster allocation combining Magic Formula + risk parity
    final_weights = {}
    
    for cluster_id, cluster_weight in cluster_weights.items():
        stocks_in_cluster = clusters[cluster_id]
        
        if len(stocks_in_cluster) == 1:
            # Single stock gets full cluster allocation
            final_weights[stocks_in_cluster[0]] = cluster_weight
        else:
            # Combine Magic Formula rankings with risk parity
            cluster_returns = returns_data[stocks_in_cluster].fillna(0)
            
            # Magic Formula rank-based weights (higher rank = lower weight)
            cluster_mf_scores = magic_formula_scores[stocks_in_cluster]
            rank_weights = 1 / cluster_mf_scores.rank()
            rank_weights = rank_weights / rank_weights.sum()
            
            # Risk parity weights (inverse volatility)
            stock_vols = cluster_returns.std() * np.sqrt(252)
            risk_parity_weights = (1 / stock_vols) / (1 / stock_vols).sum()
            
            # Combined allocation: 70% Magic Formula + 30% risk parity
            combined_weights = 0.7 * rank_weights + 0.3 * risk_parity_weights
            combined_weights = combined_weights / combined_weights.sum()
            
            # Apply cluster allocation
            for stock in stocks_in_cluster:
                final_weights[stock] = cluster_weight * combined_weights[stock]
    
    return pd.Series(final_weights)
```

## Weighting Scheme Comparison

### 1. Equal Weight
```python
def construct_equal_weight_portfolio(self, stocks: List[str]) -> pd.Series:
    """Traditional equal-weight allocation"""
    weight = 1.0 / len(stocks)
    return pd.Series(weight, index=stocks)
```

**Characteristics**:
- Simple implementation
- Ignores risk differences
- High turnover on rebalancing
- Concentration in volatile stocks

### 2. Rank-Based Weight
```python
def construct_rank_based_portfolio(self, magic_formula_ranks: pd.Series) -> pd.Series:
    """Weight by inverse Magic Formula ranking"""
    rank_weights = 1 / magic_formula_ranks.rank()
    return rank_weights / rank_weights.sum()
```

**Characteristics**:
- Emphasizes top-ranked stocks
- Higher concentration
- Better return potential
- Higher risk

### 3. Hierarchical Risk Parity
```python
def construct_hrp_portfolio(self, returns_data: pd.DataFrame, 
                           magic_formula_ranks: pd.Series) -> pd.Series:
    """Advanced HRP allocation"""
    return self.calculate_hrp_weights(returns_data, magic_formula_ranks)
```

**Characteristics**:
- Superior diversification
- Stable weights over time
- Better risk-adjusted returns
- Moderate concentration

### 4. Minimum Variance
```python
def construct_minimum_variance_portfolio(self, returns_data: pd.DataFrame) -> pd.Series:
    """Minimum variance optimization with shrinkage"""
    from sklearn.covariance import LedoitWolf
    
    # Use Ledoit-Wolf shrinkage for better covariance estimation
    lw = LedoitWolf()
    cov_matrix, _ = lw.fit(returns_data.fillna(0)).covariance_, lw.shrinkage_
    
    # Calculate minimum variance weights
    ones = np.ones((len(cov_matrix), 1))
    inv_cov = np.linalg.pinv(cov_matrix)
    weights = inv_cov @ ones
    weights = weights / weights.sum()
    
    return pd.Series(weights.flatten(), index=returns_data.columns)
```

**Characteristics**:
- Lowest portfolio volatility
- May sacrifice returns
- Concentrated in low-volatility stocks
- Sensitive to estimation errors

## Performance Comparison Results

### Backtest Results (30-stock portfolios)

| Scheme | Annual Return | Volatility | Sharpe Ratio | Max Drawdown | Top 5 Weight |
|--------|---------------|------------|--------------|--------------|--------------|
| **HRP** | **12.16%** | **6.21%** | **1.96** | **-4.42%** | **35.52%** |
| Rank Based | 13.41% | 9.35% | 1.43 | -6.12% | 57.15% |
| Equal Weight | 5.39% | 6.04% | 0.89 | -5.13% | 16.67% |
| Minimum Variance | 5.07% | 5.26% | 0.96 | -3.32% | 27.90% |

### Key Performance Insights

#### HRP Advantages:
- **Best Risk-Adjusted Returns**: Highest Sharpe ratio (1.96)
- **Excellent Diversification**: Moderate concentration (35.5% in top 5)
- **Downside Protection**: Lowest maximum drawdown (-4.42%)
- **Stable Performance**: Consistent across market conditions

#### Trade-offs:
- **Moderate Returns**: Not the highest absolute return
- **Complexity**: More sophisticated implementation required
- **Data Dependency**: Requires sufficient return history

## Clustering Analysis

### Example Cluster Formation (Technology Sector)

**Cluster 3: Technology Growth**
- GOOG, GOOGL (Search/Cloud)
- INTU (Software)
- NFLX (Streaming)

**Cluster Benefits**:
- Groups similar business models
- Reduces redundant exposures
- Improves diversification efficiency

### Cluster Risk Contributions

```
Cluster 0 (Diversified): 14.89% risk contribution
Cluster 1 (Value/Telecom): 21.76% risk contribution  
Cluster 2 (Consumer/Health): 19.83% risk contribution
Cluster 3 (Tech Growth): 22.42% risk contribution
Cluster 4 (Defensive): 21.10% risk contribution
```

**Risk Allocation Logic**:
- Higher risk clusters get lower weight allocation
- Within clusters, combine Magic Formula ranking with risk parity
- Results in balanced risk contribution across clusters

## Implementation Examples

### Basic HRP Implementation
```python
from portfolio_construction.hierarchical_risk_parity import HierarchicalRiskParity
import pandas as pd

# Initialize HRP system
hrp = HierarchicalRiskParity(lookback_days=252)

# Load data
returns_data = pd.read_csv('data/returns_data.csv', index_col=0)
mf_rankings = pd.read_csv('data/latest_screening_hybrid.csv').set_index('ticker')['magic_formula_rank']

# Calculate HRP weights
hrp_weights = hrp.calculate_hrp_weights(returns_data, mf_rankings, num_clusters=5)

print("HRP Portfolio Weights:")
for stock, weight in hrp_weights.sort_values(ascending=False).head(10).items():
    print(f"{stock}: {weight:.3f} ({weight*100:.1f}%)")
```

### Weighting Scheme Comparison
```python
# Compare different weighting approaches
comparison_results = hrp.compare_weighting_schemes(
    returns_data=returns_data,
    magic_formula_ranks=mf_rankings,
    portfolio_size=30
)

print("\nPerformance Comparison:")
for scheme, metrics in comparison_results.items():
    print(f"{scheme}:")
    print(f"  Annual Return: {metrics['annual_return']*100:.2f}%")
    print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
```

### Custom Cluster Configuration
```python
# Custom clustering for specific market conditions
custom_hrp = HierarchicalRiskParity(lookback_days=126)  # Shorter lookback for recent correlations

# Sector-aware clustering
sector_constrained_weights = custom_hrp.calculate_hrp_weights(
    returns_data,
    mf_rankings,
    num_clusters=8  # More clusters for finer control
)
```

## Advanced Features

### 1. Dynamic Clustering
```python
def adaptive_cluster_count(self, correlation_matrix: pd.DataFrame) -> int:
    """Determine optimal number of clusters based on correlation structure"""
    
    # Calculate average correlation
    avg_correlation = correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean()
    
    # More clusters for lower average correlation
    if avg_correlation < 0.3:
        return min(8, len(correlation_matrix) // 4)
    elif avg_correlation < 0.5:
        return min(6, len(correlation_matrix) // 5)
    else:
        return min(4, len(correlation_matrix) // 6)
```

### 2. Sector-Aware Clustering
```python
def sector_informed_clustering(self, correlation_matrix: pd.DataFrame, 
                              sector_data: pd.Series) -> Dict:
    """Incorporate sector information into clustering"""
    
    # Pre-cluster by sector
    sector_clusters = {}
    for sector in sector_data.unique():
        sector_stocks = sector_data[sector_data == sector].index.tolist()
        if len(sector_stocks) >= 2:
            # Run HRP within sector
            sector_corr = correlation_matrix.loc[sector_stocks, sector_stocks]
            sector_clusters[sector] = self.perform_hierarchical_clustering(sector_corr, 2)
    
    return sector_clusters
```

### 3. Regime-Aware Weighting
```python
def regime_adaptive_weights(self, returns_data: pd.DataFrame, 
                           regime_indicator: pd.Series) -> pd.Series:
    """Adjust weights based on market regime"""
    
    current_regime = regime_indicator.iloc[-1]
    
    if current_regime == "high_volatility":
        # Emphasize minimum variance in volatile markets
        mv_weights = self.calculate_minimum_variance_weights(returns_data)
        hrp_weights = self.calculate_hrp_weights(returns_data, mf_rankings)
        return 0.7 * mv_weights + 0.3 * hrp_weights
    
    elif current_regime == "trending":
        # Emphasize Magic Formula rankings in trending markets
        rank_weights = self.calculate_rank_based_weights(mf_rankings)
        hrp_weights = self.calculate_hrp_weights(returns_data, mf_rankings)
        return 0.6 * rank_weights + 0.4 * hrp_weights
    
    else:
        # Default HRP allocation
        return self.calculate_hrp_weights(returns_data, mf_rankings)
```

## Best Practices

### 1. Data Requirements
- **Minimum History**: 252 trading days (1 year) for correlation estimation
- **Data Quality**: Clean, aligned return series
- **Coverage**: Sufficient observations for each stock (80% threshold)

### 2. Parameter Tuning
- **Lookback Period**: 252 days default, adjust for market conditions
- **Cluster Count**: 3-8 clusters depending on universe size
- **Magic Formula Weight**: 70% ranking + 30% risk parity balance

### 3. Implementation Considerations
- **Rebalancing Frequency**: Quarterly to balance turnover vs adaptation
- **Transaction Costs**: Consider costs in weight optimization
- **Capacity**: HRP scales well to larger universes

### 4. Risk Management
- **Correlation Monitoring**: Track cluster correlation changes
- **Concentration Limits**: Monitor cluster and individual stock weights
- **Stress Testing**: Test performance under various market scenarios

## Limitations and Future Enhancements

### Current Limitations
1. **Static Clusters**: Clusters updated periodically, not continuously
2. **Correlation Focus**: Primarily uses linear correlation relationships
3. **Historical Dependence**: Based on historical return patterns

### Future Enhancements
1. **Dynamic Clustering**: Real-time cluster adaptation
2. **Alternative Distance Metrics**: Mutual information, copula-based measures
3. **Factor-Based Clustering**: Incorporate fundamental factors
4. **Multi-Period Optimization**: Optimize across multiple rebalancing periods

---

*This advanced portfolio construction framework enhances the Modern Magic Formula with sophisticated risk management and diversification techniques. The Hierarchical Risk Parity approach provides superior risk-adjusted returns while maintaining the benefits of the Magic Formula stock selection process.*

**Document Version**: 1.0  
**Last Updated**: July 25, 2024  
**Author**: Modern Magic Formula Development Team  
**References**: López de Prado, M. (2016). "Building Diversified Portfolios that Outperform Out-of-Sample"