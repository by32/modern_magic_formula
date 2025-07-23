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
        
        rows.append({
            "ticker": stock["ticker"],
            "company_name": stock["company_name"],
            "earnings_yield": earnings_yield,
            "roc": roc,
            "market_cap": stock["market_cap"],
            "ebit": stock["ebit"],
            "enterprise_value": stock["enterprise_value"],
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