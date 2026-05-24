# 0012 — Daily and weekly recaps as derived markdown files

- **Status:** Accepted
- **Date:** 2026-05-24
- **Related:** PRD v1-instruction-pack, ADR 0008, ADR 0010

## Context

ADR 0008 established Telegram daily-summary delivery (paper + mainnet) and
suppressed per-trade alerts in paper mode. Telegram messages are ephemeral
from the agent's perspective — the trade log carries individual events but
no aggregated artifact lives in the repo.

A user request asked whether weekly recaps would be persisted. We also
wanted human-readable rollups that are easy to share, diff, and link to
from PR descriptions, without having to re-grep the JSONL each time.

## Decision

`skills/recap` writes derived markdown files into a new `recaps/` directory:

- `recaps/YYYY-MM-DD.md` — written by `routines/daily-close` every UTC day.
- `recaps/YYYY-Www.md` — written by `routines/daily-close` only on Sundays
  (ISO week ending). Uses ISO week numbering (`date '+%G-W%V'`).

Both files derive entirely from `state/trade-log.jsonl` + `state/portfolio.json`
+ `state/cycle-index.json`. They never mutate state; the trade-log gets one
`recap` event per file written (with the path) for dedupe.

Recap files contain:

- Daily: summary, per-phase activity (was each routine completed?),
  forecasts/fills, P&L, open positions, reflection hints.
- Weekly: performance, trade quality (hit rate, Brier), strategy evolution,
  risk events, recommendations for human review.

The daily Telegram summary and weekly Telegram recap (`notify` skill) embed
a short version; the markdown file is the full record.

## Consequences

- Repo carries human-readable history alongside the machine-readable log.
- Weekly recap cadence falls out naturally from the daily-close routine —
  no extra cron, no extra cloud routine.
- ISO week numbering avoids ambiguity around US-week-vs-EU-week starts.
- Recap files are append-only at the directory level (never overwrite an
  existing dated file) — dedupe via the `recap` event in the trade-log.
- Recap files are also where `phase_missed` flags surface to humans, since
  the Telegram summary may not always reach the operator.
