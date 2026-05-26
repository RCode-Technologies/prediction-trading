---
name: reflect
description: Daily self-review. Scores forecasts, applies smartness gates, may edit strategy/current.md. Only file it may edit.
inputs: last 24h + trailing unresolved forecasts, strategy/current.md, recent recaps/
outputs: strategy/current.md (if edited) + history snapshot, reflection event
---

# Reflect

Runs once/UTC date from `daily-close`. Snapshot-then-edit. Learning is empirical, not monotonic.

## Hard rules

- **Only edits `strategy/current.md`.** Never guardrails, AGENTS, routines, skills.
- **Snapshot on every edit** to `strategy/history/YYYY-MM-DD-vN.md`.
- Record uncertainty; never overfit sparse data.

## Steps

1. **Idempotency.** Grep trade-log for `event_type=="reflection" date:<today UTC>` → if found, exit.

2. **Build dataset.** Today's events + unresolved forecasts from trailing 30d that now have resolution or fresh midpoint. Join by `forecast_id` (else `market_id`/`token_id`/`ts`). Keep: `strategy_version`, `thesis_id`, `feature_tags`, `source_providers`, `prior_p`, `raw_your_p`, `your_p`, `market_p`, `confidence`, `calibration_bucket`, `close_time`, decision/fill linkage.

3. **Score.** Resolved: Brier `(your_p - outcome)^2`, hit/miss, optional log loss (clamp away from 0/1). Unresolved: forecast vs current midpoint / closing line; flag drift (not truth). Fills: realized P&L if resolved, MTM if open.

4. **Attribute** by strategy version, thesis, feature tag, market class, `source_providers`. Both positive + negative evidence. Today's `recaps/<date>.md` has most of this — read first, recompute only gaps.

5. **Anti-overfitting gates.** Rule may tighten **immediately** on severe risk miss, correlation surprise, stale-mark failure, source quality failure. Otherwise need ≥1 of:
   - 5 resolved forecasts for same thesis/tag/class,
   - 8 unresolved with consistent favorable/adverse drift across ≥2 UTC dates,
   - weekly recap showing same lesson across independent markets.
   
   Weaker → add to **Pending evidence** only.

6. **Smartness scorecard (v2 — read from `state/scorecard.json` first).** `skills/recalibrate.sweep()` keeps this file fresh on every cycle. Reflect's job is now governance, not recomputation. Order of preference:

   1. `state/scorecard.json` if `updated_at >= now - 12h` → use directly.
   2. Today's `recaps/<date>.md` fenced JSON → use if scorecard.json is stale.
   3. Fall back to recomputing from `state/forecasts.resolved.jsonl` (slow path).

   Schema (full):
   - `exploit.{brier_agent, brier_market_p, brier_skill, calibration_slope, calibration_intercept, auc, kl_vs_market, drift_skill, resolved_n, unresolved_n}`
   - `explore.{brier_explore, brier_market_p, calibration_slope, buckets_filled, resolved_n, unresolved_n}`
   - `by_provider[]`, `by_feature_tag[]`

   **Use the v2 cold-start carve-out** (per `strategy/current.md` § Reflection-quality gate): when `exploit.resolved_n < 5`, the regression gate operates on `explore.calibration_slope` instead of `exploit.brier_skill`.

   Hold in memory; write into `metrics` of the `reflection` event in step 9.

7. **Convergent calibration update law** (per `strategy/current.md`). Per bucket with `resolved_n >= 10`:
   ```
   shrink     = min(1.0, resolved_n / 30)
   adjustment = clamp(shrink * (hit_rate - bucket_midpoint), -0.08, +0.08)
   ```
   These are the **proposed** v(N+1) calibration ledger. Don't write yet.

8. **Reflection-quality gate.** Simulate v(N+1) on trailing 14d resolved:
   1. Re-derive each `your_p` under proposed v(N+1) calibration + feature-tag + source penalties.
   2. Recompute `brier_agent` → `brier_skill_after`.
   3. Read `brier_skill_before` from today's scorecard.
   4. If `brier_skill_after < brier_skill_before - 0.005` AND not a risk-tightening edit → **refuse**. Emit `reflection edited:false reason:"regression_blocked"`, include both metrics, append proposal to **Pending evidence** (no version bump, no snapshot), exit.

9. **Auto-revert.** Inspect last 3 `reflection` events:
   - All 3 `brier_skill < last_good_version.brier_skill` (read `strategy/history/`) → next edit MUST be revert.
   - Copy `last_good_version` snapshot to `current.md`, preserve failed-run as `strategy/history/<date>-v<failed_N>.md`, bump version, emit `reflection edited:true reason:"auto_revert" reverted_to:"<vN>"`. Skip the standard edit branch.

10. **Exploration retries.** Walk hypothesis registry:
    - `status:"demoted"` with `next_retry_date <= today` → `status:"probation"`, `sizing_mult:0.5`, clear date. Pending evidence: "probation collection, 5 forecasts".
    - `status:"probation"` with ≥5 resolved since promotion → batch `brier_skill > 0` → `status:"watch" sizing_mult:1.0`; else re-demote with `next_retry_date = today + 14d`.

11. **Decide edit.** Edit if: hit-rate/Brier worse than threshold; repeated mispricing pattern not captured; correlation surprise; research method consistently better; new evidence changes thesis status (even if no rule change). Don't edit otherwise. Emit `reflection edited:false` either way to mark today done.

12. **If editing:**
    - Read frontmatter `version: vN` → bump `v(N+1)`.
    - **Snapshot:** copy to `strategy/history/YYYY-MM-DD-v<old_N>.md`. Name conflict → `-v<old_N>a`.
    - Update **structured** learning state (not free-text):
      - **Current decision rules** (calibration, sizing, filters, correlation, edge floor).
      - **Calibration ledger** (bucket, count, Brier, hit rate, adjustment).
      - **Hypothesis registry** (thesis/tag, status, evidence count, action).
      - **Pending evidence**.
      - **Caveats**.
    - Write new `current.md` with `version: v(N+1)`. Incremental; append rationale to **Changelog**.

13. **`reflection` event** via `journal`:
    ```json
    {"event_type":"reflection","date":"<YYYY-MM-DD>","edited":true,"prior_version":"v<old_N>","new_version":"v<N+1>","snapshot":"strategy/history/<YYYY-MM-DD>-v<old_N>.md","reason":"normal|regression_blocked|auto_revert|risk_tighten","reverted_to":null,"metrics":{"resolved_forecasts":0,"brier_agent":null,"brier_market_p":null,"brier_skill_before":null,"brier_skill_after":null,"calibration_slope":null,"calibration_intercept":null,"auc":null,"kl_vs_market":null,"drift_skill":null,"rejected_drift":null,"unresolved_drift_count":0},"per_source":[],"per_feature_tag":[],"promoted":[],"demoted":[],"probation_started":[],"probation_resolved":[],"pending":["<lesson>"],"rationale":"<short>"}
    ```

14. **Commit msg** (handled by `persist`): `feat(strategy): reflect -> v<N+1> (snapshot v<old_N>) [cycle <cid>]`.

15. **Guardrail recommendation.** If `guardrails.md` should change → `risk.surface_recommendation(text)` so next daily summary includes it. **Do not edit guardrails.**

## Failure modes

- No activity → write `reflection edited:false`.
- No learning fields → score what's possible; add missing fields to pending evidence.
- YAML version parse fail → treat as `v0`; write `v1` snapshot.
- Snapshot write fail → do NOT overwrite `current.md`. Log + exit.
- Gate refused → not an error; `edited:false reason:"regression_blocked"`. Re-try next day with more data.
- Auto-revert path → revert IS a normal edit for snapshotting + version bump, but mark `reason:"auto_revert"` so future reflections see it.
