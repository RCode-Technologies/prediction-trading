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

| thesis/tag                  | status  | evidence_n | current action          | note                                                                            |
| --------------------------- | ------- | ---------: | ----------------------- | ------------------------------------------------------------------------------- |
| base-rate-anchored-research | watch   |          0 | collect                 | Prefer estimates that name a base rate before news adjustments.                 |
| closing-line-value          | watch   |          0 | collect                 | Use midpoint drift as interim signal, not final truth.                          |
| thin-book-drift             | caution |          0 | require liquidity check | Do not treat movement in thin books as evidence without fresh two-sided quotes. |
| correlated-news-markets     | caution |          0 | reject uncertain bucket | If two markets depend on the same underlying fact, share one risk bucket.       |

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

## Reflection notes

(Updated by `skills/reflect`. v1 starts with no evaluated evidence.)

## Changelog

- v1 - 2026-05-24 - Added explicit self-learning contract, required forecast
  attribution, calibration ledger, hypothesis registry, and anti-overfitting
  update gates. Snapshot saved at `strategy/history/2026-05-24-v0.md`.
- v0 - 2026-05-24 - Initial seed. Observation-only baseline; the agent owns
  growth of this file.
