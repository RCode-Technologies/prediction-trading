# 0001 — Markdown-only instruction pack; coding-agent runtime

- **Status:** Accepted
- **Date:** 2026-05-24
- **Related:** PRD v1-instruction-pack

## Context

The agent runs in ephemeral scheduled coding-agent sessions, with v1 deployed through
Claude Code cloud routines. The host provides shell, network, git, and environment
variables. We need to choose between writing an application (Python/TS), or expressing
the agent entirely as markdown instructions that the scheduled agent follows using its
built-in tools.

## Decision

The repo contains **only markdown instructions and JSON/JSONL state files**. No
application code is checked in. `AGENTS.md` is the model-agnostic boot prompt.
`CLAUDE.md` exists only as a Claude Code compatibility shim and contains one concise
line telling Claude Code to read `AGENTS.md`. The agent reads on-demand routines and
uses shell tools for all actions (curl, jq, git, optional `uvx`/`pip` install of
`py-clob-client` for mainnet orders).

## Consequences

- Lower maintenance: no dependencies, no build step.
- Easy to inspect and audit by humans — everything is prose.
- Behavior is bounded by what the scheduled coding-agent runtime allows; no custom binaries.
- Performance ceiling is whatever bash + curl can deliver per cycle.
- Future migration to a coded service is possible; markdown becomes the spec.
