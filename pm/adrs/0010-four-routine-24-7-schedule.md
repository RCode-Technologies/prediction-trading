# 0010 — Four phase routines, 24/7 with US weighting (supersedes 0009)

- **Status:** Accepted
- **Date:** 2026-05-24
- **Supersedes:** 0009 (single hourly cloud routine)
- **Related:** PRD v1-instruction-pack, ADR 0011 (skills/routines split)

## Context

ADR 0009 specified a single hourly Claude Code cloud routine. Two problems
showed up before any runtime work:

1. **Token waste.** An hourly routine that only does *real* work in 4 of 24
   wake-ups burns ~5× more boot tokens than necessary. Cloud routines bill on
   usage; idle wake-ups have a real cost.
2. **Polymarket is 24/7 and globally distributed, but US news/liquidity
   dominates.** A "stock-market trading day" framing (pre-market / open /
   midday / close) is misleading; a "phases of the agent's day with US bias"
   framing is more accurate.

## Decision

v1.1 schedules **four** dedicated Claude Code cloud routines, each pointed at
a single routine file in `routines/`. Crons are UTC. Each routine file
declares its cron in YAML frontmatter at the top so the file is
self-documenting.

| UTC | ET | Routine | Purpose |
|---|---|---|---|
| 04:00 | 23:00 (prev) | `overnight-watch` | Asia/Pacific monitor, NAV + breaker, opportunistic only |
| 12:00 | 07:00 | `research-window` | US wake-up; heaviest research, build watchlist |
| 18:00 | 13:00 | `trade-window` | Peak US activity; decisions + execution |
| 22:00 | 17:00 | `daily-close` | US close; recap + reflection + daily summary (Sun: weekly) |

A fifth routine, `circuit-breaker`, is **reactive** (not scheduled). It
documents the halt protocol enforced by `skills/risk`, invoked from other
routines on breach.

The memory-branch contract from ADR 0009 is preserved unchanged:

- Default branch is the durable memory branch.
- **Allow unrestricted branch pushes** must be enabled.
- Every cycle pulls/rebases on start, validates state, acquires the repo
  lock, does work, releases the lock, commits with a Conventional Commits
  message, pull-rebases once more, pushes. Never force-pushes.
- Mainnet pre-submit decision push (with `idempotency_key`) protects
  against duplicate orders on retry.

### Phase-miss detection

Each routine grep-checks the trade-log for the prior phase's
`phase_completed` event at the start of its work. Missing event triggers a
`phase_missed` event; `skills/recap` includes these in the daily summary.
This makes silent missed routines visible to the human within ≤24h.

## Consequences

- ~5–6× lower baseline token usage than ADR 0009's hourly polling.
- Schedule changes require updating both the YAML frontmatter in the routine
  file (documentation) **and** the corresponding Claude cloud routine cron
  (operational source of truth).
- Four cloud routines to keep configured; if the human forgets one, the
  daily Telegram summary flags it within a day via `phase_missed`.
- US-biased timing (3 of 4 routines during US active hours) matches
  Polymarket's user base and news cadence.
- Asia/Pacific markets and overnight breakouts are covered by
  `overnight-watch`, which can opportunistically trade if a watchlist
  candidate moves materially.
- The five-routine model maps 1:1 to ADR 0011's skills/routines split:
  routines are thin orchestrators; the bulk of logic moved to skills.
