---
cycle_id: 20260526T120425Z-50bc2068
phase: research_window
ts: 2026-05-26T12:11:00Z
source_ts: 2026-05-26T12:08:50Z
research_overlap: none
strategy_version: v1
min_edge_bps: 300
candidates_passing_min_edge: 0
---

# Watchlist — 2026-05-26 (research window)

Source budget exhausted (3/3: brave + tavily + 1 Gamma `/markets`). The strongest research signals from this cycle (NBA East sweep, NBA West Game-4 swing) do **not** intersect the top-100-by-volume Gamma slice inside the 30d filter — those NBA markets either fell out of the top-100 or have already resolved server-side. No re-query permitted under the 3-source cap.

Top 5 below are the most liquid Gamma markets that satisfy `endDate <= 2026-06-25`, `liquidityNum >= 5000`, both sides quoted, fresh book ≤15 min. None of them has a named thesis from `research/2026-05-26/overnight-shifts.md`, and none beats the 300 bps edge floor in `strategy/current.md`. Listed for downstream phases to monitor in case overnight reporting on a *non-NBA* market updates `your_p`.

| rank | market_id | condition_id | event_slug | question | end | mid | bid/ask | liq_num | your_p | market_p | edge_bps | thesis | feature_tags | source_ts |
|---:|---|---|---|---|---|---:|---|---:|---:|---:|---:|---|---|---|
| 1 | 1439549 | 0xb4022c0b2718eca7ad27195f2d48f06527fa000269d188e1d3001ff8bbc16956 | fed-rate-cut-by-629 | Fed rate cut by September 2026 meeting? | 2026-06-17 | 0.1405 | 0.140/0.141 | 17599 | 0.140 | 0.1405 | 5 | none (no Fed thesis this cycle) | macro,base-rate-anchored-research | 2026-05-26T12:08:50Z |
| 2 | 2347246 | 0x71743db40a1925a9e3c22deb80e90b72290e6f66cad2b8058f78682a693182c8 | solana-up-or-down-on-may-26-2026 | Solana Up or Down on May 26? | 2026-05-26 | 0.100 | 0.08/0.12 | 17276 | 0.10 | 0.100 | 0 | none | crypto,thin-book-drift | 2026-05-26T12:09:19Z |
| 3 | 2316234 | 0xb28bbb46015aec3ec6784b4bcd9e4b500ba1dffbc9efd57e0052f3c0e109485b | ucl-psg-ars-2026-05-30-exact-score | Exact Score: PSG 3 - 1 Arsenal? (UCL final) | 2026-05-30 | 0.065 | 0.06/0.07 | 27207 | 0.065 | 0.065 | 0 | none (no UCL thesis) | sports,base_rate | 2026-05-26T12:09:17Z |
| 4 | 2039649 | 0xe9e8784dd743d09e69a69f87debda6d97b175fd3ccfce7238f68274e30196986 | colombia-election-1st-round-margin-of-victory | Espriella wins 2026 Colombia 1st round | 2026-05-31 | 0.330 | 0.31/0.35 | 14256 | 0.33 | 0.330 | 0 | none (no Colombia thesis) | politics,polling | 2026-05-26T12:08:29Z |
| 5 | 1897038 | 0xb3e5963c18d0fbe9285a35e65aa260b304a3cded6aaddab9507122caa33caf44 | fifwc-kr-cze-2026-06-11 | Korea Republic vs. Czechia draw | 2026-06-12 | 0.305 | 0.30/0.31 | 11431 | 0.305 | 0.305 | 0 | none | sports,base_rate | 2026-05-26T12:03:20Z |

## Notes for downstream phases

- **Research-thesis gap.** Strong informational signal this cycle is concentrated in NBA postseason (East champion → NYK resolved; West series 2-2). Neither produced a candidate inside the top-100 / 30d / liquidity filter. Trade-window may re-issue a targeted Gamma query (e.g. `/events?slug=nba-finals-2026` or NBA-tagged `/markets`) — that costs 1 source from the trade-window's 3-source budget.
- **Iran-deal proxy (Hormuz traffic returns to normal by end of June, id 1971905, mid 0.445, liq $206k)** is at `endDate 2026-06-30`, just outside the 30d window. If trade-window relaxes filter to 35d or re-runs at 18:00 UTC (window then becomes ≤2026-06-25 — still excluded), thesis says: AP "emerging deal" language alone should not move near-term resolution >5 bps. Direction would be flat/down if market already spiked on the article.
- **Per-cycle (post-observation v1):** observation flag flipped this cycle (`mode.json.observation_only=false`). Sizing + paper fills now permitted, but watchlist below produces 0 candidates over the 300 bps edge floor → trade-window may still issue forecasts, not fills, unless its own re-query surfaces an edge-bearing market.
- **No promotion based on post-thesis drift alone** — none of the top-5 has informational claim; drift evidence accumulates for reflect, not trade.
