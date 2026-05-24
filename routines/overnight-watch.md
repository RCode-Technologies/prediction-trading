---
name: overnight-watch
cron: "0 4 * * *"
cron_tz: UTC
local_time: "23:00 ET (prev day)"
phase: overnight_watch
expected_frequency: 1/day
---

# Overnight Watch — 04:00 UTC / 23:00 ET

Asia active, US asleep. Light monitor: marks, NAV, breaker. Opportunistic mainnet only if a watchlist candidate's midpoint moved ≥200 bps in our favor since the watchlist was written AND book is liquid (`liquidityNum >= 10000`).

## Steps

1. `boot`
2. `circuit-breaker.evaluate()` — cp1 (post-boot). Halted → jump to 9.
3. **No-position fast path.** If `state/portfolio.json.positions == []` and `mode.observation_only==true`, skip CLOB marks and opportunistic evaluation. Run `circuit-breaker.evaluate()` cp2 using cash-only NAV; if halted, jump to 9. Otherwise send one-line `notify routine_summary` saying no open positions and no trades opened, then jump to 9.
4. `markets` — refresh CLOB midpoints on **open positions only** (no discovery, no source burn).
5. `risk.nav()` + `journal.nav_snapshot`.
6. `circuit-breaker.evaluate()` — cp2 (post-marks). Asian-time crashes most often fire here. Halted → jump to 9.
7. Opportunistic gate (all required): watchlist ≤24h fresh, candidate midpoint moved ≥200 bps in our favor, `liquidityNum >= 10000`, mode allows (paper post-obs, or mainnet preflight passes). If yes: `sizing` → `trade` for that single candidate. If no trade opens and there are no open positions, send the same concise `routine_summary`.
8. `circuit-breaker.evaluate()` — cp3, only if step 7 fired.
9. `journal.phase_completed`.
10. `persist`.

## Source budget

0 research sources. N CLOB book calls (1/open position + ≤1/opportunistic eval). CLOB ≠ research.

## Failure modes

- Watchlist >24h stale → emit `phase_missed` for `research_window`; no new positions.
- Mainnet opportunistic preflight fail → `preflight_failed`; cycle continues (NAV + breaker still happen).

## Notify

Only: one-line `routine_summary` for no-position/no-trade runs, `circuit_breaker`, mainnet `trade_placed`, `preflight_failed`, `persist_conflict`. **No daily summary here** (daily-close owns it).

## Commit

- No trade: `chore(cycle): overnight_watch [cycle <cid>]`
- Trade fired: `feat(trade): overnight opportunistic <slug> [cycle <cid>]`
