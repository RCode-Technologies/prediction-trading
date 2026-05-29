# 0024 — Weekly `groom` for token-economy hygiene + log rotation

- **Status:** Accepted
- **Date:** 2026-05-29
- **Related:** part of the **v3 epoch** — PRD [v3-edge-and-learning](../prds/v3-edge-and-learning.md)
  §"Folded into v3" + [plan](../plans/v3-edge-and-learning.md) Phase 8. Sibling: ADR 0023
  (self-direction). Touches the append-only contract in ADR 0012/`skills/journal` and the
  scheduled-invocation budget (v3's proposed ADR 0022). Implemented in commit
  `b103af1` (`feat(skill): add weekly groom for token-economy clean + lint`).

## Context

"The repo is the brain," and the metered cost is the **scheduled invocation** plus the **auto-loaded
context** every cycle pays. Two kinds of rot accumulate against that:

1. **Append-only growth.** `state/trade-log.jsonl` grows ~35 lines/day and `forecasts.resolved.jsonl`
   grows with every resolution. Boot tails a bounded window, but the file itself is read/scanned by
   several skills, and an ever-growing hot-path log is pure drag.
2. **Drift + dead references.** As skills/routines/docs change across many cycles (and many parallel
   agents), the auto-loaded set bloats, cross-references go stale, INDEX files orphan, and schedule
   tables diverge between `AGENTS.md` and `README.md`.

Nothing owned that maintenance. The append-only rule (no skill rewrites `trade-log.jsonl`) is correct
for integrity but left no sanctioned way to *rotate* the log. And a per-cycle hygiene pass would be
self-defeating: spending a paid invocation (and its tokens) every cycle to fight ~35 log lines/day
costs more than the bloat it removes.

## Decision

Add **`skills/groom`**, a **weekly (Sunday only)** self-maintenance skill invoked from `daily-close`.

1. **Sole log rotator (a documented exception to append-only).** `groom` is the *only* skill permitted
   to rewrite `state/trade-log.jsonl` and `state/forecasts.resolved.jsonl`, moving aged lines into
   `state/archive/*.jsonl` (30-day / 90-day retention). The cutoff is
   `min(now − 30d, oldest open-forecast emitted_at)` so a line tied to an unresolved forecast is
   **never** archived — `recalibrate`'s trade-log recovery path stays intact. Rotation is **atomic**
   (tmp+mv), **no-drop** (`archived + kept == original`), and **idempotent** (skips if a `groom` event
   already exists for the UTC date). All other skills remain strictly append-only; `skills/journal`
   documents this single exception.
2. **Token-economy lint (report-only on core).** `groom` checks the auto-loaded set against
   line-count/byte budgets and verifies referential integrity (skill/link existence, research INDEX
   orphans, schema version, stale lock, schedule-table drift). It is **report-only** on core cognition
   files (`AGENTS.md`, `config/*`, `strategy/current.md`, `skills/*`, `routines/*`) — findings surface
   for a human / `reflect` / `envision`, never auto-edited. It may auto-act only on derived/terminal
   artifacts (rebuild generated `INDEX.md`; `git mv` terminal-status proposal RFCs to an archive — never
   `rm`).
3. **Weekly cadence, zero added invocations.** `groom` rides the existing Sunday `daily-close` — no new
   cron. Findings fold into `recaps/YYYY-Www.md` under *Recommendations for human review*; a `groom`
   journal event (governance — no recalibrate hook) records findings + actions every run.

## Consequences

- **The hot-path logs stop growing unbounded** without violating append-only integrity for any other
  skill, and without ever orphaning an open forecast from its trade-log history.
- **`state/archive/` joins the repo layout** as cold storage off the per-cycle read path.
- **Drift and dead references get caught weekly** and surfaced to the human in the weekly recap, rather
  than silently degrading the brain's navigability.
- **One sanctioned exception to "append-only" now exists** — narrowly scoped to `groom` and to
  rotation-with-archive (never deletion). This is the rule that most needs guarding; it is therefore a
  candidate for the self-direction **denylist** (`skills/groom/` is denylisted from autonomous
  enactment in `config/autonomy.md`) so the agent can never self-modify its own log rotator.
- **Weekly, not daily, is deliberate.** It trades fresher hygiene for honoring the real cost model (the
  invocation/token budget). Six days a week, `groom` costs nothing.
