---
name: research-window
cron: "0 12 * * *"
cron_tz: UTC
local_time: "07:00 ET"
phase: research_window
expected_frequency: 1/day
---

# Research Window — 12:00 UTC / 07:00 ET

US wake-up. Pull overnight signals (EU close, Asia resolutions, weekend polling). Build today's watchlist. **Heaviest research routine** — most of the day's source budget spent here.

## Steps

1. **Set reasoning effort to MAX** — this is the day's most consequential routine; the watchlist built here drives every downstream trade-window decision. Use the highest thinking effort available (extra-high / max). Do not start any other step until this is set.
2. `boot`
3. `circuit-breaker.evaluate()` — cp1. Halted → skip to 8 (persist, exit).
4. `research` — angle: "what shifted overnight (EU close / Asia resolutions / weekend polling / late sports)?". Budget ≤3 sources (external keys → native WebSearch/WebFetch → Polymarket only).
5. `markets` — build/refresh watchlist with fresh prices. May consume 1 Gamma source from the shared 3-source bucket.
6. `journal` — `research_note`, `candidate_rank`, `phase_completed`.
7. `notify` — `discovery_summary`. If no candidate passes the checks, send one concise sentence saying no bettable candidates passed and name only the most relevant leads. If candidates pass, summarize up to 3 and include the review checklist from `skills/notify`.
8. `persist`.

## Notify

Send `discovery_summary` in paper and mainnet. The summary is for human grasp, not execution authorization: concise when nothing passes, specific and review-oriented when something does.

## Output artifacts

- `research/YYYY-MM-DD/<slug>.md`
- `research/YYYY-MM-DD/watchlist.md` (top 5 with fresh marks)

## Trade behavior

- Paper observation: forecast-only.
- Paper post-observation: sizing + paper fills if candidate passes edge floor.
- Mainnet: not prioritized here (US news drops after 09:30 ET = `trade-window`). Execute only if strong, time-sensitive edge closes before 18:00 UTC.

## Failure modes

- All preflights fail → `preflight_failed`, exit.
- All providers error → continue on Polymarket only.
- No candidates pass min-edge → empty watchlist, `phase_completed` still emitted.

## Commit

`feat(research): window <YYYY-MM-DD> [cycle <cid>]`

Use a short commit body for watchlist count, candidates passing checks, sources used, and notification status. Do not create a follow-up bookkeeping commit.
