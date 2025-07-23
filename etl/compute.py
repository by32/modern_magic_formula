"""Functions to compute Magic Formula metrics and quality filters."""
import pandas as pd

def compute_earnings_yield(ebit: float, ev: float) -> float:
    if ev <= 0:
        return float('nan')
    return ebit / ev

def compute_roc(ebit: float, nwc: float, nfa: float) -> float:
    denom = nwc + nfa
    if denom == 0:
        return float('nan')
    return ebit / denom
