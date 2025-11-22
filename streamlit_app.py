#!/usr/bin/env python3
"""Streamlined Streamlit app for exploring the latest screening results."""

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


DATA_PATH = Path("data/latest_screening.csv")


@st.cache_data(show_spinner=False)
def load_screening_data(path: Path) -> pd.DataFrame:
    """Load the latest screening output as a DataFrame."""

    df = pd.read_csv(path)

    numeric_columns = [
        "magic_formula_rank",
        "earnings_yield",
        "roc",
        "f_score",
        "debt_to_equity",
        "momentum_6m",
        "price_strength_score",
        "cash_flow_quality_score",
        "sentiment_score",
        "overall_quality_score",
        "value_trap_avoidance_score",
        "ocf_margin",
        "fcf_margin",
        "ocf_to_ni_ratio",
        "market_cap",
        "ebit",
        "enterprise_value",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    return df


def format_percentage(value: float) -> str:
    """Format a decimal value as a percentage string."""

    if value is None or np.isnan(value):
        return "–"

    return f"{value * 100:.2f}%"


def format_number(value: float) -> str:
    """Format a large numeric value with abbreviations."""

    if value is None or np.isnan(value):
        return "–"

    magnitude = 0
    while abs(value) >= 1000 and magnitude < 4:
        value /= 1000.0
        magnitude += 1

    suffixes = {0: "", 1: "K", 2: "M", 3: "B", 4: "T"}
    return f"{value:.2f}{suffixes[magnitude]}"


def main() -> None:
    st.set_page_config(
        page_title="🎯 Modern Magic Formula",
        page_icon="🎯",
        layout="wide",
    )

    st.title("🎯 Modern Magic Formula Screener")
    st.caption("Explore the latest rankings produced by the simplified ETL pipeline.")

    if not DATA_PATH.exists():
        st.error(
            "❌ Could not find the latest screening output. Ensure the ETL pipeline has "
            "produced `data/latest_screening.csv`."
        )

        data_dir = DATA_PATH.parent
        if data_dir.exists():
            st.write("Available files in `data/`:")
            for file in sorted(data_dir.iterdir()):
                st.write(f"- {file.name}")
        return

    data = load_screening_data(DATA_PATH)

    st.sidebar.header("Filters")

    rank_series = data["magic_formula_rank"].dropna()
    if rank_series.empty:
        st.warning("No ranking information available in the dataset.")
        return

    min_rank = int(rank_series.min())
    max_rank = int(rank_series.max())
    rank_range = st.sidebar.slider(
        "Magic Formula Rank",
        min_value=min_rank,
        max_value=max_rank,
        value=(min_rank, min(min_rank + 49, max_rank)),
    )

    sectors = sorted(data["sector"].dropna().unique())
    selected_sectors = st.sidebar.multiselect(
        "Sectors",
        options=sectors,
        default=sectors,
    )

    f_score_series = data["f_score"].dropna()
    if f_score_series.empty:
        f_score_min, f_score_max = 0, 9
    else:
        f_score_min = int(f_score_series.min())
        f_score_max = int(f_score_series.max())
    min_f_score = st.sidebar.slider(
        "Minimum Piotroski F-Score",
        min_value=f_score_min,
        max_value=f_score_max,
        value=min(max(6, f_score_min), f_score_max),
    )

    search_term = st.sidebar.text_input("Search ticker or company", "").strip()

    filtered = data.copy()
    filtered = filtered[filtered["magic_formula_rank"].between(*rank_range)]

    if selected_sectors:
        filtered = filtered[filtered["sector"].isin(selected_sectors)]

    filtered = filtered[filtered["f_score"] >= min_f_score]

    if search_term:
        filtered = filtered[
            filtered["ticker"].str.contains(search_term, case=False, na=False)
            | filtered["company_name"].str.contains(search_term, case=False, na=False)
        ]

    st.subheader("Portfolio Snapshot")
    total_companies = len(filtered)
    avg_earnings_yield = filtered["earnings_yield"].mean()
    avg_roc = filtered["roc"].mean()
    avg_quality = filtered["overall_quality_score"].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Companies", f"{total_companies}")
    col2.metric("Avg. Earnings Yield", format_percentage(avg_earnings_yield))
    col3.metric("Avg. Return on Capital", format_percentage(avg_roc))
    col4.metric("Avg. Quality Score", f"{avg_quality:.2f}" if not np.isnan(avg_quality) else "–")

    st.subheader("Ranking Table")
    if total_companies == 0:
        st.info("No companies match the current filters. Adjust the filters to see results.")
        return

    display_columns = [
        "magic_formula_rank",
        "ticker",
        "company_name",
        "sector",
        "earnings_yield",
        "roc",
        "f_score",
        "overall_quality_score",
        "value_trap_avoidance_score",
        "market_cap",
        "enterprise_value",
        "last_updated",
    ]

    available_columns = [col for col in display_columns if col in filtered.columns]
    styled = filtered.sort_values("magic_formula_rank")[available_columns].copy()

    percentage_columns = {"earnings_yield", "roc"}
    for column in percentage_columns & set(styled.columns):
        styled[column] = styled[column].map(format_percentage)

    for column in {"market_cap", "enterprise_value"} & set(styled.columns):
        styled[column] = styled[column].map(format_number)

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Data sourced from the latest execution of the streamlined ETL pipeline. "
        "Metrics are provided for quick ranking review and do not include advanced diagnostics."
    )


if __name__ == "__main__":
    main()
