---
name: trade-window
cron: "0 18 * * *"
cron_tz: UTC
local_time: "13:00 America/New_York"
also_covers: "Post-Europe-close volatility; peak US news cycle in progress"
phase: trade_window
expected_frequency: 1/day
---

# Trade Window — 18:00 UTC / 13:00 ET

Peak US activity. Watchlist from the morning research routine is now mature;
fresh midday news is priced into the orderbook. **Primary decision +
execution window**, both paper and mainnet.

## Skills invoked (in order)

1. `skills/boot` — sync, validate, lock, halts check.
2. **Phase-miss check.** Grep trade-log for a `phase_completed` event today
   with `phase:"research_window"`. If missing:
   - Run a degraded research pass (budget 1 source) to build a minimum
     watchlist.
   - Emit `phase_missed` event for `research_window` (recap will surface it).
3. `skills/markets` — refresh watchlist prices (CLOB book calls; not
   research sources). Drop any candidate whose midpoint went stale.
4. `skills/sizing` — for each candidate that still passes min-edge:
   forecast + decision. Up to **one mainnet order per cycle** (paper has
   no such cap but practical limit ≤3 paper fills).
5. `skills/trade` — paper or mainnet branch. Pre-submit push for mainnet.
6. `skills/risk` — circuit breaker check after fills (in case new
   positions tipped the 24h P&L).
7. `skills/journal` — emit `phase_completed`.
8. `skills/persist` — commit + push.

## Output artifacts

- Updated `state/portfolio.json`.
- Trade-log: `cycle_start`, `forecast`(×N), `decision`(×N), `paper_fill`
  or `mainnet_order_submitted`+`mainnet_fill`, `nav_snapshot`,
  `phase_completed`, `cycle_end`.
- `state/halts.json` if breaker fires.

## Source budget

3 max (shared between any research pass + Gamma calls in this cycle).
Typical: 0–1 because we lean on the morning's watchlist.

## Conventional commit suggestion

- Paper fill: `feat(trade): paper_fill <market_slug> [cycle <cycle_id>]`
- Mainnet fill: `feat(trade): mainnet_fill <market_slug> [cycle <cycle_id>]`
- No trade: `chore(cycle): trade_window no-op [cycle <cycle_id>]`

## Failure modes

- Watchlist missing AND degraded research returns nothing → emit
  `phase_completed` with `decisions:0`, exit clean.
- Mainnet preflight fail → `preflight_failed`, no order, continue cycle.
- Push failure → `persist_conflict`; halt + notify.

## Notify policy

- Paper: per-trade alerts suppressed (ADR 0008). Daily summary covers them.
- Mainnet: `trade_placed` for every fill.
