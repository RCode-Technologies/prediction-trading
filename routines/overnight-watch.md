---
name: overnight-watch
cron: "0 4 * * *"
cron_tz: UTC
local_time: "23:00 ET (prev day)"
phase: overnight_watch
expected_frequency: 1/day
---

# Overnight Watch — 04:00 UTC / 23:00 ET

Asia active, US asleep. Light monitor: marks, NAV, breaker, **exit + governor checks**. Opportunistic mainnet only if a watchlist candidate moved ≥200 bps in our favor AND `liquidityNum >= 10000`. **Floor: ≥1 `nav_snapshot`.**

## Steps

1. `boot`
2. `circuit-breaker.evaluate()` — cp1 (v3: 24h halt **+ drawdown-from-peak governors + heat breach**). Halted/freeze → jump to 10; probation/heat-breach is non-halting (carried into sizing).
3. **No-position fast path.** `portfolio.positions == []` and `observation_only==true` → skip CLOB marks + opportunistic + exit check. Run cp2 with cash-only NAV; halted → jump to 10. Else send one-line `notify routine_summary`, jump to step 9 (recalibrate still runs).
4. `markets` — refresh CLOB midpoints on open positions only.
5. `risk.nav()` + `journal.nav_snapshot`.
6. `circuit-breaker.evaluate()` — cp2 (post-marks; governors + heat re-checked on fresh NAV). Halted → jump to 10.
6b. **Disconfirmation-stop exit check (v3; `config/guardrails.md` § Disconfirmation stop).** For each open position: `risk.pnl_from_entry(position)` and scan its `disconfirming_signals[]` against fresh news/marks. `pnl_pct <= -0.25` (non-stale mark) **or** a named disconfirming event materialised → load `skills/sizing` with `learning_intent:"risk_reduction"` + the position + `stop_reason` → SELL via `skills/trade` (reducing/closing `paper_fill` at `best_bid`). Exits are exempt from any active freeze/probation. No trip → continue (no decision).
7. **Opportunistic gate** (all required): watchlist ≤24h fresh, candidate moved ≥200 bps favorable, `liquidityNum >= 10000`, mode allows, **not frozen / not heat-breached** (governor from cp2). Yes → `sizing` (assigns `sizing_tier` from the ladder; an unproven bucket caps ≤ Tier 1) → `trade` for that one candidate.
8. `circuit-breaker.evaluate()` — cp3, only if step 6b or step 7 fired (post-fill).
9. **`recalibrate.sweep()`** — runs `snap_clv()` first (CLV snapshot of due open forecasts at +6h/+24h/close, ≤8 CLOB calls) + open-ledger self-check, then refreshes scorecard + calibration and resolves any forecasts past `close_time` (≤1 Gamma source).
10. `journal.phase_completed`.
11. `persist`.

## Source budget

0 research. N CLOB book calls (1/open position + ≤1/opportunistic + ≤1/risk_reduction SELL re-check + ≤8 for `snap_clv()` CLV snapshots). CLOB ≠ research.

## Failure modes

- Watchlist >24h stale → emit `phase_missed` for `research_window`; no new positions.
- Mainnet opportunistic preflight fail → `preflight_failed`; cycle continues (NAV + breaker still happen).

## Notify

Only: `routine_summary` (no-position/no-trade, **or a v3 `risk_reduction` exit fired — note the stop + realized P&L**), `circuit_breaker` (incl. v3 `drawdown_freeze_15pct`), mainnet `trade_placed`, `preflight_failed`, `persist_conflict`. No daily summary (daily-close owns it).

## Commit

Per `skills/commit` § Routine-mapped subjects (`overnight-watch` rows).
