---
name: overnight-watch
cron: "0 4 * * *"
cron_tz: UTC
local_time: "23:00 America/New_York (prev day)"
also_covers: "Asia/Pacific active hours; EU pre-open; US asleep — light monitor only"
phase: overnight_watch
expected_frequency: 1/day
---

# Overnight Watch — 04:00 UTC / 23:00 ET

US asleep; Asia/Pacific is active. Light-touch monitoring cycle: fresh
marks on open positions, NAV snapshot, circuit-breaker check, opportunistic
mainnet trades **only** if an Asia-driven candidate already on the
watchlist crosses a strong-edge threshold while books are thin.

## Skills invoked (in order)

1. `skills/boot` — sync, validate, lock, halts check.
2. `skills/circuit-breaker.evaluate()` — **checkpoint 1**: after boot.
   If halted, jump to step 8.
3. `skills/markets` — refresh CLOB midpoints on **open positions only**
   (no candidate discovery; no research-budget burn).
4. `skills/risk.nav()` + write `nav_snapshot` event via `skills/journal`.
5. `skills/circuit-breaker.evaluate()` — **checkpoint 2**: after mark
   refresh + nav_snapshot. **Asian-time crashes are most likely to fire
   here** — this is the routine where the breaker most often does work.
   If halted, jump to step 8.
6. **Opportunistic trade gate.** Only if:
   - watchlist from `research-window` is fresh (≤24h),
   - a watchlist candidate's midpoint moved ≥200 bps in the agent's favor
     since the watchlist was written,
   - the candidate is liquid enough (`liquidityNum >= 10000`, stricter
     than daytime threshold), AND
   - mode allows it (paper post-observation or mainnet preflight passes),
   then invoke `skills/sizing` → `skills/trade` for that single candidate.
   Skip otherwise.
7. `skills/circuit-breaker.evaluate()` — **checkpoint 3**: only if a
   trade fired in step 6.
8. `skills/journal` — emit `phase_completed`.
9. `skills/persist` — commit + push. **Cycle is only successful when push
   lands.**

## Output artifacts

- Trade-log: `cycle_start`, `nav_snapshot`, optional
  `forecast`+`decision`+`paper_fill|mainnet_*`, `phase_completed`,
  `cycle_end`.
- Updated `state/portfolio.json` (mark prices) even if no trade.

## Source budget

0 research sources. Up to N CLOB book calls (one per open position +
optionally one per watchlist candidate evaluated for opportunistic trade).
CLOB calls are not research sources.

## Conventional commit suggestion

- No trade: `chore(cycle): overnight_watch [cycle <cycle_id>]`
- Trade fired:
  `feat(trade): overnight opportunistic <market_slug> [cycle <cycle_id>]`

## Failure modes

- Watchlist stale (>24h, meaning `research-window` was missed):
  emit `phase_missed` for `research_window`, do not open new positions.
- Mainnet preflight fail on opportunistic trade → `preflight_failed`,
  continue cycle (NAV snapshot + breaker still happen).
- Asian liquidity crash triggers breaker → halt + notify; treated like any
  other circuit-breaker event.

## Notify policy

- No daily summary here (that's `daily-close`'s job).
- Notify only for `circuit_breaker`, mainnet `trade_placed`,
  `preflight_failed`, `persist_conflict`.
