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