---
name: heartbeat
cron: "0 */2 * * *"
cron_tz: UTC
phase: heartbeat
expected_frequency: 12/day
---

# Heartbeat — every 2 hours

Dead-man's switch independent of the 4 scheduled trade routines. Cheap and idempotent. The only routine that should fire when nothing else is happening.

This routine exists because the agent's 4/day cycles are themselves the system's only liveness signal in the original design — if they stop firing, there is no alert. Heartbeat closes that gap: it confirms the cron timer infrastructure (managed in the Claude Code UI) is still triggering Claude sessions on this repo.

## Steps

1. `boot` — runs the standard sync + lock + validate + observation-transition + **liveness-gap check** sequence. The liveness check inside boot is what does the real work here: if the last full cycle was > 9h ago, boot emits `liveness_gap` and notifies. Heartbeat just gives boot the chance to fire.
2. **No phase work.** Heartbeat does not run markets, sizing, trade, recap, or reflect. The whole point is to be cheap.
3. **NAV snapshot only if free.** If `state/portfolio.json.positions == []`, skip — there's nothing to mark. If positions exist AND the last `nav_snapshot` is > 2h old, call `markets.book()` on each open position's token (CLOB, not research) and emit one `nav_snapshot`. Skip mark refresh if any book call would push us over budget (heartbeat has 0 research source budget).
4. `circuit-breaker.evaluate()` — cp1. Halts use the breaker's normal path. The heartbeat itself never halts.
5. `journal.phase_completed` with `phase:"heartbeat"`, `nav_refreshed:<bool>`, `liveness_gap_fired:<bool>`.
6. `persist` — commit + push. Subject: `chore(cycle): heartbeat [cycle <cid>]`. Body: 1-2 lines.

## Source budget

0 research sources. ≤N CLOB book calls where N = open position count (only if NAV refresh actually fires).

## Failure modes

- Lock contention with another running routine → exit clean, no commit. The other routine's persist handles its own push. Heartbeat being skipped due to lock is **expected behavior, not a gap**.
- Boot detects liveness gap → emit + notify; continue normally so this heartbeat itself doesn't add to the apparent gap.
- Halts active → log, persist, exit (no NAV refresh).

## Notify

- Suppression-exempt: `liveness_gap` (via boot), `circuit_breaker`, `persist_conflict`.
- No `routine_summary` for heartbeat — silence is the success case at 2h cadence (would otherwise spam Telegram 12×/day).

## Commit

Subject per `skills/commit/SKILL.md` § Routine-mapped subjects (`heartbeat` rows). One commit per heartbeat — the commit history doubles as a liveness audit log; that's intentional.
