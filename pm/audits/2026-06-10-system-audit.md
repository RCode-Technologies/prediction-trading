# 2026-06-10 Full-System Audit (post-outage)

Human-directed session (theo6890 via Claude, interactive). Trigger: system halted
`nav_reconciliation_failed` on 2026-05-29 16:11Z and stayed dead 12 days until manually noticed.

## Recovery (pushed as f2e928d)

- Root cause: human commit 530f85f (2026-05-27 "paper baseline reset to $10k") injected
  +736.7407 shares / $276.28 without a ledger event and scaled a position 185× — exactly what the
  v3 capital-integrity rule (landed 2026-05-29, hours later) exists to catch. The halt was the
  system **working correctly**.
- Fix: restatement `paper_fill` (forecast_id:null, authorized_by theo6890_interactive_recovery)
  books the injection explicitly. Replay verified: expected_cash = 10000 − 227.20 − 276.28 + 243.13
  = 9739.65 == portfolio.cash_usdc; net shares per token = 0 == empty positions. Halt cleared.
- Note: cycle-index nav history 05-24→05-27 was rewritten by 530f85f and permanently contradicts
  the append-only trade-log for those dates (log line 3 says nav 54). Known, explained, do not
  "fix" — never rewrite history again; capital changes are `deposit`/`withdrawal` events only.

## Why 12 days of silence (the meta-failure)

The halt notified **once** at trip time. Then: `evaluate()` returns `already_active` without
notifying; boot's halt branch was silent; `null_cycle` was explicitly suppressed during halts;
the 8 daily summaries sent during the outage had no halt field (looked healthy); `liveness_gap`
never fired because heartbeats kept committing (it measures the scheduler, not trading); no
external watchdog existed. Every human-resume-only halt reason shared this failure mode.

## Fixes applied (this session, human-authored)

| Area | Change |
|---|---|
| `skills/boot` | Active halt → daily date-deduped `halt_active` notify with age; explicit jump-to-persist; **5c formula corrected** (expected cash uses full SELL proceeds, not "realized P&L" — the text/practice mismatch was a spurious-halt generator) |
| `skills/notify` (+2 templates, +1 new) | `halt_active` kind (suppression-exempt, date-deduped); mandatory 🛑 banner on both daily-summary variants |
| `skills/persist` | Push preflight is bare `git push --dry-run` (the literal `origin main` pattern is blocked by a global hook → false `push_permission_missing`); `null_cycle reason:"halted"` logged (not suppressed, notify skipped); halted `cycle_end` must carry `halted:true, halt_reason` |
| `skills/commit` | Canonical subject for halted no-op cycles (codifies practice; was 39/91 inconsistent) |
| `skills/circuit-breaker` | Recovery section documents daily re-escalation + learning-during-halt |
| `routines/{daily-close,overnight-watch,heartbeat}` | **Read-only calibration continues during halt** (sweep/snap_clv before the halted jump). The outage stranded 9 of 15 open forecasts past close_time unswept — 12 days of calibration data nearly lost. A halt stops capital actions, never the learning loop. |
| `AGENTS.md` | One line codifying the above halt semantics |
| `skills/journal` | `learning_intent` validated on `decision` too; SELL fills must carry non-null `realized_pnl_usdc` (Iran exit logged null); human-restatement fill pattern documented |
| `skills/recalibrate` | Fills with `forecast_id:null` explicitly skipped (`skipped_no_forecast_id`); **sweep 7b seeds `historical_prior` per cold exploit bucket from `tools/bootstrap-calibration.json`** (538 resolved markets; was orphaned) — reference-only, never counts as live data, dropped at `resolved_n ≥ 10` |
| `skills/sizing` | Correlation guard now a deterministic 4-rule algorithm with named bucket ids + `correlation_uncertain` reject reason (was one ambiguous line) |
| `.github/workflows/watchdog.yml` | External dead-man's switch on GitHub's scheduler: no-commit >10h or halt >24h → Telegram (if Actions secrets set) else GitHub issue. The only alert path that survives total local-scheduler death. |

## Operator actions for theo

1. **Optional but recommended:** add `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` as GitHub Actions
   secrets so the watchdog alerts via Telegram instead of GitHub issues.
2. First post-restart daily-close (22:00 UTC) will sweep ~9 expired forecasts — expect a large
   `resolved_new` and the first real scorecard refresh since 05-29. Worth eyeballing the recap.
3. `state/trade-log.jsonl` is past the 500-line groom threshold; first-ever groom rotation runs
   next Sunday — watch its `archived + kept == original` assert.

## Considered, deliberately not done

- **Reflect 2×/day / raise forecast batch targets** — forecast volume and reflection cadence are
  strategy-owned (delegated to the agent per AGENTS.md § User operating context). The latency wins
  here came from infra: calibration-during-halt, bootstrap prior, CLV pulse already every 4h. If
  you want faster still, the lever is raising the batch target in `strategy/current.md` — let
  reflect/envision propose it.
- **Editing `config/guardrails.md`** — human-owned; nothing found that requires loosening rails.
- **claude/ branches** — none exist (local or origin; verified `git ls-remote`). History shows
  they were cherry-picked into main and removed on 2026-05-29 when main-only enforcement landed.

## Audit verdicts (4 parallel reviews: control, trading/risk, learning, state/ops)

- Control plane: sound defense-in-depth (lock TTL + stale recovery, append-only log, dual branch
  hooks, protected core). Fixed: formula text, preflight pattern, halt lifecycle gaps.
- Trading/risk: math correct (Kelly, ladder, governors verified against the Iran fills); v2-era
  forecasts lack v3 gate fields (aging out naturally — sweep resolves them); paper-fill fidelity
  (BUY@ask/SELL@bid, liquidation marks) consistent everywhere.
- Learning loop: structurally closed (forecast→CLV→scorecard→reflect→strategy), multi-gate
  anti-overfitting, auto-revert. Bottleneck was data starvation during halts + cold-start void —
  both addressed.
- State integrity: all files parse, schemas uniform, event ids unique, scorecard ↔ ledger counts
  consistent; one orphan cycle_end (typo'd id, documented in-log) and the 530f85f history rewrite
  are known, explained warts.
