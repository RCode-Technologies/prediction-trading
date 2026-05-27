---
name: heartbeat
cron: "0 */4 * * *"
cron_tz: UTC
phase: heartbeat
expected_frequency: 6/day
---

# Heartbeat — every 4h

Dead-man's switch. Cheap and idempotent. Fires when nothing else is happening; closes the silent-failure gap that the 4/day trade routines can't catch alone (if those stop firing, nothing alerts).

## Steps

1. `boot` — sync + lock + validate + observation-transition + **liveness-gap check**. The boot gap check does the real work: > 9h since last completed cycle → emits `liveness_gap` + notify.
2. **No phase work.** No markets, sizing, trade, recap, reflect.
3. **NAV snapshot only if free.** `portfolio.positions == []` → skip. Positions exist AND last `nav_snapshot > 2h` → `markets.book()` per open position + emit one `nav_snapshot`. Skip if any book call would exceed budget (heartbeat has 0 research budget).
4. `circuit-breaker.evaluate()` — cp1. Heartbeat itself never halts.
5. `journal.phase_completed phase:"heartbeat", nav_refreshed:<bool>, liveness_gap_fired:<bool>`.
6. `persist`.

## Source budget

0 research. ≤N CLOB book calls where N = open position count (only if NAV refresh fires).

## Failure modes

- Lock contention with another running routine → exit clean, no commit. **Expected behavior, not a gap.**
- Boot detects liveness gap → emit + notify; continue (heartbeat itself shouldn't add to the gap).
- Halts active → log, persist, exit (no NAV refresh).

## Notify

Suppression-exempt only: `liveness_gap` (via boot), `circuit_breaker`, `persist_conflict`. No `routine_summary` — silence is success at 2h cadence.

## Commit

Per `skills/commit` § Routine-mapped subjects (`heartbeat` rows). Commits accumulate; that's intentional — the history doubles as a liveness audit log.
