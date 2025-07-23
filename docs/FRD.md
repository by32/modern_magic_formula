# Functional Requirements Document (FRD)

## 1 Overview
The system identifies investable equities that satisfy the Magic Formula (high ROC, high Earnings Yield) and augments results with quality‑control filters to avoid value traps.

## 2 User stories
* **U1** – *As an investor I want to see the weekly list of top‑ranked Magic Formula stocks so that I can research new ideas.*
* **U2** – *As an investor I want to exclude companies with poor Piotroski F‑Scores so that financially distressed firms are filtered out.*
* **U3** – *As an investor I want to compare this week’s list with last week’s to understand changes over time.*

## 3 Functional requirements
| ID | Description | Criticality |
|----|-------------|-------------|
| F1 | Weekly ETL job completes in < 5 min for 1 000 tickers | Must |
| F2 | UI table supports column sort/filter, csv/json export | Must |
| F3 | Delta endpoint `/api/deltas/latest` returns JSON diff | Must |
| F4 | Drill‑down shows price chart, revenue/EBIT trend, news sentiment | Should |
| F5 | Auth optional via reverse‑proxy | Could |

## 4 Business rules
* Universe ≥ $200 M market cap, non‑financials
* Earnings Yield = EBIT / EV, ROC = EBIT / (NWC + NFA)
* Exclude negative EBIT or EV ≤ 0
* Momentum filter: keep only top 50 % 6‑month return
* Piotroski F‑Score threshold configurable (default ≥ 6)

## 5 Glossary
* **EBIT** – Earnings Before Interest & Tax  
* **EV** – Enterprise Value  
* **ROC** – Return on Capital  
* **F‑Score** – Piotroski nine‑point quality score  
