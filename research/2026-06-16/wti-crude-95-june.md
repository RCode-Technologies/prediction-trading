---
cycle_id: 20260616T121112Z-a744c807
phase: research_window
ts: 2026-06-16T12:22:00Z
angle: Probability WTI active-month prints a High >= $95 during June 2026
sources:
  - {provider: tavily, url: "https://api.tavily.com/search?q=WTI+crude+oil+price+today+June+2026", fetched_at: 2026-06-16T12:16:00Z}
---

# WTI Crude hit (HIGH) $95 in June? — base-rate read

**Question / resolution (parsed).** Market `2492328` resolves **YES** if, during any June-2026
trading session, a 1-minute candle for the **active-month** WTI futures prints a High **≥ $95**
(Pyth prices, no rounding). Pre-creation price action is ignored; no trade → NO.

**Current level.** As of 2026-06-16 the WTI front month (Jul-26) sits around **$78.5–$81**
(Markets Insider front-month settle $80.75 on 06-15; Barchart/Oilprice Jul-26 ~$78.5–$80.9; EIA
Cushing spot series current). The most recent session was **down ~2.8–4.7%**, i.e. momentum is
*lower*, not higher.

**What YES requires.** A move from ~$80 to **$95 is ≈ +18%** intramonth, with only ~2 weeks of June
sessions left. Absent a major supply shock that is a large, fast spike.

**Evidence for (tail risk).** Geopolitics are unusually live in 2026 (U.S. action in Venezuela /
Maduro capture earlier in the year, broader instability) — a genuine supply-shock tail exists, which
is why the market is not at zero.

**Evidence against.** No active shock in the flow; price drifting down; ~18% in two weeks is far
outside typical intramonth ranges.

**Reference class.** WTI active-month posting a **≥18% intramonth High move within a ~2-week window
absent a fresh supply shock** — low single digits (~5%).

**Estimate.** your_p(YES) ≈ **0.045**. Market midpoint ≈ 0.065 (bid 0.06 / ask 0.07). Slightly rich
vs the base rate but the YES net edge is below floor and the residual is a genuine geopolitical tail —
**forecast-only (explore)**.

## Thesis cards
| thesis_id | claim | market_ids | prior_p | expected_direction | feature_tags | edge_source | reference_class | resolution_parsed | disconfirming_signals |
|---|---|---|---:|---|---|---|---|---|---|
| 20260616-wti-95-june-T1 | WTI does not print >=$95 in June; YES slightly rich vs base rate | 2492328 | 0.05 | YES down | commodity,base_rate | base_rate | WTI active-month >=18% intramonth High move in ~2wk absent supply shock | true | Venezuela/MidEast supply shock; OPEC+ surprise cut; oil breaks >$88 with momentum |
