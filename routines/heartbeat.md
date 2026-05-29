---
name: heartbeat
cron: "0 */4 * * *"
cron_tz: UTC
phase: heartbeat
expected_frequency: 6/day
---

# Heartbeat — every 4h

Dead-man's switch **+ CLV pulse**. Cheap and idempotent. Fires when nothing else is happening; closes the silent-failure gap that the 4/day trade routines can't catch alone (if those stop firing, nothing alerts). v3 turns the bare liveness ping into a useful **pulse** cycle: it now does a cheap CLV snapshot + mark while it's already paying for the session. Adds **zero** new forecasts and **zero** new invocations. (The conceptual "pulse" rename is Phase 6's doc job — this file MUST keep the name `heartbeat`; the cron points at it.)

## Steps

1. `boot` — sync + lock + validate + observation-transition + **liveness-gap check**. The boot gap check does the real work: > 9h since last completed cycle → emits `liveness_gap` + notify.
2. **No new forecasts, no trade.** No `forecast`, sizing, trade, recap, reflect, research. The only work below is *reading* the live CLOB to score forecasts we already made + mark positions.
3. **CLV pulse — `recalibrate.snap_clv()`.** Snapshot the CLOB midpoint for open forecasts due a window (+6h/+24h/close) and update `clv_mean`/`clv_hit_rate` (per intent + `edge_source`). ≤8 CLOB book calls, 0 Gamma, oldest-emitted first; emits **no** `forecast`. Skip only if no open forecast is due (then it's a free no-op). This is what makes the pulse earn its session.
4. **NAV snapshot only if free.** `portfolio.positions == []` → skip. Positions exist AND last `nav_snapshot > 2h` → `markets.book()` per open position + emit one `nav_snapshot` (reuse the CLV book reads where the token overlaps — don't double-call). Skip if any book call would exceed budget.
5. `circuit-breaker.evaluate()` — cp1. Heartbeat itself never halts.
6. `journal.phase_completed phase:"heartbeat", clv_snaps:<n>, nav_refreshed:<bool>, liveness_gap_fired:<bool>`.
7. `persist`.

## Source budget

0 research, 0 Gamma. ≤8 CLOB book calls for `snap_clv()` (due open forecasts) + ≤N for the NAV mark (N = open position count), de-duped where tokens overlap. CLOB ≠ research. Still well within a cheap pulse.

## Failure modes

- Lock contention with another running routine → exit clean, no commit. **Expected behavior, not a gap.**
- Boot detects liveness gap → emit + notify; continue (heartbeat itself shouldn't add to the gap).
- Halts active → log, persist, exit (no CLV snapshot, no NAV refresh).
- No open forecast is due a snap → `snap_clv()` is a free no-op (`clv_snaps:0`); the pulse falls back to liveness + mark only. Not a failure.

## Notify

Suppression-exempt only: `liveness_gap` (via boot), `circuit_breaker`, `persist_conflict`. No `routine_summary` — silence is success at 2h cadence.

## Commit

Per `skills/commit` § Routine-mapped subjects (`heartbeat` rows). Commits accumulate; that's intentional — the history doubles as a liveness audit log.
