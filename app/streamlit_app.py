import streamlit as st
import pandas as pd
import requests
import os

API_URL = os.getenv("API_URL", "http://api:8000")

st.title("Magic Formula Screener")

@st.cache_data(ttl=60*60)
def load_data():
    r = requests.get(f"{API_URL}/api/stocks/latest", timeout=30)
    r.raise_for_status()
    return pd.DataFrame(r.json())

df = load_data()

fscore_min = st.sidebar.slider("Minimum Piotroski F‑Score", 0, 9, 6)
momentum_min = st.sidebar.slider("Minimum 6‑mo Momentum %", -50, 100, 0)

filtered = df.query("f_score >= @fscore_min and momentum_6m >= @momentum_min")
st.dataframe(filtered, use_container_width=True)

ticker = st.selectbox("Inspect ticker", filtered["ticker"])
if ticker:
    st.write(f"### Details for {ticker}")
    # placeholder for charts
