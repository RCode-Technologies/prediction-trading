# 0007 — Strategy snapshot on every reflection-driven edit

- **Status:** Accepted
- **Date:** 2026-05-24
- **Related:** PRD v1-instruction-pack, routine 80-reflect

## Context

The reflection routine rewrites `strategy/current.md` periodically. We need a
history mechanism. Options: snapshot on every edit (verbose) or daily rollup
(cleaner).

## Decision

**Snapshot on every edit.** Before writing the new strategy, copy the current
`strategy/current.md` to `strategy/history/YYYY-MM-DD-vN.md` where N increments per
day. The new strategy commit must reference the prior snapshot path in its commit
message.

## Consequences

- Full lineage of strategy evolution, useful for forensic review after losses.
- Reflection runs ≤1×/day, so history growth is bounded (~30 files/month).
- No dedupe logic needed; if two reflections produce identical strategies, the
  duplicate snapshot is acceptable noise.
