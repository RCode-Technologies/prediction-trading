# PRD — v3: Edge, Honest Accounting, Fast Learning — + Self-Direction & Repo Hygiene

- **Status:** **Implemented 2026-05-29 (paper-mode).** All v3 phases landed: cost-honest accounting
  (P1), edge gate + forecast/trade split (P2), CLV fast-learning (P3), historical bootstrap (P4), risk
  doctrine (P5), cost-model rebalance (P6), capital integrity (P0) — alongside self-direction
  (`envision`/`enact`) + repo hygiene (`groom`). Validated in paper; **mainnet stays off** behind the
  separate human-attested promotion. Notable: the Iran position (`2354045`) auto-exited the moment P5
  went live — the new disconfirmation stop sold it at −51.7% from entry via the `risk_reduction` path,
  the exact failure v2 could see but not act on.
- **Date:** 2026-05-29
- **Owner:** Theo (supervisor; owns `config/guardrails.md` + `config/autonomy.md` + mode flips + the scheduled-invocation budget). Strategy + proposals content is agent-owned.
- **Drafted by:** Claude (Opus) design-review session, 2026-05-29.
- **Related:** extends [PRD v1-instruction-pack](v1-instruction-pack.md); proposes **strategy v3** (supersedes v2); amends ADR 0003 (paper fills), the v2 "no auto-SELL" rule, the flat-5%-cap framing, and `AGENTS.md` §"Token economy (read first)". ADRs: 0017–0022 proposed (listed below); **0023 (autonomy charter) + 0024 (weekly groom) created + implemented** as the first slices of v3.
- **Related plan:** [../plans/v3-edge-and-learning.md](../plans/v3-edge-and-learning.md)

---

## Background — why v3 exists

On 2026-05-27 the agent placed its first real post-observation position: **US x Iran diplomatic meeting by June 7** (market `2354045`), bought YES at avg **0.373**, sized to the **5% NAV cap**. It has bled steadily — mark **0.30** at 2026-05-28 close, **bid 0.23 / ask 0.25** live on 2026-05-29 — a **~-34% loss on the position** at current liquidation value (~-1.8% on the fund). The position is the entire book; everything else is cash.

The loss is not bad luck. It is the predictable output of process defects. This PRD treats that trade as the worked example for everything v3 must fix.

### What the Iran trade exposes

1. **No defensible edge.** `raw_your_p ≈ 0.45` was anchored on a base rate the agent invented ("≈0.45–0.55 for a bilateral meeting in 11 days") with no reference class. The "+7.5pp edge vs market 0.375" was a vibe dressed as a prior, on a liquid, heavily-covered headline market where a generalist has no informational advantage.
2. **It bet without reading the rules.** [research/2026-05-27/us-iran-meeting-by-jun7.md](../../research/2026-05-27/us-iran-meeting-by-jun7.md) says: *"Without the market description in hand the agent must assume conservatively-broad definition."* The resolution criteria were one field away in the same Gamma response the agent already consumes (`description`). It sized to the cap on a bet whose resolution rules it never parsed.
3. **Conviction ≠ size.** Confidence was logged "medium-low" (0.45); Kelly still pushed it to the hard 5% ceiling.
4. **One source.** `source_providers: ["agent_native_websearch"]` — a single web search, *under* the 3-source budget, not over it. Under-use, not over-use.
5. **Cost-blind accounting.** Paper filled at the **midpoint**. The live book is ~8% wide (0.23/0.25). You buy at the **ask**, sell at the **bid**. Filling paper at mid hides ~4% of entry cost and makes the strategy look better than it is — the exact signal we are trying to learn from is biased toward false confidence.
6. **No exit on disconfirmation — proven live.** The note listed disconfirming signals ("deal via intermediaries," "FM hardens"). They then *materialised*: the [2026-05-28 update](../../research/2026-05-28/macro-and-iran-update.md) records the Rome round failing, Iran hardening, kinetic escalation, and the market repricing 0.375 → 0.155. The agent revised its own estimate 0.45 → 0.18, **correctly declined to add** (edge below the 300 bps floor — the one control that worked) — and then **held the loser anyway**, because v2 has no exit path. It even rationalised holding as "tracking value." The mark kept falling (0.30 on 05-28, ~0.24 now). This is the clearest possible proof that v3 needs a disconfirmation exit: the system can *see* its thesis break and still cannot act on it.

### What the rest of the system exposes

7. **The learning loop is barely crawling.** As of 2026-05-28 the exploit slice is still `resolved_n: 0` (the Iran bet doesn't resolve until June 7), and the *first* explore probe just resolved (`outcome 0`) with `brier_explore 0.189 > brier_market_p 0.148` — the ε=+0.05 probe was already *worse* than simply trusting the market. n=1 is noise, but it hints that random ε-probing manufactures noise, not skill. With ~30 resolutions needed per bucket and resolution as the only feedback channel, useful signal is months away.
8. **Capital model integrity was broken.** The agent ran at **NAV $54** for three days ([recap 2026-05-26](../../recaps/2026-05-26.md)), then a `manual_baseline_reset` rewrote NAV to $10k and **scaled the Iran position 185.185×** to "preserve weight." The held shares are largely a back-scaled fiction. The breaker never noticed because it only watches *relative* 24h change.
9. **The breaker is decorative in the current regime.** With a 5%/token cap, a total wipe of one position is -5% NAV — the -10%/24h breaker can essentially never fire from position losses. It provides false comfort.
10. **The open-forecast ledger was silently broken** — the 05-27 trade-window had to "reconstruct forecasts.open.jsonl from trade-log (prior cycles had not populated it)."
11. **Operational fragility (claim corrected 2026-05-29).** An earlier read of this session claimed the scheduler had gone dark ~44h — that was an artifact of a **stale local clone**; `origin/main` shows 2026-05-28 ran a full cycle set (overnight-watch, research-window, an explore-only trade-window, heartbeats). The genuine risk remains: liveness depends on a single cloud scheduler plus a single scheduled heartbeat (one point of failure) with no external dead-man's-switch, and boot gap-detection only fires when a cycle *does* run.
12. **The cost model is measured in the wrong unit.** `AGENTS.md` line 7 — before anything about being *right* — leads with "Token economy (read first)… every line is paid every cycle," and the whole pack is contorted to shave *lines of auto-loaded context*. But the dominant metered cost is the **scheduled invocation** — each cron fire is a paid agent session. The system runs ~10/day (6 heartbeats + 4 routines), 6 of which spend a full paid session to write "I'm alive" and commit nothing useful. v2 counted pennies on context lines while burning whole sessions on liveness pings — and the terseness it bought *caused* failures like #2 (skip "read the resolution criteria").

### What is good and must be preserved

The plumbing is sound: append-only JSONL journal, idempotency keys, the explore/exploit split, per-forecast attribution discipline, repo-as-brain, direct-to-main simplicity, fail-closed mainnet gating, human-owned guardrails. The **300 bps min-edge floor also did its job** on 2026-05-28 — it blocked adding to the broken Iran thesis. And the system *does* re-test theses and reason about disconfirming evidence in research. v3 keeps all of it. **The problem is not the plumbing — it is a strategy with no edge feeding a learning loop that can't see the truth, that can forecast but cannot exit, on a schedule that pays for liveness instead of learning.**

---

## Operating constraint — scheduled-invocation budget (hard)

The supervisor's plan includes **15 scheduled agent invocations per day**; going over costs extra. **The cycle is the metered unit, not the line of context.** Current usage is **10/day** (4 routines + 6 heartbeats every 4h).

**v3 must stay ≤15/day and should stay at ~10/day by *repurposing*, not adding, cycles.** The 6 heartbeats are currently dead weight; v3 turns them into useful "pulse" cycles (CLV snapshots + exit checks + liveness) at **zero additional invocation cost**. The 5-cycle slack (10→15) is reserved and spent only on a **data-justified** improvement; the budget is never exceeded without explicit supervisor cost-approval. See the invocation-budget table in the [plan](../plans/v3-edge-and-learning.md).

---

## Goals

Mapped to the supervisor's four asks — *faster, better, more precise, profitable* — plus the cost constraint.

1. **Honest, cost-aware accounting** *(precise, profitable).* Paper fills execute at the **executable price** (ask for BUY, bid for SELL), fees modeled, open positions marked at **liquidation value** (mark-to-bid for longs). The only edge that counts is edge **net of spread + fees**.
2. **A defensible edge gate** *(better, precise).* A capital-risking (**exploit**) forecast is allowed only if it has: (a) the parsed resolution `description`, (b) a **named reference class / base rate** with ≥2 independent sources, (c) **net-of-cost edge ≥ threshold**, (d) a **calibrated** probability. Anything failing the gate is **explore** (forecast-only, no capital).
3. **Forecast-many, bet-few** *(faster, better).* Decouple **learning** (forecast broadly, score continuously, pay nothing) from **earning** (act rarely, only when the gate passes). Learning rate is no longer bounded by trading rate — and crucially, broad forecasting happens *inside the two content cycles we already pay for*, so it costs no extra invocations.
4. **A fast learning signal** *(faster).* Promote **closing-line value (CLV)** — does the market move toward our forecast after we make it? — to the **primary in-flight skill metric**, with resolution Brier as the slow ground truth. Reuse the already-defined `drift_skill` field as the seed. CLV snapshots ride the repurposed pulse cycles.
5. **Bootstrap from history, don't cold-start** *(faster, precise).* Build a market-calibration prior and a mechanical-signal backtest from Polymarket's thousands of **already-resolved** markets, so day-1 we have a realistic baseline Brier to beat, a price→frequency calibration map, and evidence about which signals beat the market historically. (Bootstraps the *baseline and edge hypotheses* — not a fake track record of our own.)
6. **Risk management that can actually fire** *(profitable).* A conviction-tiered, skill-scaled **sizing ladder** (not a flat cap); **equity governors** (drawdown-from-peak) that replace the toothless single breaker; **portfolio heat**; and **disconfirmation / stop exits** (a `risk_reduction` SELL path). See §Risk philosophy.
7. **Capital integrity** *(precise).* Never again rewrite NAV by scaling positions. Boot reconciles `NAV == cash + Σ(shares × mark)` with an **absolute** sanity check; unexplained deltas halt. One clean, documented reset.
8. **Reprioritize the cost model** *(the explicit ask).* In `AGENTS.md`, replace "token economy (read first)" with the resource-priority order **capital > correctness > calibration data > human attention > paid invocations > LLM context tokens**, and name the **scheduled invocation** as the metered unit. Recover cost by cutting low-value cycles, never by under-contextualizing a capital decision.
9. **Live within the invocation budget** *(the explicit ask).* Operate at ~10 invocations/day, ≤15 hard. Repurpose heartbeats into useful pulses. Treat the slack as justified-only.

---

## Folded into v3 — Self-direction + Repo hygiene (implemented 2026-05-29)

Two capabilities were built ahead of the edge/accounting/learning package and now belong to the v3
epoch. Both are **paper-mode**, ride the existing `daily-close` cycle (**zero new cron** — the ≤15/day
budget below is intact), and are recorded as ADRs **0023–0024**. They replace what was briefly drafted
as a standalone "v0.4" — there is no separate v0.4 version; this is v3.

### Self-direction (envision / enact) — ADR 0023

Closes the last manual bottleneck: **the supervisor no longer has to ask for a version bump.** `reflect`
evolves `strategy/current.md` *within* current capabilities; **`skills/envision`** (daily, agent-owned)
reflects on the whole system and **authors capability proposals** into `proposals/` — new skills, new
metrics, AGENTS.md/guardrail *recommendations*, market-structure pivots, moonshots, the mission itself.
A rotating daily lens + a MAX-reasoning Sunday deep pass keep it generative; every proposal carries
evidence, a steelman of why it's wrong, and the cheapest falsifying experiment. On Sundays
**`skills/enact`** (≤1/week, protected core) self-implements one `self_approved`, non-vetoed,
denylist-clean, reversible, paper-only proposal as a single revertible commit, then arms auto-rollback.

The keystone is **a constitution the agent cannot amend** (`config/autonomy.md`, human-owned): identity
is the trust boundary (agent commits as `Polymarket Trading Agent`, humans as themselves), and a
**protected core** — `config/{autonomy,guardrails}.md`, `AGENTS.md`,
`skills/{boot,persist,circuit-breaker,enact,recalibrate,risk}` — is enforced three ways: `enact`'s
intent gate (won't *write* a denylist path), `persist`'s write gate (won't *commit* a protected path
under the agent identity), and `boot`'s integrity audit (halts `protected_core_violation` if one is
agent-authored). Nothing touching guardrails, capital/portfolio, the breaker, or mainnet may ever be
self-enacted — those proposals are `human_application`. Veto is by repo action (`git revert` /
`LEDGER.md` status) with a standing ≥7-day window. Workspace: `proposals/{VISION.md, LEDGER.md,
<date>-<slug>.md, horizon.jsonl}`; journal events `vision` / `proposal` / `enactment` (governance — no
recalibrate hook). See [plan](../plans/v3-edge-and-learning.md) Phase 7.

### Repo hygiene (groom) — ADR 0024

**`skills/groom`** (weekly, Sundays, from `daily-close`) keeps the brain lean and AI-navigable. It is
the **sole** rotator of `state/trade-log.jsonl` + `state/forecasts.resolved.jsonl` (a documented
exception to append-only), moving aged lines into `state/archive/` (30d / 90d retention; the cutoff =
`min(now−30d, oldest open-forecast emitted_at)` never strands a line tied to an unresolved forecast, so
`recalibrate`'s trade-log recovery path is preserved — atomic, no-drop, idempotent). It also lints the
auto-loaded set against token budgets + referential integrity (dead skill/link refs, INDEX orphans,
schema drift, stale lock). **Weekly by design:** per-cycle tokens are the metered cost, so running
7×/week to fight ~35 log lines/day would be self-defeating; findings fold into the weekly recap under
*Recommendations for human review*. Report-only on core cognition files. See
[plan](../plans/v3-edge-and-learning.md) Phase 8.

## Non-goals (v3)

- **No plumbing rewrite.** `journal`, `persist`, `commit`, `boot` lock/idempotency, `notify` transport stay as-is except where a goal above requires a field.
- **No mainnet flip.** Stays `paper` until a separate, human-attested promotion. v3 is validated entirely in paper.
- **No application code / build step on the runtime path.** Still a markdown instruction pack. The one exception is a small **offline** backtest script (Phase 4), kept off the runtime path.
- **No maker / limit-order-provider strategy in paper.** Earning the spread is real but mainnet-only and microstructure-heavy; deferred to a later PRD.
- **No multi-wallet / multi-account.**
- **No new scheduled routines** unless a data-justified case clears the supervisor and stays ≤15/day.

---

## Ownership map (who may change what in v3)

| Surface | Owner | v3 changes go through |
| --- | --- | --- |
| `config/guardrails.md` (sizing ladder, governors, heat, exits) | **Human** | Supervisor edits after redline. Agent may only `risk.surface_recommendation()`. |
| Scheduled-invocation budget / cron | **Human** | Supervisor sets cron in Claude Code UI; v3 proposes the schedule. |
| `strategy/current.md` (edge-gate params, CLV thresholds, tier preconditions) | **Agent** | Seeded by builder at v3 cutover; thereafter evolved by `skills/reflect`. |
| `skills/*`, `routines/*`, `AGENTS.md` (the pack) | **Builder** | This PRD + plan; direct commits after approval. |
| `state/*` (portfolio reset, scorecard/calibration schema) | **Builder** (one-time) then **agent** | Phase 0 reset is a supervised one-time edit; thereafter machine-owned. |

---

## Risk philosophy — when to size up, when to stand down

Stated plainly, because the supervisor asked the wealth manager for an opinion, not a shrug: **the current guardrails are amateur hour, and they failed in exactly the way amateur guardrails fail.**

- **The flat 5%/token cap is the laziest risk model that exists.** It sized a fabricated geopolitical coin-flip *identically* to how it would size a proven, catalyst-backed, well-calibrated edge. It was simultaneously **far too aggressive** for the Iran vibe (correct size: zero) and **far too timid** for a real edge (you can never back the truck even when you should). A constant is not a risk model.
- **The −10%/24h breaker is security theater.** With a 5% position cap it is *mathematically incapable* of firing on position losses, and a 24-hour clock is the wrong instrument for a book of multi-week resolutions. It sat there while the Iran thesis broke in slow motion and would not have blinked.
- **There was no dry-powder discipline and no conviction ladder**, so the agent had exactly one gear: *max size on the loudest headline.* That is the risk profile of a degenerate gambler wearing a wealth-manager nametag. We invert it.

The doctrine for v3:

> **Default to capital preservation. Earn the right to be aggressive. Skill is the only license to size.**

Most markets are efficient and most days you have no edge — so most of the time the correct position is **zero**, and you do **not** pay the spread to express an opinion. You go aggressive — "degen," fine — only when *all* of these line up: a real, net-of-cost mispricing; a hard, near-term catalyst; demonstrated calibration in that exact bucket (positive CLV/Brier history); and a book that isn't already hot. When they don't line up, you forecast, you learn, and you keep the powder dry.

### Sizing ladder (size is earned, hard-capped)

| Tier | Name | Preconditions (all required) | Max size |
|---|---|---|---|
| 0 | **Observe** | default — no proven bucket skill, or `edge_net < floor`, or resolution unparsed | **0%** (forecast-only) |
| 1 | **Lean** | `edge_net ≥ floor` + resolution parsed + reference class (≥2 sources) + bucket CLV ≥ 0 | 0.5–2% NAV |
| 2 | **Conviction** | Tier 1 + *proven* bucket skill (CLV mean > 0 with n ≥ 20, or Brier-skill > 0) + hard near-term catalyst | ≤ 5% NAV |
| 3 | **Degen (earned)** | Tier 2 + exceptional edge (`edge_net ≥ 2× floor`) + high calibration confidence + uncorrelated + portfolio heat < 10% | ≤ 10% NAV (hard ceiling) |

### Equity governors (replace the toothless single breaker)

- **Drawdown-from-peak** is the primary control: −8% from peak NAV → all sizing × 0.5 (probation) + notify; −15% from peak → forecast-only freeze + human review to resume.
- **−10% / 24h** stays as the catastrophic hard halt.
- **Portfolio heat** ≤ 25% total liquidation-risk across ≤ 4 uncorrelated buckets; Tier 3 only reachable when current heat < 10%.
- **Per-position disconfirmation stop** (non-negotiable): −25% mark from entry **or** a named disconfirming event → reduce/close. The Iran position would have been stopped weeks before resolution.

All of these numbers live in `config/guardrails.md` (**human-owned**). The wealth manager proposes them with conviction; the supervisor signs off. Until a bucket earns skill, the whole book is capped at Tier 1 — meaning **early v3 will mostly not bet, and that is the point.**

---

## Acceptance criteria

1. **Cost-honest fills.** A paper BUY logs `fill_price == best_ask` (not midpoint); a paper SELL logs `fill_price == best_bid`; `fee_usdc` is computed, not 0.
2. **Liquidation marks.** `risk.nav()` marks long positions at `best_bid`; `portfolio.json` carries both `mark_mid` and `mark_liquidation`; NAV uses liquidation.
3. **Edge gate blocks the Iran pattern.** Replaying the 05-27 inputs through v3 `sizing` yields **forecast-only**, with a binding reason in `{resolution_unparsed, no_reference_class, insufficient_sources}`.
4. **Net-edge threshold.** `sizing` computes `edge_net = your_p − best_ask` (YES BUY) and refuses to fill unless `edge_net ≥ net_edge_floor` (proposed 300 bps **after** cost).
5. **Resolution criteria mandatory for exploit.** Every exploit `forecast` carries non-empty `resolution_criteria` from the Gamma `description` + `resolution_parsed: true`; missing → demoted to explore.
6. **Reference class mandatory for exploit.** Every exploit `forecast` carries `reference_class` and `source_providers` length ≥ 2; missing → explore.
7. **CLV pipeline live.** For each forecast, the scorecard reports `clv_mean` / `clv_hit_rate` from snapshots at t0, +6h, +24h, close; non-null once a forecast has aged ≥6h. Snapshots ride existing cycles (no new invocations).
8. **Scorecard promotes CLV.** Recaps + `strategy/current.md` show CLV as the headline skill metric while `resolved_n < 30`; Brier shown as "pending ground truth."
9. **Historical bootstrap exists.** A backtest artifact reports market-baseline Brier + a price→frequency calibration table from ≥500 resolved markets; `state/calibration.json` is seeded with the prior, flagged `source:"historical_bootstrap"`.
10. **Disconfirmation exit path.** A `risk_reduction` SELL fires (paper: reducing/closing `paper_fill`) on −25% mark-from-entry or a named disconfirming event. v2's "no auto-SELL" is replaced.
11. **Tiered, heat-aware sizing.** No fill exceeds its tier ceiling; default is Tier 0; an unproven-bucket candidate sizes ≤ Tier 1; new exploits are rejected above the portfolio-heat cap. (Guardrails edit — supervisor-owned.)
12. **Equity governors fire.** Simulated −8%/−15% drawdown-from-peak trigger probation/freeze; −10%/24h trips the hard halt; heat-breach rejects new risk. Unit-style checks trip each.
13. **Capital integrity invariant.** `boot` halts (`nav_reconciliation_failed`) on a >$0.01 NAV mismatch or an unexplained delta vs `starting_capital` history. No position is ever scaled to fit a baseline.
14. **Cost model reprioritized.** `AGENTS.md` opens with the resource-priority order and names the scheduled invocation as the metered unit; the heartbeat→pulse change is logged with rationale.
15. **No plumbing regression.** `jq empty` passes on all state; every `trade-log.jsonl` line validates; idempotency + lock behavior unchanged; `HEAD == origin/main` after a dry-run cycle.
16. **Invocation budget respected.** A representative UTC day shows **≤15** `cycle_start` events (target ~10); the 6 pulse cycles each do useful work (CLV snapshot and/or exit check), not a bare liveness ping; README cron matches AGENTS.md.
17. **Sizing is tier-gated end to end.** Every `decision` event carries its `sizing_tier ∈ {0,1,2,3}` and the preconditions it cleared; Tier ≥ 2 requires a logged proven-skill reference.

---

## Resolved decisions (supervisor, 2026-05-29)

1. **The live Iran position → exit now, take the loss.** Phase 0 sells the position at the live bid (≈0.23), realizes the loss (≈ −$193 against the recorded cost basis), and flattens the book before the reset. *Caveat:* the recorded cost basis is partly an artifact of the prior 185× scaling, so the precise loss figure inherits that distortion — Phase 0 documents this and the new integrity invariant prevents the class of distortion going forward. This exit doubles as the inaugural (manual) `risk_reduction` example; Phase 5 generalizes it.
2. **Backtest → approved.** A small **offline** Python script is permitted for the one-time historical pull (off the runtime path). Optimize it for *system efficiency and profitability*: beyond calibration, the backtest also reports **which cycles/edge-sources actually generate CLV**, informing whether 10/day is optimal or could even be reduced.
3. **Forecast floor → builder's call (decided): replace the rigid per-cycle floor with a daily, routine-aware target.** Drop "≥3 forecasts every cycle" (a v2 cold-start device that manufactured noise and bloated sessions). Instead: the two content cycles (research-window, trade-window) each emit a broad batch of **forecast-only** predictions (target ~8–12/day combined), of which only gate-passers (expected 0–2/day) become bets. Pulse cycles add **zero** new forecasts — they only snapshot. Rationale: maximizes learning per *paid invocation* without inflating invocation count or per-session token cost.
4. **Guardrail philosophy → see §Risk philosophy** (the wealth manager's opinionated rewrite). The flat 5% cap and the 24h-only breaker are replaced by the tiered ladder + equity governors + heat + disconfirmation stop. Numbers are proposed with conviction; supervisor owns final values in `config/guardrails.md`.
5. **Market selection → builder's rec (decided): stay category-neutral, but tag `edge_source` and let CLV-by-bucket demote weak categories automatically.** No hardcoded "avoid geopolitics" rule; the data earns or revokes each category's right to size (via Tier preconditions).

---

## Proposed ADRs (to be spun out on approval)

Kept as a list so the *decisions* are redline-able without prematurely creating Accepted-status files. On approval, each becomes `pm/adrs/00NN-*.md`.

- **0017 — Cost-honest paper accounting.** Fills at ask/bid, fees modeled, marks at liquidation value. *Amends ADR 0003.*
- **0018 — Forecast/trade separation + exploit edge gate.** Capital bets require parsed resolution + named reference class (≥2 sources) + net-of-cost edge ≥ floor + calibrated p; else explore-only.
- **0019 — CLV as primary fast-learning signal + historical bootstrap.** Promote CLV/`drift_skill`; seed calibration baseline + edge hypotheses from resolved-market history; resolution Brier remains slow ground truth.
- **0020 — Risk doctrine: tiered sizing ladder + equity governors + disconfirmation exits + portfolio heat.** Replaces the flat 5% cap as the *primary* sizing rule and the v2 "no auto-SELL." *Complements ADR 0014.* Guardrail values are human-owned.
- **0021 — Cost-model reprioritization.** Scarce resources reordered (capital > correctness > data > attention > paid invocations > context tokens); the metered unit is the scheduled invocation. *Amends `AGENTS.md` §"Token economy".*
- **0022 — Scheduled-invocation budget.** ≤15/day (≈10 default); repurpose heartbeats into useful pulses; slack spent only on data-justified improvements; never exceed 15 without explicit cost-approval.

**Created + implemented (folded into v3, 2026-05-29 — these are real Accepted files, not reservations):**

- **[0023 — Bounded agent self-direction, governed by a protected core it cannot amend](../adrs/0023-bounded-agent-self-direction.md).**
  `envision` authors proposals daily; `enact` self-implements ≤1/week (paper, reversible); a human-owned
  constitution (`config/autonomy.md`) + 3-gate enforcement keyed to commit identity bounds it. The agent
  is maximally free inside the envelope and structurally unable to widen it.
- **[0024 — Weekly groom for token-economy hygiene + log rotation](../adrs/0024-weekly-groom.md).** The
  sole `trade-log.jsonl` rotator (a documented exception to append-only); weekly Sunday cadence chosen
  because the per-cycle invocation is the metered cost; report-only on core cognition files.

---

## Remaining open items for review

- **Heat/exit/tier numbers** (PRD §Risk philosophy) are proposed defaults; confirm or override in `config/guardrails.md`.
- **Backtest depth** (how many markets, how far back, in/out-of-sample split) — builder will propose in the Phase 4 report; flag if you want a specific scope.
- **Iran exit accounting** — confirm you're fine realizing the loss against the (partly synthetic) recorded basis vs. a clean $10k reset that logs the trade as a closed learning example. Default: realize at bid.

---

## Success signal

After a 2–4 week paper window on strategy v3, run at ~10 invocations/day:
- The agent has produced **CLV-scored forecasts on ≥40 distinct markets**, with `clv_mean > 0` whose confidence interval excludes 0 in at least one `edge_source` bucket (first evidence of real skill), **or** a clear `clv_mean ≤ 0` verdict that says "we have no edge here yet — keep forecasting, don't bet."
- **Zero** capital-risking fills that fail the edge gate or exceed their tier; every fill shows `edge_net ≥ floor` priced at the ask, with a `sizing_tier`.
- The scorecard, recaps, and ≥1 `reflection` cite CLV as the live metric; no NAV-integrity halts; no position scaling; **≤15 invocations on every UTC day.**
- Paper P&L (honestly priced at bid/ask) is **flat-to-positive net of modeled costs**, or the agent has correctly throttled to forecast-only because the gate found nothing worth the spread.

Profitability is not promised. **An honest "we have no edge yet, so we are not betting" is a successful v3 outcome** — it is the exact opposite of the Iran trade.
