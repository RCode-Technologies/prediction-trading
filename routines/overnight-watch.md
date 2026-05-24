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
2. `circuit-breaker.evaluate()` — cp1 (post-boot). Halted → jump to 8.
3. `markets` — refresh CLOB midpoints on **open positions only** (no discovery, no source burn).
4. `risk.nav()` + `journal.nav_snapshot`.
5. `circuit-breaker.evaluate()` — cp2 (post-marks). Asian-time crashes most often fire here. Halted → jump to 8.
6. Opportunistic gate (all required): watchlist ≤24h fresh, candidate midpoint moved ≥200 bps in our favor, `liquidityNum >= 10000`, mode allows (paper post-obs, or mainnet preflight passes). If yes: `sizing` → `trade` for that single candidate.
7. `circuit-breaker.evaluate()` — cp3, only if step 6 fired.
8. `journal.phase_completed`.
9. `persist`.

## Source budget

0 research sources. N CLOB book calls (1/open position + ≤1/opportunistic eval). CLOB ≠ research.

## Failure modes

- Watchlist >24h stale → emit `phase_missed` for `research_window`; no new positions.
- Mainnet opportunistic preflight fail → `preflight_failed`; cycle continues (NAV + breaker still happen).

## Notify

Only: `circuit_breaker`, mainnet `trade_placed`, `preflight_failed`, `persist_conflict`. **No daily summary here** (daily-close owns it).

## Commit

- No trade: `chore(cycle): overnight_watch [cycle <cid>]`
- Trade fired: `feat(trade): overnight opportunistic <slug> [cycle <cid>]`
