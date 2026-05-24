# 0014 — Circuit breaker is a skill, invoked at multiple checkpoints

- **Status:** Accepted
- **Date:** 2026-05-24
- **Related:** ADR 0010 (amended), ADR 0011 (skills/routines split)

## Context

v1.1 (ADR 0010) introduced four scheduled routines plus a "reactive"
`routines/circuit-breaker.md`. In practice that file was never on a cron —
it documented a protocol that other routines invoked via `skills/risk`.
Calling it a routine was misleading, because:

1. **Routines are scheduled triggers** (each declares a cron at top, ADR
   0011). A reactive file with `cron: null` is not a routine; it's a
   capability — i.e. a **skill**.
2. **A single end-of-cycle check is not enough.** Mark prices can move
   between cycle phases; mainnet partial-fill failures need a forced halt
   inline with the trade flow, not as a cron event. The breaker must be
   callable from inside other routines at multiple checkpoints.

## Decision

- Delete `routines/circuit-breaker.md`.
- Promote the breaker to `skills/circuit-breaker/SKILL.md`. Two
  entrypoints:
  - `evaluate()` — read state, compute rolling 24h P&L via `skills/risk`,
    fire halt on breach.
  - `halt(reason, ...)` — force halt for non-loss reasons
    (`mainnet_cancel_failed`, `post_submit_push_failed`,
    `no_baseline_nav`, `push_permission_missing`,
    `unreconciled_cash_delta`).
- `skills/risk` becomes a pure math helper (NAV, baseline, freshness).
  All halt writes happen in `skills/circuit-breaker`.
- Every scheduled routine calls `skills/circuit-breaker.evaluate()` at
  multiple checkpoints:

  | Routine | Checkpoints |
  |---|---|
  | research-window | (1) after boot |
  | trade-window | (1) after boot, (2) after mark refresh, (3) after each fill, (4) after final nav_snapshot |
  | daily-close | (1) after boot, (2) after mark refresh, (3) after final nav_snapshot, (4) after recap |
  | overnight-watch | (1) after boot, (2) after mark refresh + nav_snapshot (most likely fire site), (3) after any opportunistic fill |

- Failure modes that previously called into `skills/risk` to halt now
  call `skills/circuit-breaker.halt(...)` directly. `skills/trade` is
  the main user of the forced-halt path.

## Consequences

- The skill/routine taxonomy from ADR 0011 is now consistent — no more
  pseudo-routine.
- Multi-checkpoint evaluation catches breaker breaches sooner (e.g. an
  Asian-time crash that would previously sit unnoticed until
  `daily-close` is caught during `overnight-watch`'s mark refresh).
- `skills/risk` is now small enough to be inlined mentally — it owns no
  state machine, only math.
- The number of `evaluate()` calls per cycle is small (1–4) and each is
  cheap, so token impact is negligible compared to the safety gain.

## Amends ADR 0010

ADR 0010 listed five routines including `circuit-breaker`. As of this
ADR, that fifth file is removed; ADR 0010's schedule table is now four
scheduled routines only.
