import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="Magic Formula Screener",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Magic Formula Stock Screener")

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    """Load screening data from static files"""
    try:
        # Load from data directory
        if os.path.exists('data/latest_screening.csv'):
            df = pd.read_csv('data/latest_screening.csv')
            with open('data/metadata.json', 'r') as f:
                metadata = json.load(f)
            return df, metadata
        else:
            # Create sample data for demo
            st.warning("📁 No screening data found. Run the ETL process to generate data.")
            sample_data = {
                'ticker': ['AAPL', 'MSFT', 'GOOG'],
                'company_name': ['Apple Inc.', 'Microsoft Corp.', 'Alphabet Inc.'],
                'earnings_yield': [0.05, 0.07, 0.04],
                'roc': [0.25, 0.30, 0.15],
                'market_cap': [2800000000000, 2200000000000, 1500000000000],
                'magic_formula_rank': [2, 1, 3],
                'last_updated': [datetime.now().isoformat()] * 3
            }
            df = pd.DataFrame(sample_data)
            metadata = {"run_date": "Sample data", "total_stocks": 3}
            return df, metadata
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), {}

# Load data
df, metadata = load_data()

if not df.empty:
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Display last update info
    if metadata.get('run_date'):
        st.sidebar.info(f"📅 Last updated: {metadata['run_date'][:19]}")
    
    # Market cap filter
    if 'market_cap' in df.columns:
        market_cap_billions = df['market_cap'] / 1e9
        min_market_cap = st.sidebar.slider(
            "Minimum Market Cap ($B)", 
            0, int(market_cap_billions.max()), 
            value=1
        )
        df = df[market_cap_billions >= min_market_cap]
    
    # Earnings Yield filter
    if 'earnings_yield' in df.columns:
        ey_min = st.sidebar.slider(
            "Minimum Earnings Yield", 
            float(df['earnings_yield'].min()), 
            float(df['earnings_yield'].max()), 
            value=float(df['earnings_yield'].min())
        )
        df = df[df['earnings_yield'] >= ey_min]
    
    # ROC filter
    if 'roc' in df.columns:
        roc_min = st.sidebar.slider(
            "Minimum ROC", 
            float(df['roc'].min()), 
            float(df['roc'].max()), 
            value=float(df['roc'].min())
        )
        df = df[df['roc'] >= roc_min]
    
    # Piotroski F-Score filter
    if 'f_score' in df.columns:
        f_score_min = st.sidebar.slider(
            "Minimum F-Score (Quality Filter)", 
            0, 9, 
            value=6,
            help="Piotroski F-Score: 9-point financial strength score (≥6 recommended)"
        )
        df = df[df['f_score'] >= f_score_min]
    
    # Debt-to-Equity filter
    if 'debt_to_equity' in df.columns:
        # Only show filter if we have debt data
        has_debt_data = df['debt_to_equity'].notna().sum() > 0
        if has_debt_data:
            debt_max = st.sidebar.slider(
                "Maximum Debt-to-Equity", 
                0.0, 2.0, 
                value=1.0,
                step=0.1,
                help="Lower debt-to-equity ratios indicate better financial health"
            )
            df = df[df['debt_to_equity'].fillna(0) <= debt_max]
    
    # Momentum filters
    if 'momentum_6m' in df.columns:
        has_momentum_data = df['momentum_6m'].notna().sum() > 0
        if has_momentum_data:
            st.sidebar.subheader("📈 Momentum Filters")
            
            # 6-month momentum filter
            momentum_min = st.sidebar.slider(
                "Minimum 6M Momentum (%)", 
                -50, 100, 
                value=0,
                step=5,
                help="6-month price momentum (0% = only positive momentum stocks)"
            )
            df = df[df['momentum_6m'].fillna(-1) >= momentum_min/100]
            
            # Price strength score filter
            if 'price_strength_score' in df.columns:
                strength_min = st.sidebar.slider(
                    "Minimum Price Strength Score", 
                    0, 3, 
                    value=1,
                    help="Price strength score: 0-3 points (momentum + near highs)"
                )
                df = df[df['price_strength_score'].fillna(0) >= strength_min]
    
    # Cash flow quality filters
    if 'cash_flow_quality_score' in df.columns:
        has_cf_data = df['cash_flow_quality_score'].notna().sum() > 0
        if has_cf_data:
            st.sidebar.subheader("💰 Cash Flow Quality")
            
            # Cash flow quality score filter
            cf_quality_min = st.sidebar.slider(
                "Minimum Cash Flow Quality Score", 
                0, 5, 
                value=3,
                help="Cash flow quality score: 0-5 points (earnings backed by cash)"
            )
            df = df[df['cash_flow_quality_score'].fillna(0) >= cf_quality_min]
            
            # Operating cash flow margin filter
            if 'ocf_margin' in df.columns:
                has_ocf_margin = df['ocf_margin'].notna().sum() > 0
                if has_ocf_margin:
                    ocf_margin_min = st.sidebar.slider(
                        "Minimum OCF Margin (%)", 
                        0, 50, 
                        value=10,
                        step=5,
                        help="Operating cash flow as % of revenue (higher = better cash generation)"
                    )
                    df = df[df['ocf_margin'].fillna(0) >= ocf_margin_min/100]
    
    # Overall quality and sentiment filters
    if 'overall_quality_score' in df.columns:
        has_quality_data = df['overall_quality_score'].notna().sum() > 0
        if has_quality_data:
            st.sidebar.subheader("🎯 Overall Quality")
            
            # Overall quality score filter
            quality_min = st.sidebar.slider(
                "Minimum Overall Quality Score", 
                0, 10, 
                value=7,
                help="Composite quality score: 0-10 (combines F-Score + Cash Flow + Sentiment)"
            )
            df = df[df['overall_quality_score'].fillna(0) >= quality_min]
            
            # Value trap avoidance filter
            if 'value_trap_avoidance_score' in df.columns:
                trap_avoidance_min = st.sidebar.slider(
                    "Minimum Value Trap Avoidance Score", 
                    0, 5, 
                    value=3,
                    help="Value trap avoidance: 0-5 (momentum + quality + cash flow)"
                )
                df = df[df['value_trap_avoidance_score'].fillna(0) >= trap_avoidance_min]
    
    # Number of results filter
    max_results = st.sidebar.number_input(
        "Max Results (Top N)", 
        min_value=10, 
        max_value=len(df) if len(df) > 0 else 1000, 
        value=min(100, len(df)) if len(df) > 0 else 100,
        step=10,
        help="Limit results to the top N ranked stocks"
    )
    df = df.head(max_results)
    
    # Main content
    st.subheader(f"📊 {len(df)} stocks found")
    
    # Format data for display
    display_df = df.copy()
    if 'market_cap' in display_df.columns:
        display_df['market_cap_billions'] = (display_df['market_cap'] / 1e9).round(1)
        display_df = display_df.drop('market_cap', axis=1)
    if 'earnings_yield' in display_df.columns:
        display_df['earnings_yield'] = (display_df['earnings_yield'] * 100).round(2)
    if 'roc' in display_df.columns:
        display_df['roc'] = (display_df['roc'] * 100).round(2)
    if 'momentum_6m' in display_df.columns:
        display_df['momentum_6m'] = (display_df['momentum_6m'] * 100).round(1)
    if 'debt_to_equity' in display_df.columns:
        display_df['debt_to_equity'] = display_df['debt_to_equity'].round(2)
    if 'ocf_margin' in display_df.columns:
        display_df['ocf_margin'] = (display_df['ocf_margin'] * 100).round(1)
    if 'fcf_margin' in display_df.columns:
        display_df['fcf_margin'] = (display_df['fcf_margin'] * 100).round(1)
    if 'ocf_to_ni_ratio' in display_df.columns:
        display_df['ocf_to_ni_ratio'] = display_df['ocf_to_ni_ratio'].round(2)
    
    st.dataframe(display_df, use_container_width=True)
    
    # Export functionality
    st.subheader("📤 Export Results")
    csv_download = df.to_csv(index=False)
    st.download_button(
        label="💾 Download CSV",
        data=csv_download,
        file_name=f"magic_formula_screening_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

else:
    st.error("❌ No data available. Please run the ETL process first.")

# Footer
st.markdown("---")
st.markdown("📊 Magic Formula Screener | ⚠️ For educational purposes only")