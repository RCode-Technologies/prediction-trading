---
cycle_id: 20260613T180246Z-85099811
phase: trade_window
ts: 2026-06-13T18:05:00Z
universe_size: 39
universe_cached_at: 2026-06-13T12:10:00Z
slate_composition: {exploit_gate_passers: 0, explore: 6}
---

# Candidates — 2026-06-13 trade window (18:00 UTC)

Broad forecast-only batch (6 candidates) re-priced against fresh CLOB books at ~18:02Z.
Same six markets as the morning research-window slate — re-forecast to track intraday CLV
(does the market drift toward our `your_p`?). **0 clear the binding § Edge gate** (each thesis
carries 1 source `brave`, no parsed Gamma `description`, no named reference class), so all
emit as `explore` forecasts — calibration/CLV probes, no capital. No fills this cycle (expected).

## Ranked slate (BUY side, YES token) — fresh 18:02Z books

| rank | market_id | market | your_p | market_p (mid) | edge_net | best_bid/ask | liq | edge_source | intent |
|---:|---|---|---:|---:|---:|---|---:|---|---|
| 1 | 2506608 | ETH > $1,700 (Jun 18) | 0.44 | 0.395 | +0.030 | 0.38/0.41 | 16256 | structural | explore |
| 2 | 631145 | DeepSeek best AI model (Jun 30) | 0.02 | 0.001 | +0.019 | —/0.001 (one-sided) | 326542 | base_rate | explore |
| 3 | 2492010 | BTC in $70k–$72k (Jun 17) | 0.025 | 0.0145 | +0.006 | 0.01/0.019 | 11443 | structural | explore |
| 4 | 2462645 | ETH > $1,800 (Jun 14) | 0.02 | 0.0125 | +0.006 | 0.011/0.014 | 19132 | structural | explore |
| 5 | 2506684 | BTC > $56,000 (Jun 18) | 0.965 | 0.985 | -0.023 | 0.982/0.988 | 22113 | structural | explore |
| 6 | 2364238 | Anthropic best Coding AI model (Jun 30) | 0.88 | 0.967 | -0.099 | 0.955/0.979 | 6193 | base_rate | explore |

## Intraday CLV read vs morning (12:10Z) books
- **ETH > $1,800 (Jun 14)** drifted UP: ask 0.008 → 0.014, mid 0.006 → 0.0125 — market moved
  toward our `your_p`=0.02 (positive CLV signal on a sub-1d-to-close card). Still well below 0.02.
- **DeepSeek best AI** book went one-sided (bids pulled; ask 0.001 only) — forecast flagged
  `stale:true`, snapped at last-good midpoint 0.001.
- BTC>$56k, BTC band, ETH>$1,700, Anthropic-coding ≈ flat vs morning.

## Notes
- ETH cards retain the morning's ~8-day staleness caveat (Jun-5 spot data; no fresh second
  provider this cycle — 0 research sources spent, theses still intraday-valid).
- No exploit fills (expected under v3 — gate needs ≥2 providers + parsed resolution + reference class).
