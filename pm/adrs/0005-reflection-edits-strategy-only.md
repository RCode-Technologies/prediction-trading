# 0005 — Reflection edits `strategy/current.md` only; guardrails are human-only

- **Status:** Accepted
- **Date:** 2026-05-24
- **Related:** PRD v1-instruction-pack, routine 80-reflect

## Context

The daily reflection routine reads outcomes and updates strategy. Open question was
whether it may also tighten `config/guardrails.md` (e.g. 5% → 3% per position). A
self-modifying safety layer is risky even when constrained to "tightening only".

## Decision

The reflection routine (`routines/80-reflect.md`) may edit **only**
`strategy/current.md`. It must never modify `config/guardrails.md` or `AGENTS.md`.
Guardrails are exclusively human-edited.

## Consequences

- Stable safety floor — humans review every guardrail change.
- Strategy can iterate freely (it operates within guardrails, not against them).
- If the agent believes guardrails should change, it must surface this in the next
  cycle's Telegram daily summary as a recommendation for human action.
