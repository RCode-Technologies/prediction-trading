# Changelog

All notable changes to this project are tracked here. Newest entries on top.
Versioning is loose semver-ish: `v0.x` until first mainnet trade, then `v1.0`.

## [Unreleased]

### Planned — v0.1.0 (Instruction Pack v1)

- See [pm/prds/v1-instruction-pack.md](prds/v1-instruction-pack.md) and
  [pm/plans/v1-instruction-pack.md](plans/v1-instruction-pack.md).
- Revised v1 planning for Claude Code cloud routines: hourly cadence, `CLAUDE.md`
  shim + model-agnostic `AGENTS.md`, default-branch memory persistence, repo-backed
  lock/idempotency, explicit state schemas, risk formulas, cloud environment/network
  setup, mainnet preflights, and `WALLET_SEED` as the only wallet secret env var.

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
