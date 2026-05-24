# Changelog

All notable changes to this project are tracked here. Newest entries on top.
Versioning is loose semver-ish: `v0.x` until first mainnet trade, then `v1.0`.

## [Unreleased]

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
