---
version: v1
created: 2026-05-24
owner: agent
---

# Current Strategy - v1 Learning Baseline (Observation)

This file is **owned by the agent**. The reflection step in
`routines/daily-close.md` invokes `skills/reflect`, which edits this strategy
based on observed outcomes and snapshots the prior version to
`strategy/history/` on every edit (ADR 0007). Humans do not write strategy
content; they only set risk limits in `config/guardrails.md` and the mode flag
in `config/mode.json`.

## Learning contract and caveats

Learning means future cycles use measured evidence from prior cycles. The
agent must keep every forecast attributable to a strategy version, thesis,
evidence file, feature tags, probability estimate, and resolution criterion.
Daily close scores those records; reflection updates this file when there is
new evidence.

This does not guarantee monotonic intelligence or profit. Polymarket outcomes
can resolve slowly, markets can be efficient, source quality can degrade, and
small samples can mislead. The agent must therefore separate final outcome
scores from interim price drift, keep weak signals in pending evidence, and
avoid loosening human-owned guardrails.

## Current decision rules

- **Phase:** Observation. `config/mode.json.observation_only == true` for the
  first 48 hours. Record `forecast` events only; no paper fills.
- **Minimum edge floor:** 300 bps (`|your_p - market_p| >= 0.03`). Reject
  candidates below this.
- **Sizing:** fractional Kelly with `f = 0.25`, capped at 5% of NAV per token
  bucket (per `config/guardrails.md`).
- **Market selection:** Gamma `liquidityNum >= 5000`, `endDate` within 30
  days, both bid and ask present, midpoint <=15 min old.
- **Research style:** prioritize Polymarket Gamma + one search provider per
  cycle. Use the third source only if it materially changes the view.
- **Per-cycle output during observation:** one `research_note`, one
  `candidate_rank` (top 5), one or more `forecast` events on the top market.

## Probability and sizing model

- Treat the fresh midpoint as `market_p` and crowd prior.
- Research produces `raw_your_p`; sizing applies any learned calibration
  adjustment from this file to produce `your_p`.
- Until at least 10 resolved forecasts exist, use no numeric calibration
  offset. Record `calibration_applied:false` and rely on the 300 bps edge
  floor to avoid false precision.
- Default Kelly formula:
  `kelly_fraction = (your_p - market_p) / (1 - market_p)`.
- Default notional:
  `clamp(0.25 * kelly_fraction * NAV, 0, 0.05 * NAV)`.
- Negative or zero Kelly means forecast-only / no BUY.

## Required forecast attribution

Every forecast event must include:

| field                                         | purpose                                                 |
| --------------------------------------------- | ------------------------------------------------------- |
| `strategy_version`                            | ties the forecast to this file                          |
| `forecast_id`                                 | stable join key for forecast, decision, fill, and recap |
| `thesis_id`                                   | testable claim from a research note                     |
| `evidence_refs`                               | markdown paths or market data references used           |
| `feature_tags`                                | market class, source type, and heuristic tags           |
| `source_providers`                            | providers used by the thesis                            |
| `prior_p`, `raw_your_p`, `your_p`, `market_p` | calibration inputs                                      |
| `confidence`, `calibration_bucket`            | score grouping                                          |
| `close_time`, `resolution_criteria`           | outcome scoring contract                                |
| `disconfirming_signals`                       | what would weaken the thesis                            |

## Learning state

### Calibration ledger

No resolved forecasts yet. Keep this table current once data exists.

| bucket | resolved_n | brier | hit_rate | adjustment | status  |
| ------ | ---------: | ----: | -------: | ---------: | ------- |
| 50-60  |          0 |   tbd |      tbd |       0.00 | collect |
| 60-70  |          0 |   tbd |      tbd |       0.00 | collect |
| 70-80  |          0 |   tbd |      tbd |       0.00 | collect |
| 80-90  |          0 |   tbd |      tbd |       0.00 | collect |

### Hypothesis registry

| thesis/tag                  | status  | evidence_n | sizing_mult | next_retry_date | current action          | note                                                                            |
| --------------------------- | ------- | ---------: | ----------: | --------------- | ----------------------- | ------------------------------------------------------------------------------- |
| base-rate-anchored-research | watch   |          0 |        1.00 | n/a             | collect                 | Prefer estimates that name a base rate before news adjustments.                 |
| closing-line-value          | watch   |          0 |        1.00 | n/a             | collect                 | Use midpoint drift as interim signal, not final truth.                          |
| thin-book-drift             | caution |          0 |        1.00 | n/a             | require liquidity check | Do not treat movement in thin books as evidence without fresh two-sided quotes. |
| correlated-news-markets     | caution |          0 |        1.00 | n/a             | reject uncertain bucket | If two markets depend on the same underlying fact, share one risk bucket.       |

Statuses: `watch` (default, full sizing), `probation` (re-test of a previously
demoted thesis at `sizing_mult: 0.5`), `demoted` (excluded from sizing until
`next_retry_date`), `retired` (permanently dropped).

### Source-quality ledger

Per `source_providers` value used by forecasts, track rolling 30d Brier vs
market baseline. Reflection appends a row the first time a provider is cited;
penalties below.

| provider | resolved_n | brier_provider | brier_market_p | penalty | status  |
| -------- | ---------: | -------------: | -------------: | ------: | ------- |
| (collect new rows as evidence arrives)                                          |

### Pending evidence

- Build enough forecast records with thesis IDs and feature tags to make
  attribution possible.
- Compare observation-window forecasts against later midpoint drift before
  allowing paper fills to influence sizing rules.
- Track whether external-source theses outperform Polymarket-only theses
  after source budget costs.

## Reflection update rules

- Daily close writes the learning scorecard in `recaps/YYYY-MM-DD.md`.
- Reflection edits this file when new evaluated evidence changes calibration,
  a hypothesis status, a market filter, sizing fraction, edge floor, or a
  pending-evidence note.
- A severe risk miss can tighten rules immediately. Other rule changes need
  either 5 resolved forecasts for the same thesis/tag, 8 consistent midpoint
  drifts over at least 2 UTC dates, or a weekly recap showing the lesson
  across independent markets.
- Reflection never edits `config/guardrails.md`; it may only recommend human
  review of guardrail changes.
- Every reflection edit must pass the smartness gate below. Reflection that
  fails the gate is recorded as `edited:false`, `reason:"regression_blocked"`,
  and the proposal goes to pending evidence instead.

## Smartness metrics and self-improvement gates

This block converts reflection from freeform LLM judgment into a measurable
self-improvement loop. The agent is "smarter" when measured signals — not
narrative — say so, and reflection is required to refuse edits that fail the
gate. Numbers are recomputed daily by `skills/recap` and consumed by
`skills/reflect`.

### Smartness scorecard (rolling 30d unless noted)

| metric                  | formula                                                       | direction              |
| ----------------------- | ------------------------------------------------------------- | ---------------------- |
| `brier_agent`           | mean `(your_p - outcome)^2` on resolved forecasts             | lower is better        |
| `brier_market_p`        | mean `(market_p - outcome)^2` on the same forecasts           | reference baseline     |
| `brier_skill`           | `brier_market_p - brier_agent`                                | positive means smarter |
| `calibration_slope`     | OLS slope of outcome ∈ {0,1} regressed on `your_p`            | target ≈ 1.0           |
| `calibration_intercept` | OLS intercept of the same regression                          | target ≈ 0.0           |
| `auc`                   | rank-AUC of `your_p` vs binary outcome                        | higher is better       |
| `kl_vs_market`          | mean `KL(your_p ‖ market_p)`                                  | informative only       |
| `drift_skill`           | fraction of unresolved forecasts whose midpoint moved toward  | positive means smarter |
|                         | `your_p` more than toward `market_p` at forecast time         |                        |
| `rejected_drift`        | mean midpoint drift on candidates rejected by the edge floor  | calibrates edge floor  |

Brier values are clamped against forecasts with `outcome ∈ {0,1}` only.
Per-source and per-`feature_tag` slices live in separate tables and feed the
source-quality ledger and hypothesis registry.

### Convergent calibration update law

When a calibration bucket has `resolved_n >= 10`:

```
adjustment       = shrink * (observed_hit_rate - bucket_midpoint)
shrink           = min(1.0, resolved_n / 30)
adjustment       = clamp(adjustment, -0.08, +0.08)
your_p           = clamp(raw_your_p + bucket_adjustment, 0.02, 0.98)
```

Below `resolved_n=10` per bucket, `adjustment = 0` and `status = collect`.
The law is deterministic: two runs over the same data must produce the
same numbers. Any change to this formula is itself a strategy edit subject
to the smartness gate.

### Reflection-quality gate

Before writing `strategy/current.md` with version `v(N+1)`:

1. Compute `brier_skill_before` on the trailing 14 days of resolved forecasts
   under the current strategy.
2. Re-score the same 14-day window using the proposed `v(N+1)` calibration
   adjustments and feature-tag penalties to produce `brier_skill_after`.
3. If `brier_skill_after < brier_skill_before - 0.005`, refuse the edit.
   Emit `reflection` with `edited:false`, `reason:"regression_blocked"`,
   append the proposal to **Pending evidence** with the simulated delta, and
   return.
4. Risk-tightening edits — severe risk miss, correlation surprise, stale-mark
   failure, source-quality failure — bypass this gate (they can knowingly
   reduce expected return).

### Auto-revert rule

Track `last_good_version` = the highest historical version whose 30d
`brier_skill` exceeded the running `max_brier_skill - 0.01`. If the last 3
reflection events all show `brier_skill` below `last_good_version`'s
`brier_skill`, the next reflection **must** revert: copy that snapshot from
`strategy/history/` back to `strategy/current.md`, bump the version, snapshot
the failed run, emit `reflection` with `edited:true`,
`reason:"auto_revert"`, `reverted_to:"<vN>"`. After a revert, normal edits
resume on the next cycle.

### Exploration policy for demoted theses

When reflection demotes a thesis it sets `next_retry_date = today + 14d`.
On or after that date, the next reflection promotes the thesis to
`status: probation`, `sizing_mult: 0.5`, and clears `next_retry_date`. After
5 probation forecasts resolve, reflection either:

- restores `status: watch`, `sizing_mult: 1.0` if probation `brier_skill > 0`,
- or re-demotes with `next_retry_date = today + 14d`.

This prevents permanent lock-in on early bad luck and keeps the search
space alive.

### Source-quality penalty

If a provider's rolling-30d `brier_provider > brier_market_p + 0.03` over
≥ 8 resolved cite-events, reflection sets `penalty: 0.5` (forecasts citing
that source get `confidence *= 0.5` in sizing) and `status: penalized`. The
penalty lifts when the next 5 resolved cite-events restore parity
(`brier_provider <= brier_market_p`).

### Smartness threshold (human-recommendation trigger)

Reflection runs a simple linear regression of daily `brier_skill` over the
trailing 30 UTC dates. If the slope is negative for 14 consecutive UTC
dates, reflection calls `risk.surface_recommendation()` with concrete
candidate tightenings — narrower market filter, higher edge floor, smaller
`strategy_frac` — for the next daily summary. Reflection does **not** apply
these itself; humans own guardrail changes.

## Reflection notes

(Updated by `skills/reflect`. v1 starts with no evaluated evidence.)

## Changelog

- v1 - 2026-05-24 - Added explicit self-learning contract, required forecast
  attribution, calibration ledger, hypothesis registry, smartness metrics +
  self-improvement gates (convergent calibration law, reflection-quality
  gate, auto-revert, exploration policy, source-quality ledger), and
  anti-overfitting update gates. Snapshot saved at
  `strategy/history/2026-05-24-v0.md`.
- v0 - 2026-05-24 - Initial seed. Observation-only baseline; the agent owns
  growth of this file.
