# Plan — v3: Edge, Honest Accounting, and Fast Learning

- **Status:** Proposed (awaiting redline — not implemented)
- **Date:** 2026-05-29
- **PRD:** [../prds/v3-edge-and-learning.md](../prds/v3-edge-and-learning.md)

## How to read this plan

Seven phases, ordered so each is independently shippable and verifiable. **Phases 0–1 are correctness/safety and land before any new bet.** Phases 2–3 are the core edge + fast-learning work. Phases 4–6 deepen learning and clean up. Each phase lists **owner**, **files**, **change**, **verify**. **All phases (0–8) were implemented
2026-05-29 (paper-mode)** — phases 0–6 (edge/accounting/learning/risk/cost-model) plus 7–8
(self-direction, repo hygiene). Mainnet stays off. The Iran exit (Phase 0) was executed by the
system's own new disconfirmation stop (Phase 5), not by hand.

Strategy v3 is cut over at the start of Phase 2 (snapshot v2 → `strategy/history/2026-05-29-v2.md`, bump `current.md` to v3). Everything is paper-mode; mainnet stays off. Edits to `config/guardrails.md` and the cron schedule are **supervisor-owned** and called out explicitly — the builder prepares the diff, the human accepts.

---

## Scheduled-invocation budget (hard constraint)

The metered cost is the **cycle** (one paid agent session), **not** the line of context v2 optimized. Plan ceiling: **15 invocations/day** (included; over = paid). Current = **10/day**. v3 stays at **10/day by repurposing, not adding.**

| Slot (UTC) | Today | v3 | Work done in v3 |
|---|---:|---:|---|
| research-window 12:00 | 1 | 1 | broad forecast-only batch (learning) + gate-passing bets |
| trade-window 18:00 | 1 | 1 | gate-passing bets + broad forecast-only batch |
| daily-close 22:00 | 1 | 1 | recap/reflect + CLV-at-close + exit checks + `recalibrate.sweep` |
| overnight-watch 04:00 | 1 | 1 | NAV + governors + CLV snapshot + exit checks |
| heartbeat → **pulse** ×6 (every 4h) | 6 | 6 | liveness **+** CLV snapshot of due forecasts + cheap mark + disconfirmation check |
| **Total** | **10** | **10** | **5/day slack reserved, unspent by default** |

The 6 ex-heartbeats become useful "pulse" cycles at **zero added invocation cost** — this is where the CLV pipeline lives. Spend the 5-cycle slack only on a backtest-justified improvement (e.g., a same-day pre-close snapshot); **never exceed 15** without explicit supervisor cost-approval.

> **Cron note:** README says heartbeat `0 */2` (12/day) but `AGENTS.md` says `0 */4` (6/day) and the supervisor confirms 6/day. Phase 6 fixes README to `0 */4` and renames "heartbeat" → "pulse." Net invocations are unchanged by v3.

---

## Phase 0 — Capital integrity reset + Iran exit *(safety; do first)*

**Owner:** builder (one-time, supervised). **Resolves PRD decision #1.**

**Files:** `state/portfolio.json`, `state/trade-log.jsonl` (exit + reset events), `state/cycle-index.json` (baseline), `skills/boot/SKILL.md`, `skills/risk/SKILL.md`, `AGENTS.md` (boot step).

**Change:**
- **Exit the Iran position now, take the loss.** Sell `2354045` YES at the live bid (≈0.23): log a `risk_reduction` `decision` + `paper_fill` closing all 1350.74 shares, realizing ≈ −$193 vs the recorded cost basis. Book goes flat. *Document* that the cost basis is partly the prior 185× synthetic scaling, so the realized figure inherits that distortion (this is the last time that distortion can occur).
- **Clean baseline.** Resulting state = cash ≈ $9,807, zero positions. Record `starting_capital` history honestly; do **not** round back to $10k by fiat.
- **Boot reconciliation invariant.** `skills/boot` recomputes `NAV = cash + Σ(shares × fresh_mark)`; divergence > $0.01 from expected (`starting_capital` ± logged fills/deposits) → `circuit-breaker.halt("nav_reconciliation_failed")`.
- **New allowed events:** `deposit`, `withdrawal` (so capital changes are explicit, never implicit scaling). `AGENTS.md` boot section states: **positions are never scaled to fit a baseline.**

**Verify:** AC #13 — post-exit `jq` shows NAV = cash, no positions; inject a fake unexplained cash delta → boot halts; grep confirms no `manual_baseline_reset`-style scaling in new state; the Iran exit appears as a `risk_reduction` fill.

---

## Phase 1 — Cost-honest accounting *(safety; do second)*

**Owner:** builder. **Implements ADR 0017.**

**Files:** `skills/markets/SKILL.md`, `skills/sizing/SKILL.md`, `skills/trade/SKILL.md`, `skills/risk/SKILL.md`, `config/guardrails.md` *(supervisor)*, `strategy/current.md`.

**Change:**
- `markets.book()` already returns both sides — surface `best_bid`, `best_ask`, `spread`, `executable_price` (ask for BUY / bid for SELL) on the candidate record; stop using `midpoint` as the trade price.
- **Paper fill price = `best_ask`** (BUY) / **`best_bid`** (SELL). Model `fee_usdc` from the Polymarket schedule.
- `risk.nav()` marks long positions at **`best_bid`** (liquidation); store `mark_mid` + `mark_liquidation` per position.
- *(Supervisor)* `config/guardrails.md`: sizing and NAV use executable/liquidation prices; cap + governors operate on liquidation NAV.
- `strategy/current.md`: define `edge_net = your_p − best_ask` (YES BUY); replace midpoint language.

**Verify:** AC #1/#2 — paper BUY on the Iran-style book logs `fill_price == ask`; NAV marks at bid; `fee_usdc > 0`.

---

## Phase 2 — Edge gate + forecast/trade split *(core)*

**Owner:** builder (pack) + agent (strategy params). **Cut over to strategy v3 here. Implements ADR 0018. Resolves PRD decision #3 (forecast floor) and #5 (edge_source tagging).**

**Files:** `strategy/current.md` (v3), `strategy/history/2026-05-29-v2.md` (snapshot), `skills/research/SKILL.md`, `skills/markets/SKILL.md`, `skills/sizing/SKILL.md`, `routines/research-window.md`, `routines/trade-window.md`, `skills/journal/SKILL.md` (new fields).

**Change:**
- **Snapshot v2**, bump `current.md` to v3, changelog entry (ADR 0007).
- New mandatory forecast fields: `resolution_criteria` (from Gamma `description`), `resolution_parsed`, `reference_class`, `edge_source` tag, `best_ask`, `best_bid`, `spread`, `edge_net`, `sizing_tier`.
- `research`: an **exploit** thesis MUST fetch + parse the `description` and name a reference class with ≥2 sources, else the candidate is explore-only.
- `sizing` **edge gate** (exploit): require `resolution_parsed` ∧ `reference_class != null` ∧ `len(source_providers) ≥ 2` ∧ `edge_net ≥ net_edge_floor`; any miss → `forecast` only with `decision reason ∈ {resolution_unparsed, no_reference_class, insufficient_sources, edge_below_net_threshold}`.
- **Forecast floor replaced (decision #3):** drop "≥3 forecasts every cycle." research-window + trade-window each emit a broad **forecast-only** batch (target ~8–12/day combined); only gate-passers (0–2/day) reach `trade`. Pulse cycles emit **no** new forecasts. Tag every forecast with `edge_source`.

**Verify:** AC #3 — replay 05-27 Iran inputs → forecast-only. Binding reasons are **qualitative**: `resolution_unparsed` (description never read), `no_reference_class` (the "0.45–0.55" base rate was invented), `insufficient_sources` (1 source, gate needs ≥2). The net-edge floor would *not* have caught it alone — at entry the ask was ~0.38, so `edge_net ≈ 0.45−0.38 ≈ 7pp` cleared 300 bps. That is the lesson: the edge was **unverifiable**, not merely thin — so the gate blocks on *provenance*, not just magnitude. AC #4/#5/#6 pass on a fresh slate.

---

## Phase 3 — Fast learning: CLV pipeline on the pulse cycles *(core)*

**Owner:** builder. **Implements ADR 0019 (CLV half). Zero added invocations.**

**Files:** `skills/recalibrate/SKILL.md`, `state/scorecard.json` (schema), `state/forecasts.open.jsonl` (schema), `strategy/current.md` (smartness section), `routines/overnight-watch.md`, `routines/heartbeat.md` (→ pulse).

**Change:**
- Extend the open-forecast ledger: `market_p_t0` + `clv_snaps:[{t:"+6h",market_p},{t:"+24h",...},{t:"close",...}]`.
- `recalibrate`: on **pulse** + overnight-watch + daily-close, snapshot the CLOB midpoint for open forecasts due a snapshot and compute `clv = (market_p_later − market_p_t0) · sign(your_p − market_p_t0)`. Aggregate `clv_mean`, `clv_hit_rate` per intent and per `edge_source` into the scorecard. Seeds from the existing `drift_skill` field.
- `strategy/current.md`: CLV is the **headline** skill metric while `resolved_n < 30`; Brier shown "pending ground truth."
- **Fix the ledger bug:** `tick()` MUST append every `forecast` to `forecasts.open.jsonl`; `sweep()` self-check flags divergence vs trade-log `forecast` count.

**Verify:** AC #7/#8/#16 — after a forecast ages 6h, `scorecard.*.clv_mean` is non-null; recap shows CLV headline; ledger count matches trade-log; pulse cycles do CLV work, not bare pings; a UTC day shows ≤15 `cycle_start`.

---

## Phase 4 — Historical bootstrap + backtest *(deepen)*

**Owner:** builder (offline, supervised). **Implements ADR 0019 (bootstrap half). Resolves PRD decision #2.**

**Files:** `pm/` backtest report (or `research/`), `state/calibration.json` (seeded prior), `tools/backtest.py` *(offline, off the runtime path — approved exception to markdown-only)*.

**Change:**
- Pull ≥500 resolved markets (Gamma/Data API); compute market-baseline Brier, a price→frequency calibration table, and a first pass at mechanical-signal edges (favorite-longshot bias, CLV/momentum persistence) with an **in/out-of-sample split**.
- **Efficiency angle (decision #2):** the report also estimates **which cycles and `edge_source` buckets actually generate CLV/edge**, so we can decide whether 10/day is optimal — or could be *reduced* to save cost without hurting learning.
- Seed `state/calibration.json` market-prior rows flagged `source:"historical_bootstrap"` (a baseline to beat + a calibration map — not a fabricated track record).

**Verify:** AC #9 — report exists with ≥500 markets + in/out-of-sample split; calibration prior seeded + flagged; report names ≥1 signal that did/didn't beat market and a recommendation on cycle count.

---

## Phase 5 — Risk doctrine that fires *(deepen)*

**Owner:** builder (pack) + **supervisor** (guardrail numbers). **Implements ADR 0020. Resolves PRD decision #4.**

**Files:** `config/guardrails.md` *(supervisor)*, `skills/risk/SKILL.md`, `skills/circuit-breaker/SKILL.md`, `skills/sizing/SKILL.md` (tiers + risk_reduction), `strategy/current.md`, `routines/overnight-watch.md`, `routines/daily-close.md`, pulse.

**Change (the §Risk-philosophy rewrite):**
- *(Supervisor)* `config/guardrails.md`: replace the flat 5% cap as the *primary* rule with the **sizing ladder** (Tier 0 default → Tier 3 ≤10% earned); add **portfolio heat** ≤25% across ≤4 uncorrelated buckets (Tier 3 needs heat <10%); add **drawdown-from-peak** governors (−8% → ×0.5 probation; −15% → forecast-only freeze); keep **−10%/24h** as the catastrophic halt; add **disconfirmation stop** (−25% from entry or named event).
- `risk`: compute `portfolio_heat`, `peak_nav`, `drawdown_from_peak`, per-position `pnl_from_entry`.
- `circuit-breaker.evaluate()`: add heat-breach + drawdown-from-peak triggers so losses are catchable under the per-token cap.
- `sizing`: assign `sizing_tier` from the ladder preconditions; `size_mult = f(clv_mean, brier_skill)` in the `edge_source` bucket (unproven bucket ⇒ ≤ Tier 1); add the `risk_reduction` SELL path (Phase 0's manual exit, generalized).
- Exit + governor checks run in overnight-watch, daily-close, and every pulse.

**Verify:** AC #10/#11/#12/#17 — held position at −25% → `risk_reduction` SELL; Σ-heat > cap → new exploit rejected; −8%/−15%/−10%-24h simulations trip probation/freeze/halt; every `decision` carries `sizing_tier` + cleared preconditions.

---

## Phase 6 — Cost-model + liveness rebalance *(cleanup)*

**Owner:** builder (pack) + **supervisor** (cron). **Implements ADR 0021 + 0022.**

**Files:** `AGENTS.md`, `routines/heartbeat.md` (→ pulse), `README.md`, `skills/recalibrate` (pulse hook).

**Change:**
- `AGENTS.md`: replace the leading "Token economy (read first)" with the **resource-priority order** (capital > correctness > calibration data > human attention > paid invocations > context tokens) and name the **scheduled invocation** as the metered unit. Keep progressive-disclosure loading; explicitly permit loading what a capital decision needs (e.g., the resolution `description`).
- Rename heartbeat → **pulse**; it now does CLV snapshot + cheap mark + disconfirmation check + liveness (Phase 3/5 wired it). *(Supervisor)* fix README cron to `0 */4` to match AGENTS.md (6/day).
- `README.md`: update schedule table + rationale; note the scheduler-reliability risk and that liveness must not depend solely on one scheduled pulse; state the ≤15/day budget and the ~10/day target.

**Verify:** AC #14/#16 — `AGENTS.md` opens with the priority order; pulse earns its tokens; README cron matches AGENTS.md; boot gap-check still detects a dark scheduler; a UTC day shows ≤15 `cycle_start`.

---

## Phase 7 — Self-direction: envision / enact *(implemented 2026-05-29; paper)*

**Owner:** builder (pack) + **human** (the `config/autonomy.md` charter + the landing commit — the
protected core must be human-authored, or the next `boot` integrity audit halts). **Implements ADR 0023.**

**Files:** `skills/envision/SKILL.md`, `skills/enact/SKILL.md` (new); `config/autonomy.md` (new,
human-owned, protected core); `proposals/{README,VISION,LEDGER,horizon.jsonl}` (new); edits to
`routines/daily-close.md` (envision daily + enact Sundays), `skills/boot` (integrity audit),
`skills/persist` (write gate), `skills/circuit-breaker` (`protected_core_violation`), `skills/journal`
(`vision`/`proposal`/`enactment` events), `skills/notify` (+3 templates), `skills/commit`
(envision/enact/auto-rollback subjects), `AGENTS.md` (§Self-direction).

**Change:** daily `envision` authors capability proposals (rotating lens, novelty gate, mandatory
self-critique — steelman + cheapest falsifying experiment); the Sunday deep pass revises `VISION.md`,
curates `LEDGER.md`, self-approves ≤1; Sunday `enact` self-implements ≤1 reversible / paper /
denylist-clean proposal as a standalone revertible commit, then arms auto-rollback. Bounded by
`config/autonomy.md`, enforced by three identity-keyed gates (intent / write / integrity audit). Rides
`daily-close`; **zero new cron.**

**Verify:** daily `vision` event + idempotency; Sunday deep + `vision_weekly`; a denylist-naming
proposal is refused (`awaiting_human`, no code); an agent-identity protected-file commit halts the next
boot (`protected_core_violation`); ≤1 enactment/ISO week, single-`git revert` undo; auto-rollback on
regression; `jq empty` clean; ≤15 `cycle_start`/day.

## Phase 8 — Repo hygiene: groom *(implemented 2026-05-29)*

**Owner:** builder. **Implements ADR 0024.**

**Files:** `skills/groom/SKILL.md` (new); edits to `routines/daily-close.md` (Sunday step),
`skills/journal` (`groom` event + the sole-rotator exception to append-only), `skills/recap` (weekly
ingests findings), `AGENTS.md` (+`state/archive/` in repo layout).

**Change:** weekly (Sunday) self-maintenance — rotate `state/trade-log.jsonl` +
`state/forecasts.resolved.jsonl` into `state/archive/` (30d / 90d; cutoff `min(now−30d, oldest
open-forecast emitted_at)` never strands an open forecast; atomic / no-drop / idempotent) + lint the
auto-loaded set (token budgets + referential integrity). The **sole** trade-log rotator. Findings ride
the weekly recap. **Weekly, not daily** — the per-cycle invocation is the metered cost, so fighting
~35 log lines/day with 7 runs would be self-defeating.

**Verify:** a Sunday `daily-close` emits a `groom` event; `archived + kept == original` (no-drop); no
open-forecast line archived; `jq -c` valid on rotated logs; lint findings appear in `recaps/YYYY-Www.md`.

## Cutover & rollout

1. Land Phases 0–1 (safety) — supervisor confirms the Iran exit + `portfolio.json` reset + the `guardrails.md` cost-language edit.
2. Cut strategy v2 → v3 at Phase 2 start (snapshot + version bump, same commit, ADR 0007).
3. Land Phases 2–3; run a **paper-only window (2–4 weeks)** at ~10 invocations/day collecting CLV.
4. Land Phase 4 bootstrap (offline) when convenient; it informs Phase 5 sizing and the cycle-count decision.
5. Land Phase 5 only after the supervisor accepts the `guardrails.md` diff.
6. Phase 6 any time after Phase 3 (cron edit is supervisor-owned).
7. Compare v2 vs v3 on CLV (and later Brier-skill) before any mainnet conversation — which stays a separate, human-driven decision.

## Verification summary (maps to PRD acceptance criteria)

| AC | Phase | Check |
| --- | --- | --- |
| 1, 2 | 1 | paper fill at ask/bid; NAV marks at bid; fees > 0 |
| 3, 4, 5, 6 | 2 | Iran replay → forecast-only (provenance reasons); net-edge floor; resolution + reference-class mandatory |
| 7, 8 | 3 | CLV non-null after 6h; CLV headline; ledger count matches |
| 9 | 4 | backtest ≥500 markets + in/out-of-sample; prior seeded + flagged; cycle-count recommendation |
| 10, 11, 12, 17 | 5 | exit fires; heat cap + tiers enforced; governors trip; `sizing_tier` on every decision |
| 13 | 0 | NAV reconciliation halt; no scaling; Iran exit logged |
| 14, 16 | 6, 3 | priority-order AGENTS.md; pulse earns tokens; ≤15 cycle_start/day; README cron fixed |
| 15 | all | `jq empty` clean; idempotency/lock intact; `HEAD == origin/main` |
| ADR 0023 | 7 | daily `vision`+idempotency; denylist refusal; protected-core boot halt; ≤1 enact/wk; auto-rollback |
| ADR 0024 | 8 | `groom` event; `archived+kept==original` no-drop; no open-forecast archived; findings in weekly recap |

## Risks & mitigations

- **CLV is a proxy, not P&L.** Positive CLV with negative net P&L is possible if we keep paying the spread. *Mitigation:* the net-edge gate (Phase 2) + liquidation marks (Phase 1) keep P&L honest; CLV is for *speed of learning*, the gate + tiers decide *whether to bet*.
- **Backtest overfitting.** A signal that "beat market" historically may be noise. *Mitigation:* in/out-of-sample split; any signal is a *hypothesis* that must re-prove itself via live CLV before it sizes anything above Tier 1.
- **Guardrail edits are human-gated** and may stall Phase 5. *Mitigation:* Phases 0–3 deliver most of the safety/learning value without any `guardrails.md` change; Phase 5 can wait on the supervisor.
- **Scheduler reliability is out of repo.** v3 can detect dark cycles but can't self-start. *Mitigation:* boot gap-check + daily-close audit surface it loudly; flagged as an operational item for the supervisor.
- **Invocation budget creep.** New ideas tend to want new cycles. *Mitigation:* the budget table is the contract — additions must displace, not add, or clear the supervisor with backtest justification, and never exceed 15/day.
