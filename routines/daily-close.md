---
name: daily-close
cron: "0 22 * * *"
cron_tz: UTC
local_time: "17:00 America/New_York"
also_covers: "Asia/Pacific opening (~22-24 UTC); EU sleep; daily reflection cadence"
phase: daily_close
expected_frequency: 1/day
runs_weekly_recap_on: Sunday (date '+%u' == 7)
---

# Daily Close — 22:00 UTC / 17:00 ET

US market close. Day's signals are crystallised; reflect on the day's
forecasts vs realized prices, generate recap, send daily Telegram summary.
On Sundays also generate the weekly recap.

## Skills invoked (in order)

1. `skills/boot` — sync, validate, lock, halts check.
2. **Phase-miss check.** Confirm `phase_completed` events exist today for
   `research_window` and `trade_window`. Emit `phase_missed` per gap;
   `recap` skill includes these.
3. `skills/markets` — final fresh-price snapshot on open positions (CLOB
   calls; not research sources). Stale marks flagged.
4. `skills/risk` — write `nav_snapshot`, evaluate 24h circuit breaker.
5. `skills/recap` — write `recaps/YYYY-MM-DD.md` (daily).
   - **If Sunday:** also write `recaps/YYYY-Www.md` (weekly).
6. `skills/reflect` — once per UTC date; may edit `strategy/current.md`
   and snapshot to `strategy/history/`.
7. `skills/notify` — send `daily_summary`. If Sunday, also send
   `weekly_recap`.
8. `skills/journal` — emit `phase_completed`.
9. `skills/persist` — commit + push memory branch.

## Output artifacts

- `recaps/YYYY-MM-DD.md` (always).
- `recaps/YYYY-Www.md` (Sundays only).
- `strategy/current.md` updated + `strategy/history/YYYY-MM-DD-vN.md` if
  reflection edits.
- Trade-log: `cycle_start`, `nav_snapshot`, `recap` (×1–2),
  `reflection`, `notification` (×1–2), `phase_completed`, `cycle_end`.

## Source budget

0 external research sources. This routine derives from the trade-log only
plus CLOB freshness calls.

## Position-close policy

- Near-resolution positions (`close_time < now + 12h`) are flagged in the
  daily recap.
- v1 does **not** auto-SELL to close. Closure is a human/strategy decision
  surfaced in the recap.
- Exception: if a halt is active AND a mainnet position is open with
  `close_time < now + 12h`, the recap explicitly highlights the residual
  exposure for human review.

## Conventional commit suggestion

- `feat(recap): daily <YYYY-MM-DD> [cycle <cycle_id>]`
- Sundays: `feat(recap): daily + weekly <YYYY-Www> [cycle <cycle_id>]`
- If strategy edited:
  `feat(strategy): reflect → v<N+1> (snapshot v<old_N>) [cycle <cycle_id>]`

## Failure modes

- Recap dedupe hit (already wrote today) → skip recap, still send notify if
  daily summary not yet sent.
- Reflection sees no data → write `reflection` event with `edited: false`.
- Notify fails → `notification` failed-kind event; cycle continues.
