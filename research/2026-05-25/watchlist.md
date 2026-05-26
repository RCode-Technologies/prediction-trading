---
cycle_id: 20260525T180603Z-6c1a6cfb
phase: trade_window
ts: 2026-05-25T18:09:00Z
source_ts: 2026-05-25T18:08:04Z
derived_from: research/2026-05-24/watchlist.md
refresh_type: CLOB-marks-only (no Gamma rerun this routine)
sources_used_this_routine: 0
budget_remaining_after: 1
degraded: true
degraded_reason: research_window phase_missed today; budget 1
mode: paper (observation_only=true; window ends 2026-05-26T00:00Z)
---

# Watchlist refresh — 2026-05-25 trade window

Carries 2026-05-24 candidates with refreshed CLOB books. **CLOB book reads are safety re-checks, not research sources** (per `skills/markets` step 5). No Gamma rerun this routine — the carried single-source budget is preserved unused.

## Refreshed top (was 5 → now 4)

| rank | market_id | question | side | best_bid | best_ask | midpoint | book_ts | your_p | market_p | edge_bps | stale | thesis_id | feature_tags | note |
|---:|---|---|---|---:|---:|---:|---|---:|---:|---:|---|---|---|---|
| 1 | 566136 | PSG win 2025–26 Champions League | BUY YES | 0.57 | 0.58 | 0.575 | 2026-05-25T18:08:04Z | 0.575 | 0.575 | 0 | false | null | sports_final, deep_book | unchanged from 5/24 |
| 2 | 1012319 | Royal Challengers Bengaluru win 2026 IPL | BUY YES | 0.37 | 0.38 | 0.375 | 2026-05-25T18:07:39Z | 0.375 | 0.375 | 0 | false | null | sports_final, cricket | unchanged |
| 3 | 1439549 | Fed rate cut by September 2026 meeting | BUY YES | 0.121 | 0.143 | 0.132 | 2026-05-25T18:06:12Z | 0.132 | 0.132 | 0 | false | null | macro, fed_path, base_rate, wide_spread_2pp | midpoint 0.151→0.132 (−1.9pp); spread 2.2pp; tiny size |
| 4 | 1492419 | Richard Tabor = NJ Republican Senate nominee | BUY YES | 0.43 | 0.44 | 0.435 | 2026-05-25T18:08:02Z | 0.435 | 0.435 | 0 | false | null | midterm_primary, political | unchanged |

`your_p = market_p` again — no thesis from yesterday's research materially shifts any of these and no new research was loaded this routine. All four rows are 0 bps vs the 300 bps min-edge floor → **0 candidates pass min-edge**. Fed midpoint drift is logged as drift evidence (for reflection), not as an edge signal — per `strategy/current.md` "Don't promote on post-thesis market drift alone".

## Dropped

- **Valorant: Leviatán vs G2 Map 2 (2343383)** — CLOB returns `No orderbook exists for the requested token id`. Market closed (close_time was 2026-05-25T01:00Z). Resolved/removed. Drop.

## Source-budget note

Degraded research budget this routine = 1 (per `routines/trade-window.md` phase-miss rule). Spent 0 — no Gamma rerun, no Brave/WebFetch. The 1-source budget for chasing yesterday's open theses (Gabbard / Tulsi / DNI / Venezuela election / Iran nuclear deal) was **not** spent because:

- Observation window ends in ~6h (2026-05-26T00:00Z); any new candidate found now still only generates a `forecast` not a fill, so the marginal value of burning the single budgeted source pre-cutover is low.
- Yesterday's untapped theses can be re-attempted by the next research_window with the full 3-source budget.

## Carry forward

- **Daily-close**: log that trade_window today was a no-op due to (a) research_window phase_missed → degraded budget, and (b) 0/4 refreshed candidates beat min-edge. Reflection should note Fed market drift (0.151→0.132) as a potential drift-skill data point if a `your_p < 0.132` forecast had been on record (none was — flat market_p).
- **Next research_window (12:00 UTC tomorrow)**: run the targeted Gabbard/DNI/Venezuela/Iran Gamma queries; full 3-source budget should be available.
