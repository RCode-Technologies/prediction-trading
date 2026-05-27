---
name: trade-window
cron: "0 18 * * *"
cron_tz: UTC
local_time: "13:00 ET"
phase: trade_window
expected_frequency: 1/day
---

# Trade Window — 18:00 UTC / 13:00 ET

Peak US activity. Primary decisions + execution (paper + mainnet). **Floor: ≥3 `forecast` events. Miss → `null_cycle`.**

## Steps

1. `boot`
2. `circuit-breaker.evaluate()` — cp1. Halted → jump to 13.
3. **Phase-miss check.** Today's `phase_completed phase:"research_window"` missing → degraded research (budget 1) + emit `phase_missed`.
4. `markets` — refresh watchlist (CLOB). Drop stale. `state/universe.jsonl` missing/>24h → run `markets.universe()` first (1 Gamma source from budget).
5. `circuit-breaker.evaluate()` — cp2 (post-marks).
6. **Build forecast slate (≥3 mandatory):**
   - Sort watchlist by `edge_bps desc, liquidity_num desc`.
   - Exploit slots: each candidate with `edge_bps >= 300` and thesis → `learning_intent:"exploit"`. Cap 3.
   - Explore slots: remaining slots fill with next watchlist candidates (no thesis needed) → `learning_intent:"explore"`, `explore_rank ∈ {1,2,3}`. Total exactly 3. If watchlist < 3, run `markets.universe()` (1 source).
   - Never duplicate a market within a cycle. Never probe a market already covered by an exploit forecast or an existing same-day explore (`explore_dedupe_key` enforced in `sizing`).
7. `sizing` per slate entry. ≤1 mainnet order/cycle. Paper practical ≤3.
8. `trade` for exploit decisions with `shares > 0`. Explore probes have `shares == 0` and skip `trade`. Mainnet: pre-submit push. Internal failures → `trade` calls `circuit-breaker.halt()`.
9. `circuit-breaker.evaluate()` — cp3 (post-fill).
10. **Self-audit.** Count cycle's `forecast` events. `< 3` → append `null_cycle reason:"forecast_floor_missed", forecasts_emitted:N, slate_built:[...]` and continue (no halt; cycle still commits).
11. `notify`:
    - Exploit `paper_fill` / mainnet `trade_placed` → daily summary covers.
    - Else `discovery_summary` (1-3 highlights + `N_exploit + N_explore`).
    - `null_cycle` emitted → also send `null_cycle` alert.
12. `journal.phase_completed forecasts:<N>, exploit_decisions:<N>, paper_fills:<N>, slate_composition:{exploit, explore}`.
13. `persist`.

## Source budget

3 max. Typical 1 (universe refresh if stale).

## Failure modes

- Watchlist AND universe missing → force `markets.universe()` (1 source). Fail → `null_cycle reason:"no_market_data"`.
- Mainnet preflight fail → `preflight_failed`. Explore probes still emit (paper-only).
- < 3 forecasts → `null_cycle reason:"forecast_floor_missed"`.

## Notify

Paper: per-trade suppressed (daily summary covers). Mainnet: `trade_placed` per fill. Both: `discovery_summary` for no-fill outcomes; `null_cycle` suppression-exempt.

## Commit

Per `skills/commit` § Routine-mapped subjects. Body: slate composition, fills, notifications. One commit per cycle; mainnet pre-submit is the only exception.
