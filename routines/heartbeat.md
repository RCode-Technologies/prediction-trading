---
name: heartbeat
cron: "0 */4 * * *"
cron_tz: UTC
phase: heartbeat
expected_frequency: 6/day
---

# Heartbeat — every 4h

> **This is the pulse cycle** (Phase 6 framing): CLV snapshot + cheap mark + disconfirmation-stop check + liveness, all on a session already paid for. Adds zero forecasts, zero invocations. File stays named `heartbeat` (the cron points here); steps below are unchanged.

Dead-man's switch **+ CLV pulse + exit/governor check**. Cheap and idempotent. Fires when nothing else is happening; closes the silent-failure gap that the 4/day trade routines can't catch alone (if those stop firing, nothing alerts). v3 turns the bare liveness ping into a useful **pulse** cycle: it now does a cheap CLV snapshot + mark + a disconfirmation-stop scan while it's already paying for the session. Adds **zero** new forecasts and **zero** new invocations. (The conceptual "pulse" rename is Phase 6's doc job — this file MUST keep the name `heartbeat`; the cron points at it.)

## Steps

1. `boot` — sync + lock + validate + observation-transition + **liveness-gap check**. The boot gap check does the real work: > 9h since last completed cycle → emits `liveness_gap` + notify.
2. **No new forecasts, no opening trade.** No `forecast`, no opening BUY, no recap/reflect/research. The only work below is *reading* the live CLOB to score forecasts we already made, mark positions, and — the sole write action permitted — a **`risk_reduction` SELL** if a held position trips the disconfirmation stop (reducing risk is always allowed, even on the cheap pulse; it never opens new risk).
3. **CLV pulse — `recalibrate.snap_clv()`.** Snapshot the CLOB midpoint for open forecasts due a window (+6h/+24h/close) and update `clv_mean`/`clv_hit_rate` (per intent + `edge_source`). ≤8 CLOB book calls, 0 Gamma, oldest-emitted first; emits **no** `forecast`. Skip only if no open forecast is due (then it's a free no-op). This is what makes the pulse earn its session.
4. **NAV snapshot only if free.** `portfolio.positions == []` → skip. Positions exist AND last `nav_snapshot > 2h` → `markets.book()` per open position + emit one `nav_snapshot` (reuse the CLV book reads where the token overlaps — don't double-call). Skip if any book call would exceed budget.
4b. **Disconfirmation-stop exit check (v3; `config/guardrails.md` § Disconfirmation stop).** Only if positions exist and marks are fresh (reuse step 3/4 book reads — **no extra Gamma, ≤1 extra CLOB book per SELL**): for each open position `risk.pnl_from_entry(position)`. `pnl_pct <= -0.25` (non-stale) **or** a named `disconfirming_signals[]` event materialised → `skills/sizing` (`learning_intent:"risk_reduction"`) → `skills/trade` SELL at `best_bid`. Exempt from freeze/probation. No trip / stale marks / no positions → free no-op (the common case).
5. `circuit-breaker.evaluate()` — cp1 (v3: also surfaces drawdown-from-peak governors + heat breach). Heartbeat itself never halts (it persists governor/breach signals via the breaker; a `drawdown_freeze_15pct` halt is written by `evaluate()` as usual).
6. `journal.phase_completed phase:"heartbeat", clv_snaps:<n>, nav_refreshed:<bool>, risk_reduction_fired:<bool>, liveness_gap_fired:<bool>`.
7. `persist`.

## Source budget

0 research, 0 Gamma. ≤8 CLOB book calls for `snap_clv()` (due open forecasts) + ≤N for the NAV mark (N = open position count) + ≤1 CLOB book re-check per `risk_reduction` SELL, de-duped where tokens overlap. CLOB ≠ research. Still well within a cheap pulse.

## Failure modes

- Lock contention with another running routine → exit clean, no commit. **Expected behavior, not a gap.**
- Boot detects liveness gap → emit + notify; continue (heartbeat itself shouldn't add to the gap).
- Halts active → still run step 3 (`recalibrate.snap_clv()` — read-only CLOB scoring; a halt blocks capital actions, not calibration), then log, persist, exit (no NAV refresh, no exit scan this cycle — the disconfirmation stop re-fires in the next non-halted pulse / in overnight-watch / daily-close, which run their exit check before any breaker-halt jump). A `drawdown_freeze_15pct` written this cycle does not block a `risk_reduction` SELL (exits are exempt; see `config/guardrails.md`).
- No open forecast is due a snap → `snap_clv()` is a free no-op (`clv_snaps:0`); the pulse falls back to liveness + mark only. Not a failure.
- No position trips the stop (the common case) → step 4b is a free no-op (`risk_reduction_fired:false`). Not a failure.

## Notify

Suppression-exempt only: `liveness_gap` (via boot), `circuit_breaker` (incl. v3 `drawdown_freeze_15pct`), **a v3 `risk_reduction` exit fill** (a stop firing is material — note stop reason + realized P&L), `persist_conflict`. No `routine_summary` — silence is success at 2h cadence.

## Commit

Per `skills/commit` § Routine-mapped subjects (`heartbeat` rows). Commits accumulate; that's intentional — the history doubles as a liveness audit log.
