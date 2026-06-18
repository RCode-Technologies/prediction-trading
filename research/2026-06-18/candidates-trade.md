---
cycle_id: 20260618T180642Z-8e3d29c3
phase: trade_window
ts: 2026-06-18T18:06:42Z
universe_size: 50
universe_cached_at: 2026-06-18T12:09:16Z
slate_composition: "5 forecasts — 0 exploit (gate-passing), 5 explore. Fresh batch (research-window covered the top-6 edge markets earlier today)."
---

# Candidates — 2026-06-18 (trade window)

Universe still fresh from 12:09Z (50 liquid markets). Research-window already forecast the six
highest-edge markets this morning; per the per-UTC-date dedupe, this batch picks the next liquid,
two-sided markets. All forecast-only: none carries a parsed Gamma resolution + ≥2 independent sources,
and none clears the net-edge floor — expected on-design for early v3 (forecast-many / bet-few).
Alibaba "best AI model" (631142) was dropped: one-sided book (no bids) at snapshot.

## Slate (ranked by liquidity; fresh CLOB books @ ~18:05Z)

| # | market_id | question | side | your_p | mid | best_ask | edge_net | edge_source | intent | note |
|---|---|---|---|---:|---:|---:|---:|---|---|---|
| 1 | 1897154 | Tunisia vs. Japan ends in a draw | YES | 0.25 | 0.235 | 0.24 | +0.010 | base_rate | explore | WC group-stage draw base rate ~25-30%; mild lean up |
| 2 | 2326439 | Belgium vs. Iran: over 3.5 goals | YES | 0.28 | 0.295 | 0.30 | -0.020 | structural | explore | Iran historically low-block/low-scoring; lean under |
| 3 | 2571231 | HSBC Champ: Hijikata def. Lehecka | YES | 0.35 | 0.3745 | 0.379 | -0.029 | base_rate | explore | Lehecka materially higher-ranked; market fair-ish |
| 4 | 839432 | Ecuador win World Cup Group E | YES | 0.04 | 0.0375 | 0.039 | +0.001 | base_rate | explore | thin tail; defer to liquid market |
| 5 | 2553323 | Collin Morikawa win 2026 U.S. Open | YES | 0.015 | 0.0155 | 0.02 | -0.005 | base_rate | explore | one of large field; honest ≈ market |

## Composition

- **0 exploit** (gate-passing) / **5 explore**.
- Edge sources: base_rate ×4, structural ×1.
- 0 researched theses (judgment-anchored explore batch); no candidate clears resolution_parsed + ≥2 sources + net-edge floor.
