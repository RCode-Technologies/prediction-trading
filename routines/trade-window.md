---
name: trade-window
cron: "0 18 * * *"
cron_tz: UTC
local_time: "13:00 ET"
phase: trade_window
expected_frequency: 1/day
---

# Trade Window — 18:00 UTC / 13:00 ET

Peak US activity. Morning watchlist is mature; midday news priced in. **Primary decisions + execution** (paper + mainnet).

## Steps

1. `boot`
2. `circuit-breaker.evaluate()` — cp1. Halted → jump to 10.
3. **Phase-miss check.** Grep trade-log for today's `phase_completed` with `phase:"research_window"`. Missing → degraded research (budget 1 source) + emit `phase_missed`.
4. `markets` — refresh watchlist prices (CLOB; not research sources). Drop stale.
5. `circuit-breaker.evaluate()` — cp2 (post-marks).
6. `sizing` per candidate that passes min-edge. ≤1 mainnet order/cycle. Paper has no cap but practical ≤3.
7. `trade` — paper or mainnet branch. Pre-submit push for mainnet. Internal failures (mainnet cancel fail, post-submit push fail) → `trade` calls `circuit-breaker.halt(reason)` directly.
8. `circuit-breaker.evaluate()` — cp3 (post-fill, portfolio updated).
9. `notify` — `discovery_summary` when no mainnet `trade_placed` notification already explains the action. If no candidate passed checks, say so simply. If candidates passed, summarize up to 3 with the review checklist from `skills/notify`.
10. `journal.phase_completed`.
11. `persist`.

## Source budget

3 max (any research + Gamma in this cycle). Typical 0-1.

## Failure modes

- Watchlist missing AND degraded research empty → `phase_completed decisions:0`, exit clean.
- Mainnet preflight fail → `preflight_failed`, no order, continue.
- Push failure → `persist_conflict`; halt + notify.

## Notify

- Paper: per-trade suppressed; daily summary covers them.
- Mainnet: `trade_placed` per fill.
- Paper + mainnet: `discovery_summary` for no-trade/no-fill outcomes or passed-check candidates that need human review.

## Commit

- Paper: `feat(trade): paper_fill <slug> [cycle <cid>]`
- Mainnet: `feat(trade): mainnet_fill <slug> [cycle <cid>]`
- No trade: `chore(cycle): trade_window no-op [cycle <cid>]`

Use one routine commit with a concise body covering candidates considered, pass/fail count, fills, and notification status. Mainnet pre-submit safety commits remain the only exception.
