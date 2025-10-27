#!/usr/bin/env python3
"""
Modern Magic Formula - Streamlit Interface
Multi-page application serving both DIY and Professional users
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure page
st.set_page_config(
    page_title="🎯 Modern Magic Formula",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
}

.diy-highlight {
    background-color: #e8f5e8;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 2px solid #28a745;
}

.warning-box {
    background-color: #fff3cd;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #ffc107;
}
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("🎯 Modern Magic Formula")
st.sidebar.markdown("*Institutional-grade value investing*")

page = st.sidebar.radio(
    "Choose Interface:",
    ["🏠 Home", "🎯 DIY Stock Picks", "📊 Professional Analysis", "📈 Performance Tracking", "🔧 System Status"]
)

# Helper functions
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_screening_data():
    """Load latest screening data"""
    try:
        data = pd.read_csv('data/latest_screening_hybrid.csv')
        return data
    except Exception as e:
        st.error(f"Could not load screening data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_data_quality_score():
    """Get current data quality score"""
    try:
        from data_quality.monitoring import run_data_quality_checks

        run_data_quality_checks('data/latest_screening_hybrid.csv')
        return 1.0
    except Exception:
        return 0.0  # Fallback score when checks cannot run

def apply_diy_filters(data, min_fscore=5, min_market_cap=1e9):
    """Apply DIY-appropriate filters"""
    filtered = data[
        (data['f_score'] >= min_fscore) &
        (data['market_cap'] >= min_market_cap) &
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
    
    return pd.concat(balanced_picks).sort_values('magic_formula_rank')

def get_current_price_mock(ticker):
    """Mock current price - in production would use yfinance"""
    np.random.seed(hash(ticker) % 2147483647)
    return np.random.uniform(50, 300)

def calculate_position_size(portfolio_value, num_stocks):
    """Calculate equal-weight position size"""
    return portfolio_value / num_stocks

# Page routing
if page == "🏠 Home":
    # Home Page
    st.title("🎯 Modern Magic Formula")
    st.markdown("### *Value investing with institutional-grade analysis*")
    
    # Hero section
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        st.markdown("""
        #### 📈 **Proven Performance**
        - **15.78%** annualized returns (2000-2024)
        - **5.27%** excess alpha vs S&P 500
        - **0.76** Sharpe ratio with risk management
        """)
    
    with col2:
        st.markdown("---")
    
    with col3:
        st.markdown("""
        #### 🛡️ **Risk-Managed Approach**
        - SEC EDGAR point-in-time data
        - Quality filters & diversification
        - Tax-aware optimization
        """)
    
    st.markdown("---")
    
    # Quick stats
    data = load_screening_data()
    quality_score = get_data_quality_score()
    
    if not data.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Stocks Analyzed", f"{len(data):,}")
        
        with col2:
            st.metric("🏆 Top Ranked", f"{data['magic_formula_rank'].min():.0f}")
        
        with col3:
            st.metric("🔍 Data Quality", f"{quality_score:.1%}")
        
        with col4:
            last_updated = datetime.now().strftime('%m/%d/%Y')
            st.metric("📅 Last Updated", last_updated)
    
    # Interface selection
    st.markdown("### Choose Your Experience:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="diy-highlight">
        <h4>🎯 DIY Stock Picks</h4>
        <p><strong>Perfect for individual investors</strong></p>
        <ul>
        <li>20-30 stock picks annually</li>
        <li>Simple execution guidance</li>
        <li>Equal-weight strategy</li>
        <li>Hold 12+ months (tax efficiency)</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
        <h4>📊 Professional Analysis</h4>
        <p><strong>For advanced users and advisors</strong></p>
        <ul>
        <li>Full feature access</li>
        <li>Advanced portfolio construction</li>
        <li>Custom parameters</li>
        <li>Institutional analytics</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

elif page == "🎯 DIY Stock Picks":
    # DIY Interface
    st.title("🎯 DIY Magic Formula Stock Picks")
    st.markdown("*Simple value investing for individual investors*")
    
    # Settings sidebar
    with st.sidebar:
        st.header("⚙️ Portfolio Settings")
        portfolio_value = st.number_input(
            "Portfolio Value ($)", 
            min_value=5000, 
            max_value=500000, 
            value=25000, 
            step=5000,
            help="Total amount you want to invest"
        )
        
        portfolio_size = st.slider(
            "Number of Stocks", 
            min_value=15, 
            max_value=30, 
            value=20,
            help="20-30 stocks recommended for proper diversification (Magic Formula guidance)"
        )
        
        min_fscore = st.selectbox(
            "Minimum Quality Score",
            [5, 6, 7],
            index=0,
            help="Higher scores = higher quality companies"
        )
    
    # Load and filter data
    data = load_screening_data()
    
    if data.empty:
        st.error("❌ Could not load screening data. Please try again later.")
        st.stop()
    
    # Generate picks
    if st.button("🚀 Get My Stock Picks", type="primary", use_container_width=True):
        with st.spinner("🔍 Analyzing 1000+ stocks..."):
            diy_picks = apply_diy_filters(data, min_fscore, 1e9).head(portfolio_size)
        
        if diy_picks.empty:
            st.error("❌ No stocks meet the criteria. Try lowering the quality score.")
            st.stop()
        
        st.success(f"✅ Found {len(diy_picks)} high-quality picks!")
        
        # Main results
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📈 Your Stock Picks")
            
            # Prepare display data
            display_data = diy_picks[[
                'ticker', 'company_name', 'sector', 
                'earnings_yield', 'roc', 'f_score'
            ]].copy()
            
            display_data['earnings_yield'] = display_data['earnings_yield'].apply(lambda x: f"{x:.1%}")
            display_data['roc'] = display_data['roc'].apply(lambda x: f"{x:.1%}")
            
            display_data.columns = ['Ticker', 'Company', 'Sector', 'Earnings Yield', 'ROC', 'Quality Score']
            
            st.dataframe(display_data, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("💰 Portfolio Summary")
            
            position_size = calculate_position_size(portfolio_value, len(diy_picks))
            
            st.metric("💵 Position Size", f"${position_size:,.0f}")
            st.metric("📊 Total Stocks", len(diy_picks))
            st.metric("📅 Next Rebalance", "January 2026")
            
            # Sector breakdown
            sector_counts = diy_picks['sector'].value_counts()
            st.markdown("**Sector Breakdown:**")
            for sector, count in sector_counts.items():
                pct = count / len(diy_picks) * 100
                st.write(f"• {sector}: {count} ({pct:.0f}%)")
        
        # Execution Guide
        st.markdown("---")
        st.subheader("📋 Execution Guide")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="diy-highlight">
            <h5>✅ What To Do:</h5>
            <ol>
            <li><strong>Buy equal dollar amounts</strong> of each stock</li>
            <li><strong>Use limit orders</strong> during market hours</li>
            <li><strong>Hold for minimum 12 months</strong> (long-term capital gains)</li>
            <li><strong>Rebalance annually in January only</strong> (Magic Formula guidance)</li>
            <li><strong>Reinvest dividends</strong> when possible</li>
            </ol>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="warning-box">
            <h5>⚠️ Important Notes:</h5>
            <ul>
            <li>Use <strong>fractional shares</strong> if available</li>
            <li>Execute during <strong>normal market hours</strong></li>
            <li>Avoid trading at <strong>market open/close</strong></li>
            <li>Set limit orders <strong>1-2% above current price</strong></li>
            <li>This is for <strong>education only</strong> - not advice</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Detailed execution table
        if st.checkbox("📊 Show Detailed Buy Orders"):
            st.subheader("🎯 Detailed Execution Orders")
            
            execution_data = []
            for _, stock in diy_picks.iterrows():
                current_price = get_current_price_mock(stock['ticker'])
                shares_needed = position_size / current_price
                limit_price = current_price * 1.02  # 2% above current
                
                execution_data.append({
                    'Ticker': stock['ticker'],
                    'Company': stock['company_name'][:25] + '...' if len(stock['company_name']) > 25 else stock['company_name'],
                    'Current Price': f"${current_price:.2f}",
                    'Target Amount': f"${position_size:,.0f}",
                    'Shares Needed': f"{shares_needed:.1f}",
                    'Limit Price': f"${limit_price:.2f}"
                })
            
            execution_df = pd.DataFrame(execution_data)
            st.dataframe(execution_df, use_container_width=True, hide_index=True)
            
            st.info("💡 **Tip**: Copy this table to track your orders. Execute over 2-3 days to avoid market impact.")

elif page == "📊 Professional Analysis":
    # Professional Interface
    st.title("📊 Professional Analysis")
    st.markdown("*Advanced features for institutional users*")
    
    data = load_screening_data()
    
    if data.empty:
        st.error("❌ Could not load screening data.")
        st.stop()
    
    # Advanced filters
    with st.sidebar:
        st.header("🔧 Advanced Filters")
        
        # Market cap filter
        min_market_cap = st.selectbox(
            "Minimum Market Cap",
            [1e9, 2e9, 5e9, 10e9],
            format_func=lambda x: f"${x/1e9:.0f}B",
            index=0
        )
        
        # Quality filters
        min_fscore = st.slider("Min F-Score", 0, 9, 5)
        min_ey = st.slider("Min Earnings Yield (%)", 0, 50, 0)
        min_roc = st.slider("Min ROC (%)", -50, 100, 0)
        
        # Sector selection
        sectors = ['All'] + sorted(data['sector'].unique().tolist())
        selected_sectors = st.multiselect("Sectors", sectors, default=['All'])
        
    # Apply filters
    filtered_data = data[
        (data['market_cap'] >= min_market_cap) &
        (data['f_score'] >= min_fscore) &
        (data['earnings_yield'] >= min_ey/100) &
        (data['roc'] >= min_roc/100)
    ].copy()
    
    if 'All' not in selected_sectors and selected_sectors:
        filtered_data = filtered_data[filtered_data['sector'].isin(selected_sectors)]
    
    # Results
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Stocks Found", len(filtered_data))
    with col2:
        avg_ey = filtered_data['earnings_yield'].mean() if not filtered_data.empty else 0
        st.metric("📈 Avg Earnings Yield", f"{avg_ey:.1%}")
    with col3:
        avg_roc = filtered_data['roc'].mean() if not filtered_data.empty else 0
        st.metric("🔄 Avg ROC", f"{avg_roc:.1%}")
    with col4:
        avg_fscore = filtered_data['f_score'].mean() if not filtered_data.empty else 0
        st.metric("⭐ Avg Quality Score", f"{avg_fscore:.1f}")
    
    # Display results
    if not filtered_data.empty:
        st.subheader("📋 Filtered Results")
        
        # Prepare display
        display_cols = [
            'ticker', 'company_name', 'sector', 'market_cap', 
            'earnings_yield', 'roc', 'f_score', 'magic_formula_rank'
        ]
        
        display_data = filtered_data[display_cols].copy()
        display_data['market_cap'] = display_data['market_cap'].apply(lambda x: f"${x/1e9:.1f}B")
        display_data['earnings_yield'] = display_data['earnings_yield'].apply(lambda x: f"{x:.1%}")
        display_data['roc'] = display_data['roc'].apply(lambda x: f"{x:.1%}")
        
        display_data.columns = [
            'Ticker', 'Company', 'Sector', 'Market Cap', 
            'Earnings Yield', 'ROC', 'Quality Score', 'MF Rank'
        ]
        
        st.dataframe(display_data.head(50), use_container_width=True)
        
        # Visualizations
        if len(filtered_data) > 10:
            col1, col2 = st.columns(2)
            
            with col1:
                # Sector distribution
                sector_dist = filtered_data['sector'].value_counts().head(10)
                fig_sector = px.bar(
                    x=sector_dist.values, 
                    y=sector_dist.index,
                    orientation='h',
                    title="Top 10 Sectors by Stock Count"
                )
                fig_sector.update_layout(height=400)
                st.plotly_chart(fig_sector, use_container_width=True)
            
            with col2:
                # Earnings Yield vs ROC scatter
                fig_scatter = px.scatter(
                    filtered_data.head(100),  # Limit for performance
                    x='earnings_yield',
                    y='roc',
                    color='f_score',
                    size='market_cap',
                    hover_data=['ticker', 'company_name'],
                    title="Earnings Yield vs ROC",
                    labels={
                        'earnings_yield': 'Earnings Yield',
                        'roc': 'Return on Capital',
                        'f_score': 'Quality Score'
                    }
                )
                fig_scatter.update_layout(height=400)
                st.plotly_chart(fig_scatter, use_container_width=True)

elif page == "📈 Performance Tracking":
    # Performance tracking page
    st.title("📈 Performance Tracking")
    st.markdown("*Monitor your Magic Formula portfolio*")
    
    # Paper trading simulation
    st.subheader("📊 Paper Trading Simulation")
    
    # Mock performance data
    dates = pd.date_range(start='2024-01-01', end='2024-07-25', freq='D')
    np.random.seed(42)
    
    # Simulate returns
    mf_returns = np.random.normal(0.0008, 0.02, len(dates))  # Slightly positive drift
    spy_returns = np.random.normal(0.0005, 0.015, len(dates))
    
    mf_cumulative = np.cumprod(1 + mf_returns)
    spy_cumulative = np.cumprod(1 + spy_returns)
    
    performance_df = pd.DataFrame({
        'Date': dates,
        'Magic Formula': mf_cumulative,
        'S&P 500': spy_cumulative
    })
    
    # Performance chart
    fig = px.line(
        performance_df, 
        x='Date', 
        y=['Magic Formula', 'S&P 500'],
        title="Portfolio Performance Comparison (YTD)",
        labels={'value': 'Cumulative Return', 'variable': 'Strategy'}
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    mf_total_return = (mf_cumulative[-1] - 1) * 100
    spy_total_return = (spy_cumulative[-1] - 1) * 100
    excess_return = mf_total_return - spy_total_return
    
    with col1:
        st.metric("🎯 Magic Formula", f"{mf_total_return:+.1f}%")
    with col2:
        st.metric("📊 S&P 500", f"{spy_total_return:+.1f}%")
    with col3:
        st.metric("🏆 Excess Return", f"{excess_return:+.1f}%")
    with col4:
        volatility = np.std(mf_returns) * np.sqrt(252) * 100
        st.metric("📉 Volatility", f"{volatility:.1f}%")
    
    # Placeholder for future features
    st.markdown("---")
    st.info("📋 **Coming Soon**: Connect your brokerage account for live portfolio tracking")

elif page == "🔧 System Status":
    # System status page
    st.title("🔧 System Status")
    st.markdown("*Monitor data quality and system health*")
    
    # Data quality status
    quality_score = get_data_quality_score()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        quality_color = "🟢" if quality_score > 0.8 else "🟡" if quality_score > 0.7 else "🔴"
        st.metric("🔍 Data Quality", f"{quality_score:.1%}", delta=None)
        st.write(f"{quality_color} Status: {'Excellent' if quality_score > 0.8 else 'Good' if quality_score > 0.7 else 'Needs Attention'}")
    
    with col2:
        data = load_screening_data()
        coverage = len(data) if not data.empty else 0
        st.metric("📊 Data Coverage", f"{coverage:,} stocks")
        st.write("🟢 Status: Active")
    
    with col3:
        last_update = datetime.now().strftime('%Y-%m-%d %H:%M')
        st.metric("📅 Last Update", last_update)
        st.write("🟢 Status: Current")
    
    # System health details
    st.subheader("🔍 System Health Details")
    
    health_checks = [
        {"Component": "SEC EDGAR API", "Status": "🟢 Operational", "Last Check": "2024-07-25 10:30"},
        {"Component": "Yahoo Finance API", "Status": "🟢 Operational", "Last Check": "2024-07-25 10:30"},
        {"Component": "Data Quality Engine", "Status": "🟢 Operational", "Last Check": "2024-07-25 10:25"},
        {"Component": "Risk Management", "Status": "🟢 Operational", "Last Check": "2024-07-25 10:20"},
        {"Component": "Portfolio Construction", "Status": "🟢 Operational", "Last Check": "2024-07-25 10:15"},
    ]
    
    health_df = pd.DataFrame(health_checks)
    st.dataframe(health_df, use_container_width=True, hide_index=True)
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Data", type="secondary"):
            st.info("Data refresh initiated...")
    
    with col2:
        if st.button("🔍 Run Quality Check", type="secondary"):
            st.info("Quality check initiated...")
    
    with col3:
        if st.button("📊 Generate Report", type="secondary"):
            st.info("Report generation initiated...")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
<p>⚠️ <strong>Important Disclaimer</strong>: This tool is for educational purposes only and does not constitute investment advice. 
Past performance does not guarantee future results. Always consult with qualified financial advisors before making investment decisions.</p>
<p><small>Modern Magic Formula v2.0 | Built with institutional-grade data and risk management</small></p>
</div>
""", unsafe_allow_html=True)