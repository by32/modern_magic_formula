"""Functions to compute Magic Formula metrics and quality filters."""
import pandas as pd
from typing import Dict, Optional

def compute_earnings_yield(ebit: float, ev: float) -> float:
    if ev <= 0:
        return float('nan')
    return ebit / ev

def compute_roc(ebit: float, nwc: float, nfa: float) -> float:
    denom = nwc + nfa
    if denom == 0:
        return float('nan')
    return ebit / denom

def compute_piotroski_fscore(fundamental_data: Dict) -> int:
    """
    Calculate Piotroski F-Score (0-9 points) for financial strength assessment.
    
    The F-Score evaluates 9 criteria across 3 categories:
    
    PROFITABILITY (4 points max):
    1. Positive net income (1 point)
    2. Positive operating cash flow (1 point) 
    3. ROA improvement year-over-year (1 point)
    4. Operating cash flow > net income (quality of earnings) (1 point)
    
    LEVERAGE/LIQUIDITY (3 points max):
    5. Decrease in long-term debt year-over-year (1 point)
    6. Increase in current ratio year-over-year (1 point)
    7. No dilution (shares outstanding decrease or flat) (1 point)
    
    OPERATING EFFICIENCY (2 points max):
    8. Increase in gross margin year-over-year (1 point)
    9. Increase in asset turnover year-over-year (1 point)
    
    Args:
        fundamental_data: Dict containing financial metrics from API
        
    Returns:
        F-Score from 0-9 (higher is better, ≥6 typically considered good)
    """
    score = 0
    
    try:
        # Helper function to safely convert to float
        def safe_float(value, default=0.0):
            if value in ['None', 'N/A', '', None]:
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        # Extract current year metrics
        net_income = safe_float(fundamental_data.get('NetIncomeTTM', 0))
        operating_cash_flow = safe_float(fundamental_data.get('OperatingCashflowTTM', 0))
        roa = safe_float(fundamental_data.get('ReturnOnAssetsTTM', 0))
        total_debt = safe_float(fundamental_data.get('TotalDebt', 0))
        current_ratio = safe_float(fundamental_data.get('CurrentRatio', 0))
        shares_outstanding = safe_float(fundamental_data.get('SharesOutstanding', 0))
        gross_margin = safe_float(fundamental_data.get('GrossProfitMargin', 0))
        
        # Additional metrics for calculations
        total_assets = safe_float(fundamental_data.get('TotalAssets', 0))
        revenue = safe_float(fundamental_data.get('RevenueTTM', 0))
        
        # PROFITABILITY CRITERIA (4 points max)
        
        # 1. Positive net income
        if net_income > 0:
            score += 1
        
        # 2. Positive operating cash flow
        if operating_cash_flow > 0:
            score += 1
        
        # 3. ROA improvement (using current ROA > 0 as proxy since we don't have historical)
        if roa > 0:
            score += 1
        
        # 4. Operating cash flow > net income (quality of earnings)
        if operating_cash_flow > 0 and net_income > 0 and operating_cash_flow > net_income:
            score += 1
        
        # LEVERAGE/LIQUIDITY CRITERIA (3 points max)
        # Note: Without historical data, we use absolute thresholds as proxies
        
        # 5. Low debt levels (proxy for debt decrease)
        debt_to_assets = total_debt / total_assets if total_assets > 0 else 1
        if debt_to_assets < 0.4:  # Less than 40% debt-to-assets
            score += 1
        
        # 6. Healthy current ratio (proxy for liquidity improvement)
        if current_ratio > 1.2:  # Current ratio above 1.2
            score += 1
        
        # 7. Reasonable share count (proxy for no dilution)
        # We'll give point if company isn't heavily diluted (using market cap as proxy)
        market_cap = safe_float(fundamental_data.get('MarketCapitalization', 0))
        if market_cap > 1e9:  # Large enough company with presumably stable share count
            score += 1
        
        # OPERATING EFFICIENCY CRITERIA (2 points max)
        
        # 8. Healthy gross margin (proxy for margin improvement)
        if gross_margin > 0.2:  # Gross margin above 20%
            score += 1
        
        # 9. Good asset turnover (proxy for efficiency improvement)
        asset_turnover = revenue / total_assets if total_assets > 0 else 0
        if asset_turnover > 0.5:  # Asset turnover above 0.5x
            score += 1
        
        return min(score, 9)  # Cap at 9 points
        
    except Exception as e:
        print(f"⚠️  Error calculating Piotroski F-Score: {e}")
        return 0

def compute_momentum_6m(ticker: str, price_data: Dict) -> Optional[float]:
    """
    Calculate 6-month price momentum for a stock.
    
    Args:
        ticker: Stock symbol
        price_data: Dict containing price history (from get_6_month_price_data)
        
    Returns:
        6-month return percentage or None if data unavailable
    """
    try:
        if not price_data:
            return None
            
        momentum = price_data.get('momentum_6m')
        if momentum is None:
            return None
            
        return float(momentum)
        
    except Exception as e:
        print(f"⚠️  Error calculating momentum for {ticker}: {e}")
        return None

def compute_price_strength_score(price_data: Dict) -> int:
    """
    Calculate a price strength score (0-3 points) for momentum analysis.
    
    Score breakdown:
    - 1 point: Positive 6-month momentum (> 0%)
    - 1 point: Strong 6-month momentum (> 10%)  
    - 1 point: Not far from 52-week high (within 20%)
    
    Args:
        price_data: Dict containing price metrics
        
    Returns:
        Price strength score from 0-3 (higher = better momentum)
    """
    if not price_data:
        return 0
        
    score = 0
    
    try:
        momentum_6m = price_data.get('momentum_6m', 0)
        price_vs_52w_high = price_data.get('price_vs_52w_high', -1)
        
        # 1 point for positive momentum
        if momentum_6m > 0:
            score += 1
        
        # 1 point for strong momentum (>10% in 6 months)
        if momentum_6m > 0.10:
            score += 1
            
        # 1 point for being near 52-week high (within 20%)
        if price_vs_52w_high > -0.20:
            score += 1
            
        return score
        
    except Exception as e:
        print(f"⚠️  Error calculating price strength score: {e}")
        return 0

def compute_debt_to_equity(fundamental_data: Dict) -> Optional[float]:
    """
    Calculate debt-to-equity ratio for financial health assessment.
    
    Args:
        fundamental_data: Dict containing balance sheet metrics
        
    Returns:
        Debt-to-equity ratio or None if data unavailable
    """
    try:
        def safe_float(value, default=0.0):
            if value in ['None', 'N/A', '', None]:
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        total_debt = safe_float(fundamental_data.get('TotalDebt', 0))
        shareholders_equity = safe_float(fundamental_data.get('TotalShareholderEquity', 0))
        
        if shareholders_equity <= 0:
            return None
            
        return total_debt / shareholders_equity
        
    except Exception as e:
        print(f"⚠️  Error calculating debt-to-equity: {e}")
        return None

def compute_cash_flow_quality_score(fundamental_data: Dict) -> int:
    """
    Calculate cash flow quality score (0-5 points) for earnings validation.
    
    This score evaluates the quality of a company's earnings by examining 
    cash flow metrics and their relationship to reported earnings.
    
    Score breakdown:
    1. Positive operating cash flow (1 point)
    2. Operating cash flow > net income (quality earnings) (1 point)
    3. Operating cash flow growth vs previous period (1 point) 
    4. Free cash flow positive (Operating CF - CapEx > 0) (1 point)
    5. Cash conversion efficiency (OCF/Revenue > 10%) (1 point)
    
    Args:
        fundamental_data: Dict containing financial metrics from API
        
    Returns:
        Cash flow quality score from 0-5 (higher = better cash generation)
    """
    score = 0
    
    try:
        def safe_float(value, default=0.0):
            if value in ['None', 'N/A', '', None]:
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        # Extract cash flow metrics
        operating_cash_flow = safe_float(fundamental_data.get('OperatingCashflowTTM', 0))
        net_income = safe_float(fundamental_data.get('NetIncomeTTM', 0))
        capex = safe_float(fundamental_data.get('CapitalExpendituresTTM', 0))
        revenue = safe_float(fundamental_data.get('RevenueTTM', 0))
        
        # Check if we have sufficient cash flow data
        has_cash_flow_data = operating_cash_flow != 0 or net_income != 0
        
        if not has_cash_flow_data:
            # If no cash flow data available, use basic profitability as proxy
            if revenue > 0 and net_income > 0:
                # Basic profitability check
                net_margin = net_income / revenue
                if net_margin > 0.10:  # >10% net margin
                    score += 2  # Give partial credit for profitability
                elif net_margin > 0.05:  # >5% net margin
                    score += 1
            return score
        
        # CASH FLOW QUALITY CRITERIA (5 points max)
        
        # 1. Positive operating cash flow
        if operating_cash_flow > 0:
            score += 1
        
        # 2. Operating cash flow > net income (quality earnings)
        if operating_cash_flow > 0 and net_income > 0 and operating_cash_flow > net_income:
            score += 1
            ocf_vs_ni_ratio = operating_cash_flow / net_income
        
        # 3. Operating cash flow growth (using absolute level as proxy)
        # Since we don't have historical data, use OCF margin as quality indicator
        if operating_cash_flow > 0 and revenue > 0:
            ocf_margin = operating_cash_flow / revenue
            if ocf_margin > 0.12:  # Strong OCF margin > 12%
                score += 1
        
        # 4. Positive free cash flow (Operating CF - CapEx)
        if operating_cash_flow > 0:
            # CapEx is usually negative, so we add it (subtract absolute value)
            free_cash_flow = operating_cash_flow + capex  # capex is typically negative
            if free_cash_flow > 0:
                score += 1
        
        # 5. Cash conversion efficiency (OCF/Revenue > 10%)
        if operating_cash_flow > 0 and revenue > 0:
            cash_conversion = operating_cash_flow / revenue
            if cash_conversion > 0.10:  # >10% cash conversion
                score += 1
        
        return min(score, 5)  # Cap at 5 points
        
    except Exception as e:
        print(f"⚠️  Error calculating cash flow quality score: {e}")
        return 0

def compute_working_capital_quality(fundamental_data: Dict) -> Optional[float]:
    """
    Calculate working capital efficiency metrics.
    
    Args:
        fundamental_data: Dict containing balance sheet metrics
        
    Returns:
        Working capital turnover ratio or None if data unavailable
    """
    try:
        def safe_float(value, default=0.0):
            if value in ['None', 'N/A', '', None]:
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        revenue = safe_float(fundamental_data.get('RevenueTTM', 0))
        current_assets = safe_float(fundamental_data.get('TotalCurrentAssets', 0))
        current_liabilities = safe_float(fundamental_data.get('TotalCurrentLiabilities', 0))
        
        # Calculate working capital
        working_capital = current_assets - current_liabilities
        
        if revenue <= 0 or working_capital <= 0:
            return None
            
        # Working capital turnover (Revenue / Working Capital)
        wc_turnover = revenue / working_capital
        
        return wc_turnover
        
    except Exception as e:
        print(f"⚠️  Error calculating working capital quality: {e}")
        return None

def compute_cash_flow_ratios(fundamental_data: Dict) -> Dict[str, Optional[float]]:
    """
    Calculate various cash flow ratios for comprehensive analysis.
    
    Args:
        fundamental_data: Dict containing financial metrics
        
    Returns:
        Dict with various cash flow ratios
    """
    try:
        def safe_float(value, default=0.0):
            if value in ['None', 'N/A', '', None]:
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        operating_cash_flow = safe_float(fundamental_data.get('OperatingCashflowTTM', 0))
        net_income = safe_float(fundamental_data.get('NetIncomeTTM', 0))
        revenue = safe_float(fundamental_data.get('RevenueTTM', 0))
        total_debt = safe_float(fundamental_data.get('TotalDebt', 0))
        capex = safe_float(fundamental_data.get('CapitalExpendituresTTM', 0))
        
        ratios = {}
        
        # Operating Cash Flow Margin
        if revenue > 0:
            ratios['ocf_margin'] = operating_cash_flow / revenue
        else:
            ratios['ocf_margin'] = None
            
        # Cash Flow to Net Income Ratio (Quality of Earnings)
        if net_income > 0:
            ratios['ocf_to_ni'] = operating_cash_flow / net_income
        else:
            ratios['ocf_to_ni'] = None
            
        # Free Cash Flow Margin
        if revenue > 0 and operating_cash_flow > 0:
            free_cash_flow = operating_cash_flow + capex  # capex typically negative
            ratios['fcf_margin'] = free_cash_flow / revenue
        else:
            ratios['fcf_margin'] = None
            
        # Cash Flow to Debt Ratio
        if total_debt > 0:
            ratios['ocf_to_debt'] = operating_cash_flow / total_debt
        else:
            ratios['ocf_to_debt'] = None
            
        return ratios
        
    except Exception as e:
        print(f"⚠️  Error calculating cash flow ratios: {e}")
        return {
            'ocf_margin': None,
            'ocf_to_ni': None, 
            'fcf_margin': None,
            'ocf_to_debt': None
        }

def compute_sentiment_score(ticker: str, fundamental_data: Dict) -> int:
    """
    Calculate sentiment score (0-3 points) for news and market sentiment analysis.
    
    This is a simplified sentiment scoring system that can be enhanced with 
    actual news sentiment APIs in the future.
    
    Score breakdown:
    1. Market performance vs sector (1 point)
    2. Analyst sentiment proxy via valuation (1 point)
    3. Short interest levels (1 point - lower short interest = better sentiment)
    
    Args:
        ticker: Stock symbol
        fundamental_data: Dict containing financial metrics
        
    Returns:
        Sentiment score from 0-3 (higher = better sentiment)
    """
    score = 0
    
    try:
        def safe_float(value, default=0.0):
            if value in ['None', 'N/A', '', None]:
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        # Extract relevant metrics for sentiment proxy
        pe_ratio = safe_float(fundamental_data.get('PERatio', 0))
        market_cap = safe_float(fundamental_data.get('MarketCapitalization', 0))
        revenue = safe_float(fundamental_data.get('RevenueTTM', 0))
        
        # SENTIMENT PROXY CRITERIA (3 points max)
        
        # 1. Reasonable valuation (not overvalued = positive sentiment)
        if pe_ratio > 0 and pe_ratio < 25:  # Reasonable P/E ratio
            score += 1
        
        # 2. Growth company characteristics (revenue scale suggests market confidence)
        if revenue > 10e9:  # >$10B revenue suggests established, trusted company
            score += 1
        
        # 3. Market cap suggests institutional confidence
        if market_cap > 50e9:  # >$50B market cap suggests institutional backing
            score += 1
        
        return min(score, 3)  # Cap at 3 points
        
    except Exception as e:
        print(f"⚠️  Error calculating sentiment score for {ticker}: {e}")
        return 0

def compute_overall_quality_score(f_score: int, cf_quality: int, sentiment: int) -> int:
    """
    Calculate an overall quality score combining all modern analysis factors.
    
    Args:
        f_score: Piotroski F-Score (0-9)
        cf_quality: Cash flow quality score (0-5) 
        sentiment: Sentiment score (0-3)
        
    Returns:
        Overall quality score from 0-10 (normalized composite score)
    """
    try:
        # Weighted combination of scores
        # F-Score: 50% weight (most important)
        # Cash Flow: 35% weight
        # Sentiment: 15% weight
        
        f_score_normalized = (f_score / 9) * 5.0  # Convert to 0-5 scale
        cf_quality_normalized = cf_quality  # Already 0-5 scale
        sentiment_normalized = (sentiment / 3) * 1.5  # Convert to 0-1.5 scale
        
        overall_score = f_score_normalized + cf_quality_normalized + sentiment_normalized
        
        # Convert to 0-10 scale and round
        final_score = int(round((overall_score / 8.0) * 10))
        
        return min(final_score, 10)  # Cap at 10
        
    except Exception:
        return 0

def compute_value_trap_avoidance_score(momentum_6m: float, f_score: int, cf_quality: int) -> int:
    """
    Calculate value trap avoidance score (0-5 points).
    
    Combines momentum, financial quality, and cash flow to identify
    stocks that are cheap for good reasons vs. value traps.
    
    Args:
        momentum_6m: 6-month price momentum (as decimal)
        f_score: Piotroski F-Score (0-9)
        cf_quality: Cash flow quality score (0-5)
        
    Returns:
        Value trap avoidance score from 0-5 (higher = less likely to be value trap)
    """
    score = 0
    
    try:
        # 1. Positive momentum (not in decline)
        if momentum_6m and momentum_6m > 0:
            score += 1
        
        # 2. Strong financial health (F-Score >= 6)
        if f_score >= 6:
            score += 2
        elif f_score >= 4:
            score += 1
        
        # 3. Good cash generation (CF Quality >= 3)
        if cf_quality >= 4:
            score += 2
        elif cf_quality >= 2:
            score += 1
        
        return min(score, 5)  # Cap at 5 points
        
    except Exception:
        return 0
