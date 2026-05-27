---
name: overnight-watch
cron: "0 4 * * *"
cron_tz: UTC
local_time: "23:00 ET (prev day)"
phase: overnight_watch
expected_frequency: 1/day
---

# Overnight Watch — 04:00 UTC / 23:00 ET

Asia active, US asleep. Light monitor: marks, NAV, breaker. Opportunistic mainnet only if a watchlist candidate moved ≥200 bps in our favor AND `liquidityNum >= 10000`. **Floor: ≥1 `nav_snapshot`.**

## Steps

1. `boot`
2. `circuit-breaker.evaluate()` — cp1. Halted → jump to 10.
3. **No-position fast path.** `portfolio.positions == []` and `observation_only==true` → skip CLOB marks + opportunistic. Run cp2 with cash-only NAV; halted → jump to 10. Else send one-line `notify routine_summary`, jump to step 9 (recalibrate still runs).
4. `markets` — refresh CLOB midpoints on open positions only.
5. `risk.nav()` + `journal.nav_snapshot`.
6. `circuit-breaker.evaluate()` — cp2 (post-marks). Halted → jump to 10.
7. **Opportunistic gate** (all required): watchlist ≤24h fresh, candidate moved ≥200 bps favorable, `liquidityNum >= 10000`, mode allows. Yes → `sizing` → `trade` for that one candidate.
8. `circuit-breaker.evaluate()` — cp3, only if step 7 fired.
9. **`recalibrate.sweep()`** — refresh scorecard + calibration; resolve any forecasts past `close_time` (≤1 Gamma source).
10. `journal.phase_completed`.
11. `persist`.

## Source budget

0 research. N CLOB book calls (1/open position + ≤1/opportunistic). CLOB ≠ research.

## Failure modes

- Watchlist >24h stale → emit `phase_missed` for `research_window`; no new positions.
- Mainnet opportunistic preflight fail → `preflight_failed`; cycle continues (NAV + breaker still happen).

## Notify

Only: `routine_summary` (no-position/no-trade), `circuit_breaker`, mainnet `trade_placed`, `preflight_failed`, `persist_conflict`. No daily summary (daily-close owns it).

## Commit

Per `skills/commit` § Routine-mapped subjects (`overnight-watch` rows).
