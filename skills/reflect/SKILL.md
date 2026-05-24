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
     "metrics": {
       "resolved_forecasts": 0,
       "brier": null,
       "unresolved_drift_count": 0
     },
     "promoted": [],
     "demoted": [],
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
