# Architecture Decision Records (ADRs)

Each ADR captures one decision that is expensive to reverse and worth remembering.
ADRs are numbered monotonically (`0001`, `0002`, …) and never renumbered.

## Statuses

- `Proposed` — under discussion.
- `Accepted` — current truth.
- `Superseded by NNNN` — replaced by a later ADR.
- `Deprecated` — no longer applies, but kept for history.

## Template

```markdown
# NNNN — <Short title>

- **Status:** Accepted
- **Date:** YYYY-MM-DD
- **Related:** PRD/plan/ADR links

## Context

Why we needed to decide something. What constraints/options were on the table.

## Decision

The choice we made, stated unambiguously.

## Consequences

What becomes easier, harder, or off-limits as a result.
```
