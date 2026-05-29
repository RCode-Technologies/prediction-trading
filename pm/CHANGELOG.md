# Changelog

All notable changes to this project are tracked here. Newest entries on top.
Versioning is loose semver-ish: `v0.x` until first mainnet trade, then `v1.0`.

## [Unreleased] — the v3 epoch

**v3** is the current epoch — *Edge, Honest Accounting, Fast Learning*, now also **Self-Direction**
and **Repo Hygiene**. Self-direction (`envision`/`enact`) and `groom` shipped 2026-05-29 (paper-mode)
as the first implemented slices of v3; the edge/accounting/learning package below is still design-only.
There is no separate `v0.4` — those changes are folded into v3.

### Implemented — Self-direction (envision / enact), 2026-05-29

The supervisor no longer has to ask for a version bump. **`skills/envision`** (daily, agent-owned)
reflects on the whole system and authors capability proposals into `proposals/`; on Sundays
**`skills/enact`** (≤1/week, protected core) self-implements one low-risk, reversible, paper-only,
denylist-clean proposal as a single revertible commit, then arms auto-rollback. Bounded by a
human-owned constitution (`config/autonomy.md`) the agent cannot amend, enforced by three gates keyed
to commit identity: `boot` integrity audit, `persist` write gate, `circuit-breaker`
`protected_core_violation`. New journal events `vision` / `proposal` / `enactment` (`enactment` notify
is suppression-exempt). Nothing touching guardrails / capital / breaker / mainnet may ever self-enact;
the human vetoes by `git revert` / `LEDGER.md` status (standing ≥7-day window). See PRD
§"Folded into v3", [plan](plans/v3-edge-and-learning.md) Phase 7,
[ADR 0023](adrs/0023-bounded-agent-self-direction.md).

### Implemented — Repo hygiene (groom), 2026-05-29

**`skills/groom`** (weekly, Sundays) keeps the brain lean and AI-navigable: the **sole** rotator of
`state/trade-log.jsonl` + `state/forecasts.resolved.jsonl` into `state/archive/` (30d / 90d; the cutoff
never strands a line tied to an open forecast — atomic, no-drop, idempotent), plus a token-budget +
referential-integrity lint of the auto-loaded set. Report-only on core cognition files; findings ride
the weekly recap. **Weekly by design** — the per-cycle invocation is the metered cost. Adds the `groom`
journal event + `state/archive/` to the repo layout. [plan](plans/v3-edge-and-learning.md) Phase 8,
[ADR 0024](adrs/0024-weekly-groom.md).

### Proposed (design only — not implemented) — Edge, Honest Accounting, Fast Learning

- **v3 design package — Edge, Honest Accounting, and Fast Learning.** Drafted
  2026-05-29 after the US x Iran trade (`2354045`) showed a ~-34% position
  loss driven by process defects (no defensible edge, bet placed without
  parsing resolution criteria, midpoint-priced paper fills, no disconfirmation
  exit) on top of a learning loop stuck at `resolved_n=0` and a capital model
  that had been rewritten by 185× position scaling.
  - [PRD](prds/v3-edge-and-learning.md) — what & why, goals mapped to
    faster/better/precise/profitable, an opinionated risk philosophy
    (conviction-tiered sizing ladder + equity governors), acceptance criteria,
    ownership map, and the resolved supervisor decisions.
  - [Plan](plans/v3-edge-and-learning.md) — seven phases (capital integrity +
    Iran exit → cost-honest accounting → edge gate + forecast/trade split →
    CLV fast-learning on repurposed pulse cycles → historical bootstrap →
    risk doctrine → cost-model rebalance).
  - **Scheduled-invocation budget baked in:** the metered cost is the *cycle*,
    not the line of context. Stays at ~10 invocations/day (≤15 ceiling) by
    repurposing the 6 dead heartbeats into useful CLV/exit "pulse" cycles —
    no new routines.
  - **Supervisor decisions folded in (2026-05-29):** exit the Iran position now
    and take the loss; approve the offline backtest; replace the per-cycle
    forecast floor with a daily routine-aware target; replace the flat 5% cap +
    24h breaker with the tiered ladder + governors; keep market selection
    category-neutral with `edge_source` tagging.
  - Proposes ADRs 0017–0022 (listed in the PRD; to be spun out on approval):
    cost-honest fills (amends 0003), edge gate, CLV + bootstrap, risk doctrine
    (tiered sizing + governors + exits, amends "no auto-SELL"), cost-model
    reprioritization (amends `AGENTS.md`), scheduled-invocation budget.
  - **Status:** awaiting supervisor review. No runtime files (`skills/`,
    `routines/`, `strategy/`, `state/`, `config/`, `AGENTS.md`) changed yet.

## [v0.3.0] — 2026-05-24

### Changed

- **Circuit-breaker is now a skill, not a routine** (ADR 0014, amends ADR
  0010). Deleted `routines/circuit-breaker.md`; added
  `skills/circuit-breaker/SKILL.md` with `evaluate()` and `halt(reason)`
  entrypoints. Every scheduled routine now invokes the breaker at multiple
  checkpoints (after boot, after mark refresh, after fills, after final
  nav_snapshot).
- **`skills/risk` slimmed to pure math.** NAV computation, baseline
  lookup, freshness summary, guardrail-recommendation surface. Halt
  writes moved to `skills/circuit-breaker`.
- **Research falls back to native web tools.** `skills/research` adds
  Agent native WebSearch / WebFetch as a fallback when no API keys are
  configured (ADR 0015). All native-tool calls count against the same
  3-source per-cycle cap.
- **Push is the explicit cycle success criterion** (ADR 0016).
  `skills/persist` now:
  - sets git identity idempotently every cycle (`GIT_AUTHOR_NAME` /
    `GIT_AUTHOR_EMAIL` defaults applied if env unset),
  - runs `git push --dry-run` before the first commit and halts with
    `push_permission_missing` if rejected,
  - verifies local HEAD matches `origin/<branch>` after push and writes
    the SHA to `cycle-index.json.last_pushed_commit`,
  - cycle routine prompts in README explicitly demand commit+push.

### Added

- ADR 0014 — circuit-breaker as skill, multi-checkpoint invocation.
- ADR 0015 — research native web tools fallback.
- ADR 0016 — push is the cycle success criterion.
- `skills/circuit-breaker/SKILL.md`.

### Removed

- `routines/circuit-breaker.md` (logic moved to skill; preserved in git
  history).

## [v0.2.0] — 2026-05-24

### Changed — Instruction Pack v1.1 (skills/routines split + 24/7 schedule)

- **Routines split from skills.** `routines/` now holds 5 thin scheduled
  playbooks; capability logic moved to 10 new `skills/<name>/SKILL.md` files
  (ADR 0011).
- **Schedule rebuilt for 24/7 + US weighting.** Four scheduled routines
  (`research-window` 12 UTC, `trade-window` 18 UTC, `daily-close` 22 UTC,
  `overnight-watch` 04 UTC) plus reactive `circuit-breaker`. Supersedes
  single hourly routine from v0.1.0 (ADR 0010 supersedes ADR 0009).
- **Each routine declares its cron** in YAML frontmatter at top of file.
- **Phase-miss detection.** Each routine grep-checks for the prior
  `phase_completed` event; missed phases logged + surfaced in the daily
  recap and Telegram summary.
- **Recaps as derived markdown files** in `recaps/`. Daily file every
  end-of-day; weekly file on Sundays using ISO week (ADR 0012).
- **Conventional Commits** for every agent commit with `[cycle <cycle_id>]`
  suffix (ADR 0013).
- **Wallet-secret constraint sharpened:** only `skills/trade/SKILL.md` may
  read `WALLET_SEED`.

### Added

- ADR 0010 — four phase routines, 24/7 US-weighted (supersedes 0009).
- ADR 0011 — skills vs routines split.
- ADR 0012 — daily + weekly recaps as derived markdown files.
- ADR 0013 — Conventional Commits.
- 10 skills under `skills/`: boot, research, markets, sizing, trade,
  journal, persist, notify, risk, recap, reflect.
- 5 routines under `routines/`: research-window, trade-window, daily-close,
  overnight-watch, circuit-breaker.
- `recaps/` directory (initially empty; populated by `daily-close`).

### Removed

- Old `routines/00-wake-up.md` through `routines/99-circuit-breaker.md`
  (10 files). Logic redistributed into skills + new routines. Preserved in
  git history.

## [v0.1.0] — 2026-05-24

### Added — Instruction Pack v1

- `CLAUDE.md` one-line shim → `AGENTS.md` (89-line model-agnostic boot prompt).
- `routines/` 00–99 playbooks: wake-up, load-state, research, analyze-markets,
  decide-and-size, execute-trade (paper + mainnet branches), log-and-persist,
  notify-telegram, reflect, circuit-breaker. All under 150 lines each.
- `config/guardrails.md` (canonical 5% per-position, 10%/24h halt, correlation,
  research cap, append-only log) and `config/mode.json` (paper default,
  observation_only true, hourly cadence, mainnet attestation gate).
- Seeded `state/`: `portfolio.json` ($54 USDC), `halts.json`, `lock.json`,
  `cycle-index.json`, empty `trade-log.jsonl`.
- `strategy/current.md` v0 baseline (agent-owned), `strategy/history/`.
- `research/INDEX.md` skeleton.
- `skills/polymarket/` git submodule → `Polymarket/agent-skills`.
- Human-facing `README.md`: cloud routine setup, env vars by mode, paper→mainnet
  promotion, pause protocol, log-reading recipes.

### Verification

- Boot context (AGENTS.md + 7 boot files) = 258 lines (< 600 cap).
- `wc -l AGENTS.md` = 89 (< 200 cap).
- `jq empty` validates all seeded JSON.
- `grep -ri "private_key\|signer\|createAndPostOrder\|WALLET_SEED" routines/`
  returns hits only in `routines/50-execute-trade.md`.
- `grep -ri "TODO" routines/` returns zero.
- 5%/10% guardrails appear in AGENTS.md, config/guardrails.md, and relevant
  routines (≥2 places each).

## [v0.0.2] — 2026-05-24

### Changed

- Renamed `pm/decisions/` → `pm/adrs/`; updated all cross-references.
- ADR 0004 rewritten: env vars now split by mode (paper needs only optional research
  keys; mainnet adds `WALLET_SEED` + `POLYMARKET_FUNDER_ADDRESS`).
  Deferred `PERPLEXITY_API_KEY` and `X_BEARER_TOKEN` for v1 due to cost/access
  constraints.
- PRD goal 7 added: agent as autonomous financial strategy modeler / wealth manager.
- PRD Users section expanded: agent is the financial reasoner; human provides
  credentials and guardrails only.
- Plan Phase 4 (README) and strategy seed updated to reflect the above.

## [v0.0.1] — 2026-05-24

### Added

- Project-management scaffold (`pm/` folder: README, CHANGELOG, prds/, plans/, adrs/).
- PRD for v1 Instruction Pack ([prds/v1-instruction-pack.md](prds/v1-instruction-pack.md)).
- Implementation plan for v1 Instruction Pack ([plans/v1-instruction-pack.md](plans/v1-instruction-pack.md)).
- ADRs 0001–0008 capturing locked design decisions.

### Notes

- No agent runtime files exist yet. Repo currently contains only `pm/` and git metadata.
- Root-level `PLAN.md` removed; design now lives under `pm/plans/`.
