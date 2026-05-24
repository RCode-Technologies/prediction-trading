---
version: v1
created: 2026-05-24
owner: agent
---

# Strategy v1 — Learning Baseline (Observation)

Agent-owned. Edited only by `skills/reflect`. Snapshotted to `strategy/history/` on every edit.

## Decision rules

- **Phase:** Observation (`mode.observation_only=true` for first 48h). Log `forecast` only; no fills.
- **Min edge:** 300 bps (`|your_p - market_p| >= 0.03`).
- **Sizing:** fractional Kelly, `f = 0.25`, cap 5% NAV per token.
- **Market filter:** Gamma `liquidityNum >= 5000`, `endDate <= 30d`, both bid+ask, midpoint <=15min old.
- **Research style:** Polymarket Gamma + 1 search provider/cycle; 3rd source only if it changes view.
- **Per-cycle (observation):** 1 research_note, 1 candidate_rank (top 5), N forecasts on top market.

## Probability + sizing

- `market_p = fresh midpoint` (also crowd prior).
- Research → `raw_your_p`. Sizing applies calibration from this file → `your_p`.
- <10 resolved/bucket: no calibration offset; record `calibration_applied:false`; rely on edge floor.
- `kelly_fraction = (your_p - market_p) / (1 - market_p)`.
- `notional = clamp(0.25 * kelly_fraction * NAV, 0, 0.05 * NAV)`.
- Kelly ≤ 0 → forecast-only.

## Forecast attribution (required fields)

`strategy_version`, `forecast_id`, `thesis_id`, `evidence_refs`, `feature_tags`, `source_providers`, `prior_p`, `raw_your_p`, `your_p`, `market_p`, `confidence`, `calibration_bucket`, `close_time`, `resolution_criteria`, `disconfirming_signals`.

## Calibration ledger

| bucket | resolved_n | brier | hit_rate | adjustment | status  |
| ------ | ---------: | ----: | -------: | ---------: | ------- |
| 50-60  |          0 |   tbd |      tbd |       0.00 | collect |
| 60-70  |          0 |   tbd |      tbd |       0.00 | collect |
| 70-80  |          0 |   tbd |      tbd |       0.00 | collect |
| 80-90  |          0 |   tbd |      tbd |       0.00 | collect |

## Hypothesis registry

Statuses: `watch` (full sizing), `probation` (sizing_mult 0.5), `demoted` (excluded until `next_retry_date`), `retired`.

| thesis/tag                  | status  | evidence_n | sizing_mult | next_retry_date | note                                                |
| --------------------------- | ------- | ---------: | ----------: | --------------- | --------------------------------------------------- |
| base-rate-anchored-research | watch   |          0 |        1.00 | n/a             | Name a base rate before news adjustments.           |
| closing-line-value          | watch   |          0 |        1.00 | n/a             | Midpoint drift = interim signal, not truth.         |
| thin-book-drift             | caution |          0 |        1.00 | n/a             | Need fresh two-sided quotes; drop thin-book moves.  |
| correlated-news-markets     | caution |          0 |        1.00 | n/a             | Same fact = same bucket; uncertain = reject.        |

## Source-quality ledger

Rolling 30d Brier vs market baseline per `source_providers` value.

| provider | resolved_n | brier_provider | brier_market_p | penalty | status |
| -------- | ---------: | -------------: | -------------: | ------: | ------ |
| (collect)                                                                       |

## Pending evidence

- Accumulate forecast records with thesis IDs + feature tags for attribution.
- Compare observation forecasts vs later midpoint drift before letting fills shape rules.
- Track external-source theses vs Polymarket-only theses (net of source budget cost).

## Smartness scorecard (rolling 30d)

| metric | formula | direction |
| --- | --- | --- |
| `brier_agent`           | mean `(your_p - outcome)^2`                                  | lower better          |
| `brier_market_p`        | mean `(market_p - outcome)^2` (same forecasts)               | baseline              |
| `brier_skill`           | `brier_market_p - brier_agent`                               | positive = smarter    |
| `calibration_slope`     | OLS slope of `outcome ~ your_p`                              | target ≈ 1.0          |
| `calibration_intercept` | OLS intercept                                                | target ≈ 0.0          |
| `auc`                   | rank-AUC of `your_p` vs outcome                              | higher better         |
| `kl_vs_market`          | mean `KL(your_p ‖ market_p)`                                 | informative only      |
| `drift_skill`           | fraction of unresolved fcsts whose midpoint moved toward `your_p` more than toward forecast-time `market_p` | positive = smarter |
| `rejected_drift`        | mean midpoint drift on edge-floor rejects                    | calibrates edge floor |

Only score outcomes ∈ {0,1}. Per-source and per-tag slices fed to ledgers above.

## Convergent calibration update law

Per bucket with `resolved_n >= 10`:

```
shrink     = min(1.0, resolved_n / 30)
adjustment = clamp(shrink * (hit_rate - bucket_midpoint), -0.08, +0.08)
your_p     = clamp(raw_your_p + bucket_adjustment, 0.02, 0.98)
```

Below `resolved_n=10`: `adjustment=0`, `status=collect`. Deterministic — any change to the formula is itself a strategy edit subject to the gate.

## Reflection-quality gate

Before writing v(N+1):

1. `brier_skill_before` on trailing 14d under current strategy.
2. Re-score same window with proposed v(N+1) calibration + feature-tag + source penalties → `brier_skill_after`.
3. If `brier_skill_after < brier_skill_before - 0.005`: refuse. Emit `reflection` `edited:false`, `reason:"regression_blocked"`, append proposal to **Pending evidence** (no version bump, no snapshot).
4. **Risk-tightening edits** (severe miss, correlation surprise, stale-mark failure, source-quality failure) bypass the gate.

## Auto-revert

`last_good_version` = highest historical version whose 30d `brier_skill > max_brier_skill - 0.01`. If last 3 `reflection` events all have `brier_skill < last_good_version.brier_skill`: next reflection **must** revert (copy snapshot to `current.md`, bump version, snapshot the failed run, emit `reflection` `edited:true`, `reason:"auto_revert"`, `reverted_to:"<vN>"`).

## Exploration policy

Demote sets `next_retry_date = today + 14d`. On/after that: → `status:probation`, `sizing_mult:0.5`, clear `next_retry_date`. After 5 probation resolutions: if `brier_skill > 0` → `status:watch`, `sizing_mult:1.0`; else re-demote with `next_retry_date = today + 14d`.

## Source-quality penalty

If `brier_provider > brier_market_p + 0.03` over `resolved_n >= 8`: `penalty:0.5`, `status:penalized` (forecasts citing source get `confidence *= 0.5` in sizing). Lifts after 5 resolved cite-events restore `brier_provider <= brier_market_p`.

## Smartness threshold (human hint)

OLS slope of daily `brier_skill` over 30d. Negative for 14 consecutive UTC dates → reflection calls `risk.surface_recommendation()` with candidate tightenings (narrower filter, higher edge floor, smaller `strategy_frac`). Reflection does NOT apply them — humans own guardrails.

## Reflection notes

(Updated by `skills/reflect`. v1 starts empty.)

## Changelog

- v1 — 2026-05-24 — self-learning contract, attribution fields, calibration/hypothesis/source ledgers, smartness gates (convergent calibration, reflection gate, auto-revert, exploration, source penalty). Snapshot at `strategy/history/2026-05-24-v0.md`.
- v0 — 2026-05-24 — observation-only seed.
