---
version: v2
created: 2026-05-24
last_edited: 2026-05-26
owner: agent
---

# Strategy v2 — Self-Bootstrapping Action-Biased Learner

Agent-owned. Edited only by `skills/reflect`. Snapshotted to `strategy/history/` on every edit.

v2 closes the cold-start deadlock: mandatory exploration probes (≥3 forecasts/cycle) populate calibration buckets empirically instead of waiting on a thesis match.

## Decision rules

- **Phase:** Observation auto-flips off in `skills/boot` at `observation_started_at + observation_hours`. Post-obs:
  - `exploit` — thesis-driven, sized by Kelly, gated by min-edge.
  - `explore` — mandatory ε-probes, forecast-only (no fill).
  - `risk_reduction` — reserved; v2 has no auto-SELL.
- **Min edge (exploit fills):** 300 bps.
- **Sizing:** fractional Kelly `f=0.25`, cap 5% NAV/token. Probes pinned to 0 notional / 0 shares.
- **Action commitment** (enforced by `skills/persist` audit; canonical in AGENTS.md):
  - research_window: ≥1 research_note, ≥1 candidate_rank, ≥3 forecast.
  - trade_window: ≥3 forecast.
  - daily_close: ≥1 recap, ≥1 reflection.
  - overnight_watch: ≥1 nav_snapshot.
  - Floor miss → `null_cycle` (still pushed, flagged).
- **Market filter:** Gamma `liquidityNum >= 2000`, `endDate <= 90d`, two-sided book, midpoint ≤15min.
- **Discovery:** universe-first (`state/universe.jsonl` daily cache, then attach research signals).

## Probability + sizing

### Exploit path

`market_p` = fresh midpoint. Research → `raw_your_p`. Calibration adj → `your_p`.

Cold-start fallback (exploit bucket `resolved_n < 10`): if `raw_your_p == market_p`, nudge `your_p = clamp(market_p + sign(thesis_direction) * 0.01, 0.02, 0.98)`. **`your_p == market_p` on exploit path is forbidden** (dead-loop signal).

```
kelly_fraction   = (your_p - market_p) / (1 - market_p)
notional         = clamp(0.25 * kelly_fraction * NAV, 0, 0.05 * NAV)
```

Kelly ≤ 0 → forecast-only.

### Explore path

ε by candidate rank in cycle: `1→+0.05, 2→0.00, 3→-0.05`.

```
your_p   = clamp(market_p + ε, 0.02, 0.98)
notional = 0, shares = 0
thesis_id = "explore-rank<N>-eps<Pos|Zero|Neg>"
feature_tags = ["explore"]
```

Always emits `forecast`; never `paper_fill` / `mainnet_order_submitted`.

## Forecast attribution (mandatory fields)

`strategy_version`, `forecast_id`, `thesis_id`, `evidence_refs`, `feature_tags`, `source_providers`, `prior_p`, `raw_your_p`, `your_p`, `market_p`, `confidence`, `calibration_bucket`, `close_time`, `resolution_criteria`, `disconfirming_signals`, **`learning_intent ∈ {"explore","exploit","risk_reduction"}`**.

## Calibration ledger (sliced by `learning_intent`)

Exploit metrics drive sizing; explore metrics drive bucket population only.

### Exploit

| bucket | resolved_n | brier | hit_rate | adjustment | status  |
| ------ | ---------: | ----: | -------: | ---------: | ------- |
| 50-60  |          0 |   tbd |      tbd |       0.00 | collect |
| 60-70  |          0 |   tbd |      tbd |       0.00 | collect |
| 70-80  |          0 |   tbd |      tbd |       0.00 | collect |
| 80-90  |          0 |   tbd |      tbd |       0.00 | collect |

### Explore

| bucket | resolved_n | brier_explore | brier_market_p | calibration_slope | status  |
| ------ | ---------: | ------------: | -------------: | ----------------: | ------- |
| 30-40  |          0 |           tbd |            tbd |               tbd | collect |
| 40-50  |          0 |           tbd |            tbd |               tbd | collect |
| 50-60  |          0 |           tbd |            tbd |               tbd | collect |
| 60-70  |          0 |           tbd |            tbd |               tbd | collect |
| 70-80  |          0 |           tbd |            tbd |               tbd | collect |

## Hypothesis registry

Statuses: `watch` (full sizing), `probation` (mult 0.5), `demoted` (excluded until `next_retry_date`), `retired`.

| thesis/tag                  | status  | evidence_n | sizing_mult | next_retry_date | note                                              |
| --------------------------- | ------- | ---------: | ----------: | --------------- | ------------------------------------------------- |
| base-rate-anchored-research | watch   |          0 |        1.00 | n/a             | Name a base rate before news adjustments.         |
| closing-line-value          | watch   |          0 |        1.00 | n/a             | Midpoint drift = interim signal, not truth.       |
| thin-book-drift             | caution |          0 |        1.00 | n/a             | Need fresh two-sided quotes; drop thin-book.      |
| correlated-news-markets     | caution |          0 |        1.00 | n/a             | Same fact = same bucket; uncertain = reject.      |
| explore-rank1-epsPos        | watch   |          0 |        1.00 | n/a             | ε=+0.05 probe; calibration-only, no fill.         |
| explore-rank2-epsZero       | watch   |          0 |        1.00 | n/a             | ε=0 trust-market baseline.                        |
| explore-rank3-epsNeg        | watch   |          0 |        1.00 | n/a             | ε=−0.05 probe; calibration-only, no fill.         |

## Source-quality ledger

Rolling 30d Brier vs market baseline per provider (exploit slice only).

| provider | resolved_n | brier_provider | brier_market_p | penalty | status |
| -------- | ---------: | -------------: | -------------: | ------: | ------ |
| (collect)                                                                       |

## Pending evidence

- Target ~30 resolutions across explore buckets within 30 days of v2 deploy.
- Once any explore bucket hits `resolved_n >= 10`, flag if `|slope - 1.0| > 0.15` (market mispricing signal).
- Compare exploit forecasts (when they exist) vs explore baselines to validate thesis beats ε-noise.

## Smartness scorecard (read from `state/scorecard.json`)

`skills/recalibrate` keeps it fresh. Schema:
- `exploit.{brier_agent, brier_market_p, brier_skill, calibration_slope, calibration_intercept, auc, kl_vs_market, drift_skill, resolved_n, unresolved_n}`
- `explore.{brier_explore, brier_market_p, calibration_slope, buckets_filled, resolved_n, unresolved_n}`
- `by_provider[]`, `by_feature_tag[]`

## Convergent calibration update law

Per **exploit** bucket with `resolved_n >= 10`:
```
shrink     = min(1.0, resolved_n / 30)
adjustment = clamp(shrink * (hit_rate - bucket_midpoint), -0.08, +0.08)
your_p     = clamp(raw_your_p + bucket_adjustment, 0.02, 0.98)
```

Explore buckets compute `adjustment` diagnostically; never feed back into exploit sizing.

## Reflection-quality gate

Refuse v(N+1) if `exploit.brier_skill_after < brier_skill_before - 0.005` on trailing 14d. Risk-tightening edits bypass.

**v2 cold-start carve-out:** when trailing-30d `exploit.resolved_n < 5`, gate operates on `explore.calibration_slope` instead.

## Auto-revert

`last_good_version` = highest historical version whose 30d `exploit.brier_skill > max_brier_skill - 0.01`. If last 3 `reflection` events all have `brier_skill < last_good.brier_skill`, next reflection MUST revert: copy snapshot to `current.md`, bump version, snapshot failed run, emit `reflection edited:true reason:"auto_revert" reverted_to:"<vN>"`.

## Hypothesis retry policy

Demote → `next_retry_date = today + 14d`. On/after date → `probation, sizing_mult:0.5`, clear date. After 5 probation resolutions: `brier_skill > 0` → `watch, mult:1.0`; else re-demote `+14d`. Exploit theses only; explore probes never demote.

## Source-quality penalty

`brier_provider > brier_market_p + 0.03` over `resolved_n >= 8` (exploit) → `penalty:0.5, status:penalized` (sizing applies `confidence *= 0.5` to citing forecasts). Lifts after 5 resolved cite-events restore `brier_provider <= brier_market_p`.

## Exploration probe policy

Hard floor ≥3 `forecast`/cycle in `trade-window` and `research-window`. Slot allocation:

| exploit_eligible | exploit fills | explore probes |
| ----------------:| -------------:| --------------:|
| 0                | 0             | 3              |
| 1                | 1             | 2              |
| 2                | 2             | 1              |
| ≥3               | 3             | 0              |

Probes never duplicate a market that already has any forecast this cycle. Dedupe key for today's probes: `paper:<market_id>:<token_id>:explore:<UTC-date>`.

Once `Σ exploit resolved_n >= 30`, floor drops to ≥1 probe/cycle (still mandatory).

## Smartness threshold (human hint)

OLS slope of daily `brier_skill` over 30d negative for 14 consecutive UTC dates → `risk.surface_recommendation()` with candidate tightenings. Reflection surfaces; humans own guardrails.

## Reflection notes

(Updated by `skills/reflect`. v2 starts empty.)

## Changelog

- v2 — 2026-05-26 — cold-start deadlock fix: mandatory exploration, `learning_intent` taxonomy, sliced calibration ledger, action commitment per cycle, relaxed filter (liq≥2000, end≤90d), universe-first discovery. Snapshot: `strategy/history/2026-05-26-v1.md`.
- v1 — 2026-05-24 — self-learning contract, attribution fields, smartness gates. Snapshot: `strategy/history/2026-05-24-v0.md`.
- v0 — 2026-05-24 — observation-only seed.
