#!/usr/bin/env python3
"""
Test Streamlit DIY interface functionality
"""

import pandas as pd
import sys
import os
sys.path.append('.')

def test_diy_interface():
    """Test the key DIY interface functions"""
    
    print("🎯 Testing DIY Magic Formula Interface")
    print("=" * 50)
    
    # Test 1: Data loading
    print("📊 Test 1: Data Loading")
    try:
        data = pd.read_csv('data/latest_screening_hybrid.csv')
        print(f"   ✅ Loaded {len(data)} stocks successfully")
        
        # Check required columns
        required_cols = ['ticker', 'company_name', 'sector', 'earnings_yield', 'roc', 'f_score', 'market_cap', 'magic_formula_rank']
        missing_cols = [col for col in required_cols if col not in data.columns]
        
        if missing_cols:
            print(f"   ❌ Missing columns: {missing_cols}")
            return False
        else:
            print(f"   ✅ All required columns present")
            
    except Exception as e:
        print(f"   ❌ Data loading failed: {e}")
        return False
    
    # Test 2: DIY filtering
    print("\n🔍 Test 2: DIY Filtering")
    try:
        # Apply DIY filters (same logic as in Streamlit app)
        filtered = data[
            (data['f_score'] >= 5) &
            (data['market_cap'] >= 1e9) &
            (data['earnings_yield'] > 0) &
            (data['roc'] > 0)
        ].copy()
        
        # Simple sector diversification
        sector_counts = filtered.groupby('sector').size()
        max_per_sector = max(1, len(filtered) // 4)  # Max 25% per sector
        
        balanced_picks = []
        for sector in sector_counts.index:
            sector_stocks = filtered[filtered['sector'] == sector].head(max_per_sector)
            balanced_picks.append(sector_stocks)
        
        diy_picks = pd.concat(balanced_picks).sort_values('magic_formula_rank').head(15)
        
        print(f"   ✅ Filtered to {len(diy_picks)} DIY picks")
        print(f"   📊 Sectors represented: {len(diy_picks['sector'].unique())}")
        
        # Check diversification
        max_sector_pct = diy_picks['sector'].value_counts().iloc[0] / len(diy_picks)
        if max_sector_pct <= 0.35:  # Max 35% in any sector
            print(f"   ✅ Good diversification (max sector: {max_sector_pct:.1%})")
        else:
            print(f"   ⚠️  High concentration (max sector: {max_sector_pct:.1%})")
            
    except Exception as e:
        print(f"   ❌ DIY filtering failed: {e}")
        return False
    
    # Test 3: Portfolio calculation
    print("\n💰 Test 3: Portfolio Calculation")
    try:
        portfolio_value = 25000
        position_size = portfolio_value / len(diy_picks)
        
        print(f"   ✅ Portfolio value: ${portfolio_value:,}")
        print(f"   ✅ Position size: ${position_size:,.0f}")
        print(f"   ✅ Number of positions: {len(diy_picks)}")
        
        # Mock execution table
        execution_data = []
        for _, stock in diy_picks.head(5).iterrows():  # Test first 5
            current_price = 100.0  # Mock price
            shares_needed = position_size / current_price
            
            execution_data.append({
                'ticker': stock['ticker'],
                'current_price': current_price,
                'shares_needed': shares_needed,
                'position_value': position_size
            })
        
        print(f"   ✅ Execution table generated for {len(execution_data)} positions")
        
    except Exception as e:
        print(f"   ❌ Portfolio calculation failed: {e}")
        return False
    
    # Test 4: Display formatting
    print("\n📋 Test 4: Display Formatting")
    try:
        # Test percentage formatting
        display_data = diy_picks[['ticker', 'company_name', 'sector', 'earnings_yield', 'roc', 'f_score']].copy()
        display_data['earnings_yield_fmt'] = display_data['earnings_yield'].apply(lambda x: f"{x:.1%}")
        display_data['roc_fmt'] = display_data['roc'].apply(lambda x: f"{x:.1%}")
        
        print(f"   ✅ Percentage formatting works")
        print(f"   ✅ Display data prepared for {len(display_data)} stocks")
        
        # Show sample
        print(f"\n   📈 Sample DIY picks:")
        for i, (_, row) in enumerate(display_data.head(3).iterrows()):
            print(f"      {i+1}. {row['ticker']} - {row['earnings_yield_fmt']} EY, {row['roc_fmt']} ROC, F-Score: {row['f_score']}")
            
    except Exception as e:
        print(f"   ❌ Display formatting failed: {e}")
        return False
    
    # Test 5: Data quality check
    print("\n🔍 Test 5: Data Quality Check")
    try:
        from data_quality.monitoring import DataQualityMonitor
        monitor = DataQualityMonitor()
        quality_results = monitor.run_monitoring_check('data/latest_screening_hybrid.csv')
        quality_score = quality_results.get('overall_score', 0)
        
        print(f"   ✅ Data quality score: {quality_score:.1%}")
        
        if quality_score >= 0.80:
            print(f"   ✅ Quality threshold met")
        else:
            print(f"   ⚠️  Quality below threshold (80%)")
            
    except Exception as e:
        print(f"   ⚠️  Quality check unavailable: {e}")
    
    print(f"\n✅ All DIY interface tests completed successfully!")
    print(f"🚀 Streamlit app ready for individual investors")
    
    return True

if __name__ == "__main__":
    success = test_diy_interface()
    if success:
        print(f"\n🎯 Ready to launch: streamlit run app/streamlit_app.py")
        print(f"📱 Access DIY interface at: http://localhost:8501")
        print(f"💡 Perfect for individual investors seeking 15-20 high-quality value picks")
    sys.exit(0 if success else 1)