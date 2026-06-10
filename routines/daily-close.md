---
name: daily-close
cron: "0 22 * * *"
cron_tz: UTC
local_time: "17:00 ET"
phase: daily_close
expected_frequency: 1/day
runs_weekly_recap_on: Sunday (date '+%u' == 7)
---

# Daily Close — 22:00 UTC / 17:00 ET

Crystallize day's signals. Recap, reflect, daily Telegram. Sundays: also weekly. **Floor: ≥1 `recap`, ≥1 `reflection`.**

## Steps

1. `boot`
2. `circuit-breaker.evaluate()` — cp1 (v3: 24h halt **+ drawdown-from-peak governors + heat breach**). Halted/freeze → run step 7b (`recalibrate.sweep()` — read-only scoring; a halt blocks capital actions, not calibration) + daily summary if due (template carries the mandatory halt banner), then jump to 11.
3. **Phase-miss check.** Today's `phase_completed` for `research_window` + `trade_window`. Emit `phase_missed` per gap.
4. `markets` — final fresh-price snapshot on open positions (CLOB).
5. `circuit-breaker.evaluate()` — cp2 (post-marks).
6. `risk.nav()` + `journal.nav_snapshot`.
7. `circuit-breaker.evaluate()` — cp3 (post-snapshot; governors + heat on fresh NAV). Halted → surface in recap.
7a. **Disconfirmation-stop exit check (v3; `config/guardrails.md` § Disconfirmation stop).** For each open position: `risk.pnl_from_entry(position)` + scan `disconfirming_signals[]` against the day's marks/news. `pnl_pct <= -0.25` (non-stale) **or** a named disconfirming event → load `skills/sizing` with `learning_intent:"risk_reduction"` + the position + `stop_reason` → SELL via `skills/trade` (reducing/closing `paper_fill` at `best_bid`); surface the exit in recap. Exempt from any active freeze/probation. No trip → continue.
7b. **`recalibrate.sweep()`** — final daily sweep. Resolves open forecasts past `close_time`. Writes `state/scorecard.json` + `state/calibration.json`.
7c. **Sunday only** (`date '+%u' == 7`): load `skills/groom` and run it — rotate append-only logs out of the hot path + lint the brain for token bloat / drift. Returns `findings[]` for step 8. Non-Sunday: skip (groom is weekly; see `skills/groom` § Why weekly).
8. `recap` — write `recaps/YYYY-MM-DD.md` (reads `state/scorecard.json`). Sunday: also `recaps/YYYY-Www.md`, listing groom `findings[]` under *Recommendations for human review*.
9. `reflect` — once/UTC date. Reads scorecard. May edit `strategy/current.md` + snapshot.
9b. `envision` — once/UTC date, after reflect. Daily light pass (rotating lens): appends `proposals/horizon.jsonl`, always emits a `vision` event, may write `proposals/<date>-<slug>.md` + a `LEDGER.md` row and surface ≤1 proposal. Sunday: deep pass (MAX reasoning) — revises `proposals/VISION.md`, curates `LEDGER.md`, self-approves ≤1 non-vetoed `self_enactable` proposal. Idempotent on today's `vision` event; never blocks the cycle.
9c. `enact` — **Sundays only**, after `envision`. (a) Auto-rollback: a live enactment that regressed (`null_cycle` spike / `protected_core_violation` / `brier_skill` drop on forecasting-path changes) is auto-reverted (`revert(agent): auto-rollback <slug>`, standalone commit) + `notify enactment`; one clean ≥7d graduates to `live`. (b) Implement ≤1/week: the single `self_approved`, non-vetoed, denylist-clean proposal — apply its change-sketch, validate, commit standalone (`feat(agent): enact <slug>`), `notify enactment` (suppression-exempt), arm auto-rollback. Denylist hit or validation fail → refuse (`awaiting_human` / `enact_failed`), write no code. Never blocks the cycle.
10. `notify daily_summary`. Sunday: also `weekly_recap`. Then grep trade-log for this UTC date's `reflection` event: if `edited==true` OR `reason=="regression_blocked"` → also `notify strategy_evolution` as a separate message (template handles variants). Grep this UTC date's `vision` event: if `surfaced==true` → also `notify proposal`; Sunday also `notify vision_weekly`. Each kind is its own date-deduped message (`notify` step 2), so safe under re-runs.
11. `journal.phase_completed`.
12. `persist`.

## Source budget

0 research. CLOB freshness only (+ ≤1 CLOB book re-check per `risk_reduction` SELL) + ≤1 Gamma for `recalibrate.sweep` resolution lookup. Sunday groom adds 0 sources (local file work only).

## Position-close policy (v3)

- Near-resolution (`close_time < now + 12h`) flagged in recap.
- **v3 `risk_reduction` exit (replaces v2 "no auto-SELL").** Step 7a runs the disconfirmation stop: a held position at **−25% mark-from-entry** (non-stale, liquidation-marked) **or** a materialised named disconfirming event is reduced/closed via `skills/sizing` (`learning_intent:"risk_reduction"`) → `skills/trade` (paper: reducing/closing `paper_fill` at `best_bid`). The exit is logged as a `risk_reduction` `decision` + `paper_fill` and surfaced in the recap (stop reason + realized P&L). Exits are exempt from an active drawdown freeze/probation (you may always reduce risk).
- Halt active + mainnet position with `close_time < now + 12h` → recap highlights residual exposure.

## Failure modes

- Recap dedupe hit → skip recap; still notify if not sent.
- Reflect sees no data → `reflection edited:false`.
- Envision finds no new angle → `vision surfaced:false`; no proposal (a quiet day is not noise).
- Notify fails → `notification` failed-kind event; cycle continues.

## Commit

Per `skills/commit` § Routine-mapped subjects (`daily-close` rows). If reflection edited strategy, keep both artifacts in the same commit, prefer `feat(strategy)` subject. Body: recap paths, reflection result, notifications, open positions. Sunday groom archival rides this same commit — note archived counts + any lint findings in the body. Envision proposals + `LEDGER.md` updates ride this commit too (`skills/commit` § daily-close headline precedence). On Sundays `enact` pushes its own standalone revertible commit(s) *before* this cycle commit (see `skills/enact`); the cycle commit excludes enacted files.
