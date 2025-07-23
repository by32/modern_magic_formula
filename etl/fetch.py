"""Data-fetching utilities for external APIs."""
import requests, os, time, logging

def get_alpha_vantage_fundamentals(ticker: str, api_key: str):
    url = "https://www.alphavantage.co/query"
    params = {"function": "OVERVIEW", "symbol": ticker, "apikey": api_key}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()
