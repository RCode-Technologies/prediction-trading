# 0009 — Cloud routine persists memory to default branch hourly

- **Status:** Superseded by 0010
- **Date:** 2026-05-24
- **Superseded:** 2026-05-24 — single hourly routine replaced by four
  phase-specific Claude cloud routines (research-window, trade-window,
  daily-close, overnight-watch). The memory-branch and idempotency contract
  is preserved by ADR 0010; only the schedule shape changed.
- **Related:** PRD v1-instruction-pack, ADR 0010, ADR 0011

## Context

Claude Code cloud routines run in fresh sessions. A commit that stays only in an
ephemeral workspace or on a generated `claude/` branch will not be visible to the next
scheduled run. The trading agent's memory therefore needs a branch contract, a push
contract, and overlap protection.

## Decision

v1 uses the repository default branch as the durable memory branch and runs on an
hourly Claude Code cloud routine schedule.

The routine must be configured with **Allow unrestricted branch pushes** for this
repo. At the start of every cycle, it fetches and rebases onto the memory branch,
then acquires `state/lock.json`. At the end of every cycle, it validates state, writes
`cycle_end`, commits, rebases once more, pushes to the memory branch, and releases the
lock. It never force-pushes.

For mainnet orders, the routine commits and pushes a `decision` event containing the
trade `idempotency_key` before submitting the order. If that pre-submit push fails,
the order is not submitted. If the post-submit push fails, the prior decision event is
already durable and later runs must not submit the same order again.

If branch push permission is unavailable, the routine halts before research or
trading. If an unexpired lock exists, the routine exits without trading. If a lock is
expired, the routine writes a `stale_lock_recovered` event and proceeds with a new
`cycle_id`.

## Consequences

- The next scheduled run starts from the prior run's committed state.
- Hourly cadence matches Claude routine schedule limits.
- Unrestricted branch push permission is required for unattended operation.
- Overlapping triggers do not duplicate mainnet orders because the lock and
  idempotency key checks run before execution.
