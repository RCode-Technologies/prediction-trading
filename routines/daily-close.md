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

Crystallize day's signals. Recap, reflect, daily Telegram. Sundays: also weekly. **Floor: ≥1 `recap`, ≥1 `reflection`.**

## Steps

1. `boot`
2. `circuit-breaker.evaluate()` — cp1. Halted → daily summary if due, jump to 11.
3. **Phase-miss check.** Today's `phase_completed` for `research_window` + `trade_window`. Emit `phase_missed` per gap.
4. `markets` — final fresh-price snapshot on open positions (CLOB).
5. `circuit-breaker.evaluate()` — cp2 (post-marks).
6. `risk.nav()` + `journal.nav_snapshot`.
7. `circuit-breaker.evaluate()` — cp3 (post-snapshot). Halted → surface in recap.
7b. **`recalibrate.sweep()`** — final daily sweep. Resolves open forecasts past `close_time`. Writes `state/scorecard.json` + `state/calibration.json`.
7c. **Sunday only** (`date '+%u' == 7`): load `skills/groom` and run it — rotate append-only logs out of the hot path + lint the brain for token bloat / drift. Returns `findings[]` for step 8. Non-Sunday: skip (groom is weekly; see `skills/groom` § Why weekly).
8. `recap` — write `recaps/YYYY-MM-DD.md` (reads `state/scorecard.json`). Sunday: also `recaps/YYYY-Www.md`, listing groom `findings[]` under *Recommendations for human review*.
9. `reflect` — once/UTC date. Reads scorecard. May edit `strategy/current.md` + snapshot.
10. `notify daily_summary`. Sunday: also `weekly_recap`. Then grep trade-log for this UTC date's `reflection` event: if `edited==true` OR `reason=="regression_blocked"` → also `notify strategy_evolution` as a separate message (template handles variants). All three are date-deduped by `notify` step 2, so safe under re-runs.
11. `journal.phase_completed`.
12. `persist`.

## Source budget

0 research. CLOB freshness only + ≤1 Gamma for `recalibrate.sweep` resolution lookup. Sunday groom adds 0 sources (local file work only).

## Position-close policy

- Near-resolution (`close_time < now + 12h`) flagged in recap.
- No auto-SELL in v2.
- Halt active + mainnet position with `close_time < now + 12h` → recap highlights residual exposure.

## Failure modes

- Recap dedupe hit → skip recap; still notify if not sent.
- Reflect sees no data → `reflection edited:false`.
- Notify fails → `notification` failed-kind event; cycle continues.

## Commit

Per `skills/commit` § Routine-mapped subjects (`daily-close` rows). If reflection edited strategy, keep both artifacts in the same commit, prefer `feat(strategy)` subject. Body: recap paths, reflection result, notifications, open positions. Sunday groom archival rides this same commit — note archived counts + any lint findings in the body.
