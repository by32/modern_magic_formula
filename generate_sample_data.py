#!/usr/bin/env python3
"""Generate sample data for testing the Magic Formula screener without API keys."""

import pandas as pd
import json
import os
from datetime import datetime

def generate_sample_data():
    """Create realistic sample data for Magic Formula screening."""
    
    # Sample stock data with realistic financial metrics
    sample_stocks = [
        {
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "ebit": 123500000000,  # $123.5B EBIT
            "enterprise_value": 2800000000000,  # $2.8T Enterprise Value
            "market_cap": 2900000000000,  # $2.9T Market Cap
        },
        {
            "ticker": "MSFT", 
            "company_name": "Microsoft Corporation",
            "ebit": 89400000000,  # $89.4B EBIT
            "enterprise_value": 2200000000000,  # $2.2T Enterprise Value
            "market_cap": 2300000000000,  # $2.3T Market Cap
        },
        {
            "ticker": "GOOGL",
            "company_name": "Alphabet Inc.",
            "ebit": 76000000000,  # $76B EBIT
            "enterprise_value": 1600000000000,  # $1.6T Enterprise Value
            "market_cap": 1650000000000,  # $1.65T Market Cap
        },
        {
            "ticker": "BRK.B",
            "company_name": "Berkshire Hathaway Inc.",
            "ebit": 35000000000,  # $35B EBIT
            "enterprise_value": 700000000000,  # $700B Enterprise Value
            "market_cap": 750000000000,  # $750B Market Cap
        },
        {
            "ticker": "V",
            "company_name": "Visa Inc.",
            "ebit": 18500000000,  # $18.5B EBIT
            "enterprise_value": 450000000000,  # $450B Enterprise Value
            "market_cap": 475000000000,  # $475B Market Cap
        },
        {
            "ticker": "JNJ",
            "company_name": "Johnson & Johnson",
            "ebit": 25000000000,  # $25B EBIT
            "enterprise_value": 400000000000,  # $400B Enterprise Value
            "market_cap": 420000000000,  # $420B Market Cap
        }
    ]
    
    # Calculate Magic Formula metrics
    rows = []
    for stock in sample_stocks:
        # Calculate earnings yield (EBIT / Enterprise Value)
        earnings_yield = stock["ebit"] / stock["enterprise_value"]
        
        # Mock ROC calculation (Return on Capital)
        # In real implementation, this would use working capital + fixed assets
        roc = earnings_yield * 1.5  # Simple approximation for demo
        
        # Mock F-Score (Piotroski Score) - assign realistic scores
        f_scores = {"AAPL": 8, "MSFT": 7, "GOOGL": 6, "BRK.B": 8, "V": 9, "JNJ": 7}
        f_score = f_scores.get(stock["ticker"], 6)
        
        # Mock debt-to-equity ratios - realistic values for large companies
        debt_ratios = {"AAPL": 0.3, "MSFT": 0.2, "GOOGL": 0.1, "BRK.B": 0.2, "V": 0.4, "JNJ": 0.5}
        debt_to_equity = debt_ratios.get(stock["ticker"], 0.3)
        
        # Mock momentum data - some stocks with positive, some negative momentum
        momentum_data = {
            "AAPL": 0.15,    # +15% momentum
            "MSFT": 0.08,    # +8% momentum  
            "GOOGL": -0.05,  # -5% momentum
            "BRK.B": 0.12,   # +12% momentum
            "V": 0.22,       # +22% momentum
            "JNJ": 0.03      # +3% momentum
        }
        momentum_6m = momentum_data.get(stock["ticker"], 0.05)
        
        # Mock price strength scores based on momentum
        if momentum_6m > 0.15:
            price_strength_score = 3
        elif momentum_6m > 0.05:
            price_strength_score = 2
        elif momentum_6m > 0:
            price_strength_score = 1
        else:
            price_strength_score = 0
        
        # Mock cash flow quality metrics
        cash_flow_scores = {"AAPL": 4, "MSFT": 5, "GOOGL": 3, "BRK.B": 4, "V": 5, "JNJ": 4}
        cash_flow_quality_score = cash_flow_scores.get(stock["ticker"], 3)
        
        # Mock cash flow margins (as percentages, will be converted for display)
        ocf_margins = {"AAPL": 0.28, "MSFT": 0.35, "GOOGL": 0.22, "BRK.B": 0.15, "V": 0.45, "JNJ": 0.18}
        ocf_margin = ocf_margins.get(stock["ticker"], 0.20)
        
        fcf_margins = {"AAPL": 0.24, "MSFT": 0.32, "GOOGL": 0.18, "BRK.B": 0.12, "V": 0.42, "JNJ": 0.15}
        fcf_margin = fcf_margins.get(stock["ticker"], 0.17)
        
        # Operating cash flow to net income ratios
        ocf_to_ni_ratios = {"AAPL": 1.2, "MSFT": 1.4, "GOOGL": 1.1, "BRK.B": 1.3, "V": 1.5, "JNJ": 1.2}
        ocf_to_ni_ratio = ocf_to_ni_ratios.get(stock["ticker"], 1.2)
        
        # Mock sentiment scores (market sentiment proxy)
        sentiment_scores = {"AAPL": 3, "MSFT": 3, "GOOGL": 2, "BRK.B": 3, "V": 3, "JNJ": 2}
        sentiment_score = sentiment_scores.get(stock["ticker"], 2)
        
        # Calculate composite scores
        from etl.compute import compute_overall_quality_score, compute_value_trap_avoidance_score
        overall_quality_score = compute_overall_quality_score(f_score, cash_flow_quality_score, sentiment_score)
        value_trap_avoidance_score = compute_value_trap_avoidance_score(momentum_6m, f_score, cash_flow_quality_score)
        
        rows.append({
            "ticker": stock["ticker"],
            "company_name": stock["company_name"],
            "earnings_yield": earnings_yield,
            "roc": roc,
            "f_score": f_score,
            "debt_to_equity": debt_to_equity,
            "momentum_6m": momentum_6m,
            "price_strength_score": price_strength_score,
            "cash_flow_quality_score": cash_flow_quality_score,
            "sentiment_score": sentiment_score,
            "overall_quality_score": overall_quality_score,
            "value_trap_avoidance_score": value_trap_avoidance_score,
            "ocf_margin": ocf_margin,
            "fcf_margin": fcf_margin,
            "ocf_to_ni_ratio": ocf_to_ni_ratio,
            "market_cap": stock["market_cap"],
            "ebit": stock["ebit"],
            "enterprise_value": stock["enterprise_value"],
            "sector": "Technology",  # Simplified for sample data
            "last_updated": datetime.now().isoformat()
        })
    
    # Create DataFrame and sort by Magic Formula ranking
    df = pd.DataFrame(rows)
    df = df.sort_values(['earnings_yield', 'roc'], ascending=[False, False])
    df['magic_formula_rank'] = range(1, len(df) + 1)
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Save to CSV
    df.to_csv('data/latest_screening.csv', index=False)
    print(f"✅ Saved screening data to data/latest_screening.csv")
    
    # Save to JSON
    df.to_json('data/latest_screening.json', orient='records', date_format='iso')
    print(f"✅ Saved screening data to data/latest_screening.json")
    
    # Create metadata
    metadata = {
        "run_date": datetime.now().isoformat(),
        "total_stocks": len(df),
        "data_sources": ["Sample Data (for testing)"],
        "version": "1.0-sample"
    }
    
    with open('data/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Saved metadata to data/metadata.json")
    
    # Display results
    print(f"\n📊 Magic Formula Rankings:")
    print("="*60)
    for _, row in df.iterrows():
        print(f"{row['magic_formula_rank']:2d}. {row['ticker']:6s} - {row['company_name']}")
        print(f"    EY: {row['earnings_yield']*100:.2f}%  ROC: {row['roc']*100:.2f}%  MC: ${row['market_cap']/1e9:.0f}B")
        print()
    
    return df

if __name__ == "__main__":
    generate_sample_data()