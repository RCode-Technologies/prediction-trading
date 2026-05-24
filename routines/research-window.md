---
name: research-window
cron: "0 12 * * *"
cron_tz: UTC
local_time: "07:00 America/New_York"
also_covers: "Europe end-of-morning briefing; Asia/Pacific overnight news already crystallised"
phase: research_window
expected_frequency: 1/day
---

# Research Window — 12:00 UTC / 07:00 ET

US wake-up. Pull together overnight signals from EU/AS markets that closed
or moved, build today's watchlist before US news cycle accelerates. This is
the **heaviest research routine** — most of the day's source budget is
spent here.

## Skills invoked (in order)

1. `skills/boot` — sync, validate, lock, halts check.
2. `skills/circuit-breaker.evaluate()` — **checkpoint 1**: after boot.
   If halted, skip to step 6 (send daily summary if due, persist, exit).
3. `skills/research` — angle: "what shifted overnight (EU close, Asia
   resolutions, weekend polling, late sports)?". Budget: up to 3 sources
   (external API keys → agent native WebSearch/WebFetch → Polymarket only).
4. `skills/markets` — build/refresh watchlist with fresh prices. May
   consume 1 Gamma source from the same 3-source bucket.
5. `skills/journal` — emit `research_note`, `candidate_rank`,
   `phase_completed` events.
6. `skills/persist` — commit + push memory branch. **The cycle is only
   successful when push lands.**

## Output artifacts

- `research/YYYY-MM-DD/<slug>.md` — main note.
- `research/YYYY-MM-DD/watchlist.md` — top 5 candidates with fresh marks.
- Trade-log events: `cycle_start`, `research_note`, `candidate_rank`,
  `phase_completed`, `cycle_end`.

## Trade behavior

- **Paper observation:** forecast-only (sizing emits `forecast` events; no
  paper fills during observation window).
- **Paper post-observation:** sizing + paper fills allowed if a candidate
  passes the strategy's minimum edge floor.
- **Mainnet:** trades **not** prioritised here — most US news drops after
  09:30 ET (`trade-window`). Only execute if a candidate has a strong,
  time-sensitive edge that may close before 18:00 UTC.

## Conventional commit suggestion

`feat(research): window <YYYY-MM-DD> [cycle <cycle_id>]`

## Failure modes

- All preflights fail → `preflight_failed` event, exit.
- All providers error → continue on Polymarket public data only.
- No candidates pass min-edge → no decisions, still write a research note
  and watchlist (may be empty); emit `phase_completed`.

## Cross-phase contract

- `phase_completed` event with `phase: "research_window"` is what
  downstream routines (`trade-window`, `daily-close`, `overnight-watch`)
  use to detect a missed run.
