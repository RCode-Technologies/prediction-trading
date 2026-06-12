# 2026-06-10 Full-System Audit (post-outage)

Human-directed session (theo6890 via Claude, interactive). Trigger: system halted
`nav_reconciliation_failed` on 2026-05-29 16:11Z and stayed dead 12 days until manually noticed.

## Addendum — 2026-06-10 08:12Z confabulated `protected_core_violation` halt

Hours after the restart, the 08:12Z heartbeat halted on `protected_core_violation` naming
`config/autonomy.md, config/guardrails.md, skills/enact, skills/risk`, citing "genesis commit
e89b223". **This was a fabrication.** Ground truth (`git log -1 --format=%ae` per path): all four —
and all nine protected-core paths — are last-authored by `mail@rcode.tech` (human). `e89b223` is not
a genesis commit; it is an unrelated 2026-06-04 heartbeat that touches none of those files. The
deterministic audit prints `PROTECTED_CORE_VIOLATIONS:[ ]` (empty). No violation existed.

Why it happened: boot 5b was prose an LLM *interprets* ("author email == agent → halt"), not a script
it *runs*. The heartbeat cycle reasoned narratively about authorship, confused genesis/oldest with
newest, invented a hash, and tripped the breaker. The earlier `nav_reconciliation_failed` halt had
masked this latent fragility (boot returned at step 5 before reaching 5b); clearing it exposed it.

Fix: boot 5b rewritten as a copy-pasteable deterministic snippet whose printed `PROTECTED_CORE_VIOLATIONS`
list is the *only* admissible evidence, plus HARD anti-confabulation rules (newest-author-only; never
reason from genesis; never halt from memory or a guessed hash). False halt cleared (verified empty).
Lesson generalizes: any LLM-executed gate that can halt capital ops must emit a mechanical verdict, not
invite narrative judgement.

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

## Addendum 2 — 2026-06-12: the confabulation recurred; 5b made a script

Human-directed session (theo6890 via Claude, interactive). Trigger: "trading is still halted."

**What actually happened.** The 06-10 clearance (`3a1b23a`) did NOT hold. ~8 min later the
12:15Z heartbeat and 12:19Z research_window halted again on `protected_core_violation`, this time
citing a *different* "genesis scaffold commit" (`2725337`) — itself a 2026-06-05 `overnight_watch`
heartbeat that touches **none** of the four named files. Identical failure mode to the 08:12Z
confabulation (`e89b223`), and it then re-tripped every cycle for two more days (06-10 → 06-12),
all halted, scheduler healthy throughout (~15 cycles). Addendum 1's prose rewrite + HARD
anti-confabulation rules were **not enough**: 5b was still an LLM-*interpreted* instruction, so the
cycle kept narrating a violation instead of running the check.

**Ground truth (verified this session against `origin/main` HEAD `c224e41`).**
`bash skills/boot/protected-core-audit.sh` → `PROTECTED_CORE_VIOLATIONS:[ ]`, exit 0. All nine
protected paths last-authored by `mail@rcode.tech`. 5c reconciles
(`10000 − 1.50 − 225.70 + 243.13 − 276.28 = 9739.65 == cash`, 0 positions). No violation existed.

**Fix applied (human-authored, this session).**
| Area | Change |
|---|---|
| `skills/boot/protected-core-audit.sh` | **New committed script** — the deterministic check is now executable, not prose. Emits `PROTECTED_CORE_VIOLATIONS:[…]` + exit 0/3. `cd`s to repo root; newest-commit author per path; genesis explicitly irrelevant. |
| `skills/boot` 5b | Rewritten to `bash skills/boot/protected-core-audit.sh` and act SOLELY on its exit code (0=pass, 3=halt with the hash IT printed, other=inconclusive→continue). HARD: no `protected_core_violation` halt may be written without a matching exit-3 *this cycle*. |
| `state/halts.json` | Cleared (the confabulation). |

**Lesson (now demonstrated twice).** Addendum 1 already said "any LLM-executed gate that can halt
capital ops must emit a mechanical verdict, not invite narrative judgement" — but the fix stopped at
*better prose*. Prose was re-narrated within minutes. The durable fix is to move the verdict OUT of
the model's discretion into a committed script whose exit code boot obeys. Apply this pattern to any
other halt gate that an LLM evaluates from prose.

## Still open for theo (2026-06-12)

1. **Rogue branch `claude/serene-brown-or8nac`** exists on origin (1 commit, `91f9696`, a 06-11
   halted heartbeat) — violates the main-only HARD rule. Recoverable by SHA. Delete with
   `git push origin --delete claude/serene-brown-or8nac` once you've confirmed nothing unique is on it.
2. Watch the next *unattended* cloud cycle boot clean (5b exit 0, no halt) to confirm the fix holds
   without a human in the loop.
