# 0002 — Polymarket skills loaded via git submodule

- **Status:** Accepted
- **Date:** 2026-05-24
- **Related:** PRD v1-instruction-pack

## Context

`Polymarket/agent-skills` provides ~1,700 lines of reference (`SKILL.md` + 7
reference files) using progressive disclosure. We can vendor it (copy), submodule
it, or fetch it fresh each scheduled run.

## Decision

Add it as a **git submodule** at `skills/polymarket/`. The agent reads
`SKILL.md` only inside `routines/50-execute-trade.md`'s mainnet branch, and
reference files (`order-patterns.md`, etc.) only when a routine explicitly demands
them.

## Consequences

- Stays in sync with upstream without copy/paste drift.
- Requires `git submodule update --init --recursive` in setup and verification. The
  mainnet execution routine still checks that `skills/polymarket/SKILL.md` exists
  before it can trade.
- If the submodule cannot be initialized in an ephemeral cloud run, mainnet execution
  fails closed before signing or submitting orders.
- Upstream renames/restructures will require pinning to a known-good commit.
