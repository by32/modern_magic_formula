#!/usr/bin/env python3
"""
Simple test version of Streamlit app to diagnose deployment issues
"""

import streamlit as st
import pandas as pd
import numpy as np
import os

# Configure page
st.set_page_config(
    page_title="🎯 Modern Magic Formula - Test",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Modern Magic Formula - Test Mode")

# Test data loading
st.header("📊 Data Loading Test")

try:
    # Check if data file exists
    data_file = 'data/latest_screening_hybrid.csv'
    if os.path.exists(data_file):
        st.success(f"✅ Data file found: {data_file}")
        
        # Try to load data
        data = pd.read_csv(data_file)
        st.success(f"✅ Data loaded successfully: {len(data)} rows")
        st.write(f"Columns: {list(data.columns)}")
        
        # Show first few rows
        st.subheader("Sample Data")
        st.dataframe(data.head())
        
    else:
        st.error(f"❌ Data file not found: {data_file}")
        st.write("Available files:")
        if os.path.exists('data'):
            files = os.listdir('data')
            for f in files:
                st.write(f"- {f}")
        else:
            st.write("No data directory found")
            
except Exception as e:
    st.error(f"❌ Error loading data: {e}")

# Test basic functionality
st.header("🧪 Basic Functionality Test")
st.write("If you can see this message, basic Streamlit functionality is working!")

# Show environment info
st.header("🔧 Environment Info")
st.write(f"Python path: {os.getcwd()}")
st.write(f"Available packages:")
try:
    import sys
    st.write("- streamlit ✅")
    st.write("- pandas ✅") 
    st.write("- numpy ✅")
    try:
        import plotly
        st.write("- plotly ✅")
    except:
        st.write("- plotly ❌")
    
    try:
        import yfinance
        st.write("- yfinance ✅")
    except:
        st.write("- yfinance ❌")
        
except Exception as e:
    st.error(f"Error checking packages: {e}")