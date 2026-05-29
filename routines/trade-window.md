---
name: trade-window
cron: "0 18 * * *"
cron_tz: UTC
local_time: "13:00 ET"
phase: trade_window
expected_frequency: 1/day
---

# Trade Window — 18:00 UTC / 13:00 ET

Peak US activity. Primary decisions + execution (paper + mainnet). **Target (v3): a broad forecast-only batch (~4–6; combined daily ~8–12 with research-window); only § Edge-gate passers (expected 0–2/day) become bets.** Emitting **zero** forecasts → `null_cycle`. (AGENTS.md "Action commitment" mirror still shows the v2 rigid `≥3 forecast` floor — orchestrator syncs it in Phase 6.)

## Steps

1. `boot`
2. `circuit-breaker.evaluate()` — cp1. Halted → jump to 13.
3. **Phase-miss check.** Today's `phase_completed phase:"research_window"` missing → degraded research (budget 1) + emit `phase_missed`.
4. `markets` — refresh watchlist (CLOB). Drop stale. `state/universe.jsonl` missing/>24h → run `markets.universe()` first (1 Gamma source from budget).
5. `circuit-breaker.evaluate()` — cp2 (post-marks).
6. **Build broad forecast-only batch (~4–6):** *(research-window step 8 reuses this algorithm)*
   - Sort watchlist by `edge_bps desc, liquidity_num desc`; take the top ~4–6.
   - Default `learning_intent:"explore"` (forecast, no capital) for **all** entries. A candidate is *attempted* as exploit only if it carries a thesis with `resolution_parsed:true` + non-null `reference_class` + ≥2 `source_providers` AND `edge_bps >= 300`; the binding exploit-vs-explore decision is the `sizing` § Edge gate (`edge_net`, not `edge_bps`).
   - Tag every forecast with `edge_source`. Never duplicate a market within the cycle (`explore_dedupe_key` enforced in `sizing`). If watchlist < target, run `markets.universe()` (1 source).
7. `sizing` per slate entry — emits a `forecast` for every entry; the **edge gate** decides exploit-vs-explore and assigns `sizing_tier:0`. ≤1 mainnet order/cycle.
8. `trade` for **gate-passing** exploit decisions with `shares > 0`. Forecast-only entries have `shares == 0` and skip `trade`. Mainnet: pre-submit push. Internal failures → `trade` calls `circuit-breaker.halt()`.
9. `circuit-breaker.evaluate()` — cp3 (post-fill).
10. **Self-audit.** Count cycle's `forecast` events. `0` → append `null_cycle reason:"forecast_floor_missed", forecasts_emitted:N, slate_built:[...]` and continue (no halt; cycle still commits).
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
- Mainnet preflight fail → `preflight_failed`. Forecast-only entries still emit (paper-only).
- 0 forecasts → `null_cycle reason:"forecast_floor_missed"`.

## Notify

Paper: per-trade suppressed (daily summary covers). Mainnet: `trade_placed` per fill. Both: `discovery_summary` for no-fill outcomes; `null_cycle` suppression-exempt.

## Commit

Per `skills/commit` § Routine-mapped subjects. Body: slate composition, fills, notifications. One commit per cycle; mainnet pre-submit is the only exception.
