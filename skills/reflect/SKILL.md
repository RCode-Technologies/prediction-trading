---
name: reflect
description: Daily self-review and learning loop. Scores forecasts, updates the strategy learning state, snapshots the prior version. May only edit strategy/current.md (ADR 0005).
inputs: last 24h plus trailing unresolved forecasts from trade-log, current strategy/current.md, recent recaps/
outputs: strategy/current.md (if edited), strategy/history/YYYY-MM-DD-vN.md snapshot, reflection event
---

# Reflect

Strategy self-improvement loop. Runs once per UTC date from the end-of-day
routine. Snapshot-then-edit (ADR 0007). This skill is where history becomes a
better future policy; recaps and logs alone are not learning.

## Hard rules

- **May only edit `strategy/current.md`.** Never `config/guardrails.md`,
  never `AGENTS.md`, never routines, never skills (ADR 0005).
- **Snapshot on every edit.** Always copy the prior version to
  `strategy/history/YYYY-MM-DD-vN.md` before overwriting.
- **Do not claim guaranteed improvement.** Learning is empirical and may be
  noisy; record uncertainty and avoid overfitting sparse data.

## Steps

1. **Idempotency check.** Grep `state/trade-log.jsonl` for
   `event_type=="reflection"` with `date:<today UTC>`. If found, exit.

2. **Build the learning dataset.** Pull today's events plus any unresolved
   forecasts from the trailing 30 days that now have a resolution or fresh
   midpoint. Join by `forecast_id` where present, otherwise by
   `market_id`/`token_id`/`ts`. Keep the fields needed for attribution:
   `strategy_version`, `thesis_id`, `feature_tags`, `source_providers`,
   `prior_p`, `raw_your_p`, `your_p`, `market_p`, `confidence`,
   `calibration_bucket`, `close_time`, and `decision`/fill linkage.

3. **Score forecast quality.** For each resolved market, compute Brier score
   `(your_p - outcome)^2`, hit/miss, and optional log loss with probabilities
   clamped away from 0/1. For unresolved markets, compare forecast price to
   current midpoint / closing line and flag drift; do not treat drift as final
   truth. For fills, aggregate realized P&L where resolved and MTM P&L where
   open.

4. **Attribute what worked.** Aggregate by strategy version, thesis, feature
   tag, market class, and `source_providers`. Record both positive and negative
   evidence. The `recap` skill already wrote much of this to today's
   `recaps/YYYY-MM-DD.md`; read it first, then recompute only gaps.

5. **Apply anti-overfitting gates.** A rule may tighten immediately on a
   severe risk miss, correlation surprise, stale-mark failure, or source
   quality failure. Otherwise require at least one of:
   - 5 resolved forecasts for the same thesis/tag or market class,
   - 8 unresolved forecasts with consistent favorable or adverse midpoint
     drift across at least 2 UTC dates,
   - a weekly recap showing the same lesson across independent markets.
     If evidence is weaker, add it to pending evidence instead of changing a
     trading rule.

5a. **Compute the smartness scorecard.** Read the block written by
    `skills/recap` for today (`recaps/<date>.md` "Smartness scorecard")
    and the trailing 30d slice from prior recaps. If recap did not run or
    its scorecard is empty, recompute from `state/trade-log.jsonl` directly:

    - `brier_agent`, `brier_market_p`, `brier_skill = brier_market_p - brier_agent`
    - `calibration_slope`, `calibration_intercept` (OLS over `your_p` vs outcome)
    - `auc`, `kl_vs_market`, `drift_skill`, `rejected_drift`
    - per-provider `{resolved_n, brier_provider, brier_market_p}`
    - per-`feature_tag` `{resolved_n, brier_tag, brier_market_p}`

    Hold these in memory for the next steps. Write them into the `metrics`
    block of the `reflection` event at step 8.

5b. **Apply the convergent calibration update law** (see
    `strategy/current.md` → "Smartness metrics and self-improvement gates"
    → "Convergent calibration update law"). For each bucket with
    `resolved_n >= 10`:

    ```
    adjustment = clamp(min(1.0, resolved_n/30) * (hit_rate - bucket_mid),
                       -0.08, +0.08)
    ```

    Use the resulting adjustments as the **proposed** v(N+1) calibration
    ledger. Do not write yet.

5c. **Reflection-quality gate.** Simulate v(N+1) on the trailing 14 days
    of resolved forecasts:

    1. Re-derive each forecast's `your_p` under the proposed v(N+1)
       calibration + feature-tag penalties + source penalties.
    2. Recompute `brier_agent` → `brier_skill_after`.
    3. Read `brier_skill_before` from today's scorecard.
    4. If `brier_skill_after < brier_skill_before - 0.005` **and** the edit
       is not a risk-tightening edit (severe miss, correlation surprise,
       stale-mark failure, source-quality failure), **refuse the edit**.
       Emit `reflection` with `edited:false`,
       `reason:"regression_blocked"`, include both `brier_skill_before`
       and `brier_skill_after` in `metrics`, append the proposal to
       **Pending evidence** in `strategy/current.md` (this is a
       pending-evidence-only append; no version bump, no history snapshot),
       and exit.

5d. **Auto-revert check.** Inspect the last 3 `reflection` events:
    - If all three have `brier_skill` lower than `last_good_version`'s
      `brier_skill` (reading from `strategy/history/`), the next edit
      must be a revert.
    - Copy the `last_good_version` snapshot back to `strategy/current.md`,
      preserve the failed-run version as
      `strategy/history/<date>-v<failed_N>.md`, bump the version, and emit
      `reflection` with `edited:true`, `reason:"auto_revert"`,
      `reverted_to:"<vN>"`. Skip the standard "decide whether to edit"
      branch.

5e. **Exploration retries.** Walk the hypothesis registry:
    - For each `status:"demoted"` thesis with `next_retry_date <= today`:
      flip to `status:"probation"`, `sizing_mult:0.5`, clear
      `next_retry_date`. Mark in pending evidence: "probation collection,
      5 forecasts".
    - For each `status:"probation"` thesis with ≥ 5 resolved forecasts
      since promotion: compute that batch's `brier_skill`. If `> 0`, set
      `status:"watch"`, `sizing_mult:1.0`. Else re-demote with
      `next_retry_date = today + 14d`.

6. **Decide whether to edit.** Reasons to edit:
   - Hit-rate or Brier worse than the strategy's stated threshold.
   - Repeated mispricing pattern not captured in current strategy.
   - Correlation surprise (two trades turned out related).
   - A research method that consistently produced better forecasts.
   - New evaluated evidence changes the status of a thesis in the learning
     state, even if no trading rule changes yet.

   Reasons not to edit: no new evaluated evidence, or too few data points and
   no new pending-evidence note. Emit `reflection` with `edited: false` either
   way to mark today done.

7. **If editing:**
   - Read `strategy/current.md` frontmatter, parse `version: vN`,
     increment to `v(N+1)`.
   - **Snapshot:** copy current file to
     `strategy/history/YYYY-MM-DD-v<old_N>.md`. If filename already exists
     today, append a letter suffix (`-v<old_N>a`).
   - Update the strategy's structured learning state, not only free-text
     notes. Maintain these sections when present:
     - **Current decision rules**: calibration, sizing, market filters,
       correlation rules, edge floor.
     - **Calibration ledger**: bucket, count, Brier, hit rate, adjustment.
     - **Hypothesis registry**: thesis/tag, status, evidence count,
       action (`promote`, `demote`, `watch`, `retire`).
     - **Pending evidence**: weak signals that should be tested again.
     - **Caveats**: known limits and data gaps.
   - Write new `strategy/current.md` with `version: v(N+1)`. Keep the change
     incremental; append rationale to the `# Changelog` section at the bottom.

8. **Emit `reflection` event** via `journal`:

   ```json
   {
     "event_type": "reflection",
     "date": "<YYYY-MM-DD>",
     "edited": true,
     "prior_version": "v<old_N>",
     "new_version": "v<N+1>",
     "snapshot": "strategy/history/<YYYY-MM-DD>-v<old_N>.md",
     "reason": "normal|regression_blocked|auto_revert|risk_tighten",
     "reverted_to": null,
     "metrics": {
       "resolved_forecasts": 0,
       "brier_agent": null,
       "brier_market_p": null,
       "brier_skill_before": null,
       "brier_skill_after": null,
       "calibration_slope": null,
       "calibration_intercept": null,
       "auc": null,
       "kl_vs_market": null,
       "drift_skill": null,
       "rejected_drift": null,
       "unresolved_drift_count": 0
     },
     "per_source": [],
     "per_feature_tag": [],
     "promoted": [],
     "demoted": [],
     "probation_started": [],
     "probation_resolved": [],
     "pending": ["<lesson>"],
     "rationale": "<short>"
   }
   ```

9. **Conventional commit message** (handled by `persist` skill at end of
   end-of-day routine):

   ```
   feat(strategy): reflect -> v<N+1> (snapshot v<old_N>) [cycle <cycle_id>]
   ```

10. **Guardrail recommendation hint.** If reflection thinks
    `config/guardrails.md` should change, call `risk.surface_recommendation(text)`
    so the next daily summary includes it. **Do not edit `guardrails.md`.**

## Failure modes

- **No activity:** acceptable; write `reflection` with `edited: false`.
- **No learning fields:** still score what is possible, but add missing fields
  to pending evidence so future forecasts become attributable.
- **YAML version parse fails:** treat as `v0`; write `v1` snapshot.
- **Snapshot write fails:** do not overwrite `current.md`. Log + exit.
- **Smartness gate refused the edit:** not an error. Emit
  `reflection` with `edited:false`, `reason:"regression_blocked"`, append
  the proposal to pending evidence. Next reflection re-tries with more data.
- **Auto-revert path:** treat the revert as a normal edit for snapshotting
  and version bump, but mark `reason:"auto_revert"` so future reflections
  see it in the trade-log when computing `last_good_version`.
