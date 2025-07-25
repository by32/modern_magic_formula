# **Action‑oriented improvement plan (Markdown version)**

Below is the same set of practical recommendations, rewritten fully in Markdown so you can paste it straight into GitHub, Notion, or a README.

---

## **1 Move to point‑in‑time fundamentals & extend the back‑test**

### **1.1 Why**

*Eliminate look‑ahead bias* (using data that were not yet published) and *increase statistical power* by covering several market cycles.

### **1.2 Data sources**

* **WRDS → Compustat Snapshot** (quarterly \+ annual point‑in‑time tables)  
* **S\&P Capital IQ PIT** or **FactSet RBICS PIT** (commercial alternatives)

### **1.3 Implementation steps**

\# pseudocode: build a point‑in‑time fundamentals table  
import wrds, pandas as pd

db \= wrds.Connection()  
fund \= db.raw\_sql("""  
    SELECT gvkey, datadate, rdq, at, dltt, ib, sale  
    FROM comp.fundq\_snapshot  
    WHERE datadate \>= '1999‑01‑01'  
""")

\# SEC filing‑date lags  
SEC\_LAG \= { "large\_acc": 60, "acc": 75, "non\_acc": 90 }  \# calendar days  
fund\["lag\_days"\] \= fund\["filing\_status"\].map(SEC\_LAG)  
fund\["available\_dt"\] \= fund\["rdq"\] \+ pd.to\_timedelta(fund\["lag\_days"\], "D")

* Merge price and fundamentals **only when `evaluation_date ≥ available_dt`**.  
* Re‑compute quarterly scores back to **Jan 2000** (earlier if your data license allows).  
* Store **monthly total‑return series** for performance metrics (Sharpe, t‑stats).

### **1.4 Tests**

* Compare “live” ranks produced each quarter to historical Bloomberg / Capital IQ snapshots.  
* Sanity‑check the factor IC (information coefficient) sign every year—e.g., EBIT/EV should stay positive \> 60 % of the time.

### **1.5 Effort**

*Medium* (one‑off ETL \+ nightly delta load).

---

## **2 Replace the static Russell 1000 list (kill survivorship bias)**

1. **Download** the *quarterly* “Constituents & Weights” spreadsheets from FTSE Russell.  
2. Concatenate into a single table keyed on `(effective_date, ticker)`.  
3. At each rebalance, **inner‑join** your candidate universe to the list that was in force on that date.  
4. Optionally broaden coverage to the **top 3 000** US common shares (`crsp.shrcd ∈ {10,11}`) with:  
   * Free‑float cap ≥ $750 m  
   * 20‑day median **$ADV \> $5 m**

*Effort: Low* (one parsing script).

---

## **3 Validate or optimise factor weights**

| Step | What to do | Tooling |
| ----- | ----- | ----- |
| **Baseline** | Z‑score each sub‑factor & take the arithmetic mean | `pandas` |
| **Grid search** | `TimeSeriesSplit(n_splits=5, gap=4)`; maximise out‑of‑sample **IR** or top‑decile **IC t‑stat** | `scikit‑learn` |
| **Walk‑forward** | Re‑estimate weights every December on the prior 10 years, then freeze for the next calendar year | custom |
| **Robustness reporting** | Publish equal‑weight vs. CV‑weight results | markdown / Jupyter |

*Effort: Low.*

---

## **4 Model realistic implementation costs**

**Half‑spread cost**  
cost \= 0.5 \* quoted\_spread \* shares

1. *Data:* IEX Cloud or Polygon 1‑min top‑of‑book.  
2. **Price‑impact cost**  
   MI=η σQ/ADV  
   where  
   * η≈0.5 for US equities  
   * σ \= 20‑day realised volatility  
   * Q \= shares to trade  
3. **Capacity test** – reject trades where Q/ADV\>8%.  
4. **Inject costs** at each simulated fill (not end‑of‑period lump).

*Effort: Medium* (need intraday quotes, but one‑time).

---

## **5 Add beta, size & sector risk guards**

* **β filter** – single‑stock β (252 d vs SPY) ∈ 0, 2; portfolio β within ±0.10 of 1\.  
* **Sector cap** – no GICS sector \> 25 % of NAV (`PyPortfolioOpt` → `add_sector_constraints`).  
* **Size floor** – market‑cap ≥ $1 bn.

*Effort: Low.*

---

## **6 Track after‑tax performance & turnover**

1. **Lot‑level tracking** (`buy_dt`, `shares`, `cost_basis`).  
2. Label each sale **STCG** (\< 365 d) or **LTCG**; apply current top US marginal rates (40.8 % vs 23.8 %).  
3. Report **pre‑tax CAGR**, **after‑tax CAGR**, **tax drag**, and **annual turnover %**.

*Effort: Medium.*

---

## **7 Run a pure‑value sleeve for comparison**

* Maintain two books side‑by‑side:  
  * **Modern score** (Value \+ Quality \+ Momentum)  
  * **Classic Greenblatt** (Value only)  
* Overlay 50 / 50 or optimise the weights via minimum variance.  
* Compare **drawdown statistics** and **tail correlations**.

*Effort: Trivial* once factors exist.

---

## **8 Automate data‑quality checks**

### **8.1 Great Expectations**

* **Expectation suite** examples  
  * `shares_outstanding > 0`  
  * `ebit` not null  
  * Piotroski sub‑metrics ∈ {0, 1}

### **8.2 CI / alerts**

1. **GitHub Actions** nightly:  
   * Query yesterday’s WRDS deltas  
   * Run GE suite  
   * Post Slack alert on failure  
2. **Fallback logic** – if a required item is **missing on rebalance day**, *drop the stock* instead of defaulting to 0\.

*Effort: Low → Medium* (HTML reporting optional).

---

## **9 Optional high‑leverage upgrades**

| Upgrade | Benefit |
| ----- | ----- |
| **Liquidity‑weighted sizing** | Reduces market‑impact cost |
| **Hierarchical Risk Parity weights** | Diversifies idiosyncratic shocks |
| **Staggered re‑balance** (trade ⅕ each day over a week) | Lowers footprint and signalling risk |

---

## **10 Suggested timeline**

| Phase | Scope | Indicative duration |
| ----- | ----- | ----- |
| **0** | Load PIT data, build rolling universe, *re‑create 2021‑24* results to validate pipeline | 1‑2 weeks |
| **1** | Extend to 2000+, implement β/sector caps, equal‑weight factors, cost model | 4‑6 weeks |
| **2** | Cross‑validate factor weights, add tax engine, capacity tests, GE pipeline | Ongoing |
| **3** | Review net alpha (\> 2 σ). If good, move to *paper trading* with real execution cost capture | — |

---

### **Bottom line**

With these concrete steps you **remove look‑ahead, survivorship and naïve cost assumptions**, bringing the Modern Magic Formula up to institutional standards and making any remaining alpha far more credible.

