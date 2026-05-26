---
version: v2
created: 2026-05-24
last_edited: 2026-05-26
owner: agent
---

# Strategy v2 — Self-Bootstrapping Action-Biased Learner

Agent-owned. Edited only by `skills/reflect`. Snapshotted to `strategy/history/` on every edit.

v2 closes the cold-start deadlock that stalled v1: no resolved forecasts → no calibration → `your_p = market_p` → 0 edge → no forecasts. The fix is mandatory exploration probes: every `trade-window` cycle emits ≥3 `forecast` events regardless of thesis quality, so the calibration ledger fills empirically instead of waiting for a perfect news day.

## Decision rules

- **Phase:** Observation latches off automatically in `skills/boot` once `now >= observation_started_at + observation_hours`. Post-observation:
  - **Exploitation forecasts** (`learning_intent: "exploit"`) — thesis-driven, sized by Kelly, sized to fill, gated by min-edge.
  - **Exploration probes** (`learning_intent: "explore"`) — mandatory ε-probes, forecast-only (no fill), bypass min-edge.
  - **Risk-reduction** (`learning_intent: "risk_reduction"`) — SELL to close/reduce. v2 still no auto-SELL; reserved.
- **Min edge for exploit fills:** 300 bps (`|your_p - market_p| >= 0.03`).
- **Sizing:** fractional Kelly `f = 0.25`, cap 5% NAV per token. Exploration probes pinned to **0 notional, 0 shares** (forecast-only).
- **Action commitment per cycle (enforced by routine self-audit):**
  - `research-window`: ≥1 `research_note`, ≥1 `candidate_rank`, ≥3 `forecast` events (any intent).
  - `trade-window`: ≥3 `forecast` events.
  - `daily-close`: ≥1 `recap`, ≥1 `reflection`.
  - `overnight-watch`: ≥1 `nav_snapshot`.
  - A cycle that breaks its floor must append `null_cycle reason:"<why>"` and notify. **No-op cycles are failures, not defaults.**
- **Market filter (v2, relaxed from v1):** Gamma `liquidityNum >= 2000`, `endDate <= 90d`, both bid+ask, midpoint ≤15 min old. v1 had `>=5000` / `<=30d`, which excluded the long-dated political/macro markets where the most learnable edge actually lives.
- **Research style:** Universe-first. `markets.universe()` pulls the liquid set first; then `research` runs targeted lookups keyed off market questions. No more news-first runs that miss every market.

## Probability + sizing

### Exploit path (thesis matched)

- `market_p = fresh midpoint` (also crowd prior).
- Research → `raw_your_p`. Sizing applies calibration → `your_p`.
- Cold-start fallback (per exploit bucket `resolved_n < 10`): `your_p = clamp(market_p + sign(thesis_direction) * 0.01, 0.02, 0.98)`. **`your_p == market_p` is forbidden on the exploit path** — that's the dead-loop signal.
- `kelly_fraction = (your_p - market_p) / (1 - market_p)`.
- `notional = clamp(0.25 * kelly_fraction * NAV, 0, 0.05 * NAV)`.
- Kelly ≤ 0 → forecast-only.

### Explore path (no thesis, deterministic probe)

For a candidate with no usable thesis, sizing assigns `your_p` via **fixed ε-perturbation by candidate rank** so probes are deterministic and balanced:

| candidate rank in cycle | ε       | semantic                  |
| ----------------------- | ------- | ------------------------- |
| 1                       | +0.05   | favor YES                 |
| 2                       |  0.00   | match market (baseline)   |
| 3                       | -0.05   | favor NO                  |

```
your_p   = clamp(market_p + ε, 0.02, 0.98)
notional = 0
shares   = 0
thesis_id = "explore-rank<N>-eps<sign>"   # explore-rank1-epsPos, explore-rank2-epsZero, explore-rank3-epsNeg
feature_tags = ["explore"]
```

Rationale for ε=±5pp: large enough to be a statistically distinct prediction once 30+ resolutions land per bucket, small enough that mean-reverting markets don't trash calibration metrics. ε=0 anchors a "trust-the-market" baseline so we can score whether any agent overlay beats the market baseline (`brier_market_p`).

Exploration probes always emit `forecast`, never `paper_fill` or `mainnet_order_submitted`.

## Forecast attribution (required fields)

`strategy_version`, `forecast_id`, `thesis_id` (may be `"explore-rank<N>-eps<sign>"`), `evidence_refs`, `feature_tags`, `source_providers`, `prior_p`, `raw_your_p`, `your_p`, `market_p`, `confidence`, `calibration_bucket`, `close_time`, `resolution_criteria`, `disconfirming_signals`, **`learning_intent` (new in v2, mandatory: `"explore" | "exploit" | "risk_reduction"`)**.

## Calibration ledger

Sliced by `learning_intent`. Exploit metrics drive sizing; explore metrics drive bucket population only.

### Exploit calibration

| bucket | resolved_n | brier | hit_rate | adjustment | status  |
| ------ | ---------: | ----: | -------: | ---------: | ------- |
| 50-60  |          0 |   tbd |      tbd |       0.00 | collect |
| 60-70  |          0 |   tbd |      tbd |       0.00 | collect |
| 70-80  |          0 |   tbd |      tbd |       0.00 | collect |
| 80-90  |          0 |   tbd |      tbd |       0.00 | collect |

### Explore calibration (cold-start population)

| bucket | resolved_n | brier_explore | brier_market_p | calibration_slope | status   |
| ------ | ---------: | ------------: | -------------: | ----------------: | -------- |
| 30-40  |          0 |           tbd |            tbd |               tbd | collect  |
| 40-50  |          0 |           tbd |            tbd |               tbd | collect  |
| 50-60  |          0 |           tbd |            tbd |               tbd | collect  |
| 60-70  |          0 |           tbd |            tbd |               tbd | collect  |
| 70-80  |          0 |           tbd |            tbd |               tbd | collect  |

## Hypothesis registry

Statuses: `watch` (full sizing), `probation` (sizing_mult 0.5), `demoted` (excluded until `next_retry_date`), `retired`.

| thesis/tag                  | status  | evidence_n | sizing_mult | next_retry_date | note                                                |
| --------------------------- | ------- | ---------: | ----------: | --------------- | --------------------------------------------------- |
| base-rate-anchored-research | watch   |          0 |        1.00 | n/a             | Name a base rate before news adjustments.           |
| closing-line-value          | watch   |          0 |        1.00 | n/a             | Midpoint drift = interim signal, not truth.         |
| thin-book-drift             | caution |          0 |        1.00 | n/a             | Need fresh two-sided quotes; drop thin-book moves.  |
| correlated-news-markets     | caution |          0 |        1.00 | n/a             | Same fact = same bucket; uncertain = reject.        |
| explore-rank1-epsPos        | watch   |          0 |        1.00 | n/a             | ε=+0.05 probe; calibration-only, no fill.           |
| explore-rank2-epsZero       | watch   |          0 |        1.00 | n/a             | ε=0 trust-market baseline.                          |
| explore-rank3-epsNeg        | watch   |          0 |        1.00 | n/a             | ε=−0.05 probe; calibration-only, no fill.           |

## Source-quality ledger

Rolling 30d Brier vs market baseline per `source_providers` value. **Exploit-only** (explore probes don't cite sources).

| provider | resolved_n | brier_provider | brier_market_p | penalty | status |
| -------- | ---------: | -------------: | -------------: | ------: | ------ |
| (collect)                                                                       |

## Pending evidence

- Population target: 30+ resolutions across explore buckets within ~30 days from v2 deploy (3 probes/cycle × ~30 cycles × ~33% resolve-in-window rate).
- Once any explore bucket has `resolved_n >= 10`, recompute its calibration slope and flag if |slope - 1.0| > 0.15 — that's evidence the market's own midpoint is mispriced relative to outcomes.
- Compare exploit forecasts (when they appear) vs explore baselines to validate that thesis-driven `your_p` beats ε-noise around market.
- Track unresolved-drift on all forecasts via `skills/recalibrate` — it runs on every relevant JSONL append, not gated on resolution.

## Smartness scorecard (rolling 30d)

Computed by `skills/recap` AND incrementally by `skills/recalibrate`, consumed by `skills/reflect`. **Default slice is exploit-only**; explore metrics tracked in parallel.

- `brier_agent` (mean `(your_p - outcome)^2` over exploit forecasts), `brier_market_p` (same on `market_p`, baseline), `brier_skill = brier_market_p - brier_agent` (positive = smarter).
- `calibration_slope` / `calibration_intercept` — OLS of `outcome ~ your_p` on exploit forecasts.
- `auc` — rank-AUC of exploit `your_p` vs outcome.
- `kl_vs_market` — mean `KL(your_p ‖ market_p)`.
- `drift_skill` — fraction of unresolved exploit fcsts whose midpoint moved toward `your_p` more than toward forecast-time `market_p`.
- `rejected_drift` — mean midpoint drift on edge-floor rejects.
- **Explore slice (parallel):** `explore_brier`, `explore_calibration_slope`, `explore_buckets_filled` (count of buckets with `resolved_n >= 10`). Used by reflect to decide when exploit calibration adjustments are safe to apply.

## Convergent calibration update law

Per **exploit** bucket with `resolved_n >= 10`:
```
shrink     = min(1.0, resolved_n / 30)
adjustment = clamp(shrink * (hit_rate - bucket_midpoint), -0.08, +0.08)
your_p     = clamp(raw_your_p + bucket_adjustment, 0.02, 0.98)
```
`resolved_n < 10` → `adjustment=0`, `status=collect`. Changing this formula is itself a strategy edit (gate applies).

**Explore buckets** also compute `adjustment` for diagnostic purposes but DO NOT feed back into exploit sizing. Their role is calibration-slope estimation, not edge correction.

## Reflection-quality gate

Refuse v(N+1) if `brier_skill_after < brier_skill_before - 0.005` on trailing 14d **exploit** resolved (simulated under proposed calibration + feature-tag + source penalties). Risk-tightening edits bypass.

**v2 cold-start carve-out:** when trailing-30d exploit `resolved_n < 5` (system still bootstrapping via exploration), the gate becomes a **non-regression on `explore_calibration_slope`** — we don't have exploit data yet, but a slope drifting away from 1.0 is still a regression signal.

## Auto-revert

`last_good_version` = highest historical version whose 30d `brier_skill > max_brier_skill - 0.01`. If last 3 `reflection` events all have `brier_skill < last_good_version.brier_skill`, next reflection **must** revert: copy snapshot to `current.md`, bump version, snapshot failed run, emit `reflection edited:true reason:"auto_revert" reverted_to:"<vN>"`.

## Hypothesis retry policy (v1 carryover)

Demote → `next_retry_date = today + 14d`. On/after that → `status:probation`, `sizing_mult:0.5`, clear date. After 5 probation resolutions: `brier_skill > 0` → `status:watch`, `sizing_mult:1.0`; else re-demote `+14d`. Applies to exploit theses; explore probes never demote.

## Source-quality penalty

`brier_provider > brier_market_p + 0.03` over `resolved_n >= 8` (exploit slice) → `penalty:0.5`, `status:penalized` (sizing applies `confidence *= 0.5` to citing forecasts). Lifts after 5 resolved cite-events restore `brier_provider <= brier_market_p`.

## Exploration probe policy (operational)

The `explore` *path* (above) is the math. The *policy* is when probes fire:

- **Always**, in every `trade-window`. Hard floor: ≥3 `forecast` events/cycle.
- If 0 exploit candidates pass min-edge → 3 probes, top-3 watchlist by liquidity.
- If 1 exploit candidate passes → 1 exploit + 2 probes (from rank 2-3 of watchlist).
- If 2 exploit → 2 exploit + 1 probe.
- If ≥3 exploit → 3 exploit forecasts; probes skip this cycle.
- Probes never run on a market that already has an exploit forecast this cycle (no double-coverage).
- Probes never duplicate a forecast already emitted earlier today (idempotency_key check on `paper:<market_id>:<token_id>:explore:<date>`).
- Once `Σ exploit resolved_n >= 30` across the calibration ledger, the floor drops to ≥1 probe/cycle (still mandatory — exploration never goes to zero, just lighter tempo).

This is the inescapable learning loop: cycles cannot exit without emitting forecasts; forecasts populate buckets; buckets unlock calibration; calibration unlocks exploit fills.

## Smartness threshold (human hint)

OLS slope of daily `brier_skill` over 30d negative for 14 consecutive UTC dates → reflection calls `risk.surface_recommendation()` with candidate tightenings (narrower filter, higher edge floor, smaller `strategy_frac`). Reflection does NOT apply them — humans own guardrails.

## Reflection notes

(Updated by `skills/reflect`. v2 starts empty.)

## Changelog

- v2 — 2026-05-26 — closed cold-start deadlock. Mandatory exploration probes (≥3/cycle), `learning_intent` taxonomy, exploit/explore-sliced calibration ledger, action commitment per cycle, relaxed market filter (liq≥2000, end≤90d), universe-first markets discovery. Snapshot at `strategy/history/2026-05-26-v1.md`.
- v1 — 2026-05-24 — self-learning contract, attribution fields, calibration/hypothesis/source ledgers, smartness gates (convergent calibration, reflection gate, auto-revert, exploration, source penalty). Snapshot at `strategy/history/2026-05-24-v0.md`.
- v0 — 2026-05-24 — observation-only seed.
