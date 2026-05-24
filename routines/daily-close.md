---
name: daily-close
cron: "0 22 * * *"
cron_tz: UTC
local_time: "17:00 ET"
phase: daily_close
expected_frequency: 1/day
runs_weekly_recap_on: Sunday (date '+%u' == 7)
---

# Daily Close — 22:00 UTC / 17:00 ET

US close. Crystallize day's signals. Reflect, recap, daily Telegram. Sundays: also weekly recap.

## Steps

1. `boot`
2. `circuit-breaker.evaluate()` — cp1. Halted → daily summary if due, jump to 11.
3. **Phase-miss check.** Confirm today's `phase_completed` for `research_window` + `trade_window`. Emit `phase_missed` per gap.
4. `markets` — final fresh-price snapshot on open positions (CLOB, not research). Flag stale.
5. `circuit-breaker.evaluate()` — cp2 (post-marks). Asia-time crashes often surface here.
6. `risk.nav()` + `journal.nav_snapshot`.
7. `circuit-breaker.evaluate()` — cp3 (post-snapshot). Halted → surface in recap.
8. `recap` — write `recaps/YYYY-MM-DD.md` (with learning + smartness scorecards used by reflection). **Sunday:** also `recaps/YYYY-Www.md`.
9. `reflect` — once/UTC date. Convert scorecards into strategy update if new evidence. May edit `strategy/current.md` and snapshot to `strategy/history/`.
10. `notify` — `daily_summary`. Sunday: also `weekly_recap`.
11. `journal.phase_completed`.
12. `persist`.

## Source budget

0 research sources. CLOB freshness only.

## Position-close policy

- Near-resolution (`close_time < now + 12h`) → flagged in recap.
- v1 does **not** auto-SELL. Human/strategy decision, surfaced in recap.
- Exception: halt active + mainnet position with `close_time < now + 12h` → recap explicitly highlights residual exposure.

## Failure modes

- Recap dedupe hit → skip recap; still send notify if not sent.
- Reflect sees no data → `reflection edited:false`.
- Notify fails → `notification` failed-kind event; cycle continues.

## Commit

- `feat(recap): daily <YYYY-MM-DD> [cycle <cid>]`
- Sun: `feat(recap): daily + weekly <YYYY-Www> [cycle <cid>]`
- If strategy edited, keep recap + strategy artifacts in the same routine commit and prefer: `feat(strategy): reflect to v<N+1> [cycle <cid>]`

Use one routine commit with a concise body covering recap paths, reflection result, notifications, and whether positions remain open.
