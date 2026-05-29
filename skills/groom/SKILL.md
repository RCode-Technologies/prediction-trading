---
name: groom
description: Weekly self-maintenance — rotate append-only logs out of the hot path and lint the brain so per-cycle token cost stays bounded and the repo stays AI-navigable. Loaded on demand by daily-close on Sundays.
inputs: none (reads state/, config/, routines/, skills/, strategy/, research/)
outputs: state/archive/*.jsonl, leaner state/trade-log.jsonl, groom event, lint findings (folded into weekly recap)
---

# Groom

Keeps the brain **lean and AI-first** without touching the hot path. Every line of an auto-loaded
file (`AGENTS.md`, `config/mode.json`, the six `state/*.json`, `strategy/current.md`,
`trade-log.jsonl` tail) is paid **every cycle** — groom rotates growth out of those files and flags
drift before it costs tokens.

## Why weekly, not daily

Token economy is the whole point: running groom every cycle would add load + checks + an event
7×/week to fight accretion that is slow (~35 trade-log lines/day). A 30-day retention window plus
weekly rotation keeps the live log well under budget, and the tail-load (50 lines) is unaffected at
any size. So groom rides `daily-close` **only on Sundays** (`date '+%u' == 7`), reusing that
routine's boot/lock/persist and folding findings into the weekly recap. Zero cost the other 6 days.

## Scope (HARD)

- **Owns + may rewrite:** `state/trade-log.jsonl`, `state/forecasts.resolved.jsonl`, `state/archive/*`.
  Sole rewriter of the trade-log (journal is append-only; rotation is the documented exception,
  mirroring how `recalibrate.sweep` compacts `forecasts.open.jsonl`).
- **Report-only, NEVER edits:** `AGENTS.md`, `config/`, `strategy/current.md` (reflect-owned),
  `config/guardrails.md` (human-owned), routines, skills, `recaps/`, `research/`. Groom surfaces
  findings; humans/`reflect` act on them. Uncertain → report, don't touch. (Mirrors guardrail
  philosophy: uncertain = reject.)
- Deterministic + idempotent. Atomic writes only (`.tmp` + `mv`). Never drops a line: archived +
  kept == original count, asserted.

## Steps

1. **Dedupe.** Grep trade-log for `event_type=="groom"` with today's UTC `date` → if present, exit
   (idempotent under re-runs).

2. **Rotate trade-log** (the main token win). Skip entirely if `wc -l < 500` AND oldest line
   `ts >= now-30d` — nothing to gain, no churn.
   - **Cutoff = min( now − 30d , oldest_open_emitted_at )** where `oldest_open_emitted_at` =
     min `emitted_at` over `resolved:false` rows in `state/forecasts.open.jsonl`. The 30d bound
     covers every routine lookback (recap 7d, reflect/recalibrate 30d, last-3-reflections); the
     open-forecast bound guarantees recovery stays possible (`recalibrate` reconstructs open
     forecasts from the trade-log — never archive a line tied to an unresolved forecast).
   - Keep lines with `ts >= cutoff`; archive lines with `ts < cutoff`.
   - Append each archived line to `state/archive/trade-log-<YYYY-MM>.jsonl` (month of that line's
     `ts`), preserving order. `mkdir -p state/archive` first.
   - Write kept lines to `state/trade-log.jsonl.tmp`, validate `jq -c . tmp`, then `mv` into place.
   - **Assert** `archived + kept == original`; mismatch → abort rotation, leave live file untouched,
     record finding `trade_log_rotation_aborted`.

3. **Rotate resolved forecasts.** Skip if `state/forecasts.resolved.jsonl` `< 200` lines. Else move
   rows with `resolution_ts < now-90d` to `state/archive/forecasts-resolved-<YYYY>.jsonl` (90d ≫ the
   30d scorecard window). Atomic rewrite of the remainder. Same no-drop assertion.

4. **Lint — report only.** Build a `findings[]` list of strings (empty = clean):
   - **Budget guard** (line count is the token proxy). Flag any over soft cap:
     `AGENTS.md`≤130 · `strategy/current.md`≤220 · `config/mode.json`≤40 ·
     `state/cycle-index.json`≤250 (catches `nav_snapshots` bloat — it loads every cycle) ·
     `state/scorecard.json`≤80 · `state/calibration.json`≤80 · `state/portfolio.json`≤120 ·
     `state/{halts,lock}.json`≤30 · live `state/trade-log.jsonl`≤1200.
   - **Validity** (deeper than boot's tail check): `jq empty config/*.json state/*.json`;
     `jq -c . state/*.jsonl state/archive/*.jsonl >/dev/null`.
   - **Schema:** every `state/*.json` and the first line of every `state/*.jsonl` has
     `schema_version`.
   - **Referential integrity (AI-first navigability)** — deterministic, no prose parsing:
     - Every `skills/*/` dir contains a `SKILL.md` (no empty/half-built skill).
     - Every explicit `skills/<name>` path or `[...](path)` link in `routines/*.md`, `AGENTS.md`,
       and `skills/*/SKILL.md` resolves to an existing file.
     - Every `research/INDEX.md` slug → `research/<date>/<slug>.md` exists; every
       `research/*/*.md` (excluding `INDEX.md`, `watchlist.md`) appears in `INDEX.md` (orphans).
   - **Lock sanity:** flag if `state/lock.json` is `active:true` with `expires_at < now` (stale).
   - **Strategy lineage:** `strategy/current.md` `version: vN` but no `strategy/history/*-v<N-1>.*`
     snapshot → flag (light check).

5. **Emit `groom` event** via `journal` (one line):
   ```json
   {"event_type":"groom","cadence":"weekly","cutoff":"<iso>","trade_log_archived":<n>,"trade_log_live_lines":<n>,"resolved_archived":<n>,"lint_findings":[...],"budgets_over":[...]}
   ```

6. **Surface findings.** Return `findings[]` to the caller (`daily-close`) so the **weekly recap**
   lists them under *Recommendations for human review* and the `weekly_recap` notification carries
   them. No new notify kind — groom never adds always-paid surface for itself.

## Source budget

0 sources. Pure local file work (`jq`, `wc`, `grep`, `git mv`-free atomic rewrites). No CLOB, no
research, no Gamma.

## Failure modes

- Rotation assertion fails → leave live files untouched, record `*_aborted` finding, continue.
  Never lose an event; git history is the backstop.
- `forecasts.open.jsonl` missing/corrupt → cannot compute the open-forecast bound → fall back to a
  conservative `now-90d` cutoff (keeps more), record finding. Never archive into the unknown.
- `jq` parse error on any file → record finding, skip that file's rotation, continue lint.
- Re-run same day → step 1 dedupe exits. Rotation is independently idempotent (nothing past cutoff).
