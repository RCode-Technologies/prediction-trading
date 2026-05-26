---
name: trade-window
cron: "0 18 * * *"
cron_tz: UTC
local_time: "13:00 ET"
phase: trade_window
expected_frequency: 1/day
---

# Trade Window — 18:00 UTC / 13:00 ET

Peak US activity. Morning watchlist is mature; midday news priced in. **Primary decisions + execution** (paper + mainnet). **Action commitment: this routine must emit ≥3 `forecast` events. Cycles that fail this floor are `null_cycle` failures.**

## Steps

1. `boot`
2. `circuit-breaker.evaluate()` — cp1. Halted → jump to 13.
3. **Phase-miss check.** Grep trade-log for today's `phase_completed` with `phase:"research_window"`. Missing → degraded research (budget 1 source) + emit `phase_missed`.
4. `markets` — refresh watchlist prices (CLOB; not research sources). Drop stale. If `state/universe.jsonl` is missing or >24h old, run `markets.universe()` first (uses 1 Gamma source from this cycle's budget).
5. `circuit-breaker.evaluate()` — cp2 (post-marks).
6. **Build forecast slate (≥3 mandatory).** Compose the cycle's forecast slate before invoking `sizing`:
   - Sort watchlist by `edge_bps` desc, then `liquidity_num` desc.
   - **Exploit slot fill:** every candidate with `edge_bps >= 300` and a usable thesis is tagged `learning_intent:"exploit"`. Cap at 3 for paper.
   - **Explore slot fill:** if exploit count < 3, take the next watchlist candidates (no thesis required, any liquid two-sided market) and tag `learning_intent:"explore"` with `explore_rank ∈ {1,2,3}` assigned in the order they fill the remaining slots. Targets exactly 3 total. If watchlist has < 3 candidates, run `markets.universe()` (costs 1 source) and pull from there.
   - Hard rule: never duplicate a market within a cycle. Never probe a market that already has an exploit forecast this cycle. Never re-probe a market that already has a `learning_intent:"explore"` `forecast` for today (`explore_dedupe_key` check happens in `sizing`).
7. `sizing` per slate entry, in slate order. ≤1 mainnet order/cycle. Paper has no fill cap but practical ≤3.
8. `trade` — paper or mainnet branch for each exploit decision with `shares > 0`. Exploration forecasts have `shares == 0` and skip `trade` entirely. Pre-submit push for mainnet. Internal failures (mainnet cancel fail, post-submit push fail) → `trade` calls `circuit-breaker.halt(reason)` directly.
9. `circuit-breaker.evaluate()` — cp3 (post-fill, portfolio updated).
10. **Self-audit.** Count `forecast` events appended this cycle (by `cycle_id`). If `forecasts < 3`, append:
    ```json
    {"event_type":"null_cycle","reason":"forecast_floor_missed","forecasts_emitted":N,"expected_minimum":3,"slate_built":[...]}
    ```
    and continue to notify + persist (do not halt — the cycle still commits so the failure is visible, but humans must investigate).
11. `notify`:
    - If any exploit `paper_fill` or mainnet `trade_placed` fired → daily-summary path already covers it.
    - Else send `discovery_summary` (1-3 candidate highlights + slate composition: `N_exploit + N_explore`).
    - If `null_cycle` was emitted → also send `null_cycle` alert.
12. `journal.phase_completed` with `forecasts:<N>`, `exploit_decisions:<N>`, `paper_fills:<N>`, `slate_composition: {exploit: <n>, explore: <n>}`.
13. `persist`.

## Source budget

3 max (any research + Gamma in this cycle). Typical 1 — usually consumed by `markets.universe()` refresh if the universe is stale.

## Failure modes

- Watchlist missing AND universe missing → `markets.universe()` is forced, costs 1 source. If THAT fails (Gamma down), emit `null_cycle reason:"no_market_data"`, exit clean.
- Mainnet preflight fail → `preflight_failed`, no order, continue. Exploration probes still emit (paper-only, no SDK needed).
- Push failure → `persist_conflict`; halt + notify.
- Fewer than 3 forecasts despite all of the above → `null_cycle reason:"forecast_floor_missed"` (loud, but cycle persists so the gap is auditable).

## Notify

- Paper: per-trade suppressed; daily summary covers them.
- Mainnet: `trade_placed` per fill.
- Paper + mainnet: `discovery_summary` for no-trade/no-fill outcomes or passed-check candidates that need human review.
- New: `null_cycle` alert sent in **paper AND mainnet** any time the forecast floor is missed.

## Commit

Subject per `skills/commit/SKILL.md` § Routine-mapped subjects (`trade-window` rows). Body: slate composition, fills, notifications. One routine commit; mainnet pre-submit safety commits are the only exception.
