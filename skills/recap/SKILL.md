---
name: recap
description: Aggregates trade-log into daily + weekly reports. Reads state/scorecard.json (kept fresh by recalibrate); embeds it as fenced JSON. Pure derivation; emits a recap event.
inputs: state/trade-log.jsonl, portfolio.json, cycle-index.json, scorecard.json
outputs: recaps/YYYY-MM-DD.md, recaps/YYYY-Www.md (Sun), recap event
---

# Recap

Invoked by `daily-close`. Recap embeds the scorecard `reflect` will consume.

## Daily

1. **Dedupe.** Grep trade-log for `event_type=="recap" kind:"daily" date:<today>` → exit if present.

2. **Aggregate today's events** (UTC date):
   - Cycles started/completed (from `phase_completed`).
   - Phases run vs expected 4.
   - Research notes written.
   - Candidates ranked / top market per phase.
   - Forecasts count + avg `your_p - market_p`, sliced by `learning_intent`.
   - Paper fills (count + total notional).
   - Mainnet fills (count + total notional + fees).
   - Halts.
   - NAV start-of-day vs now (Δ%).
   - Open positions count + cost basis + MTM.
   - **`null_cycle`** events from the day (auditable floor misses).
   - **Learning scorecard:** resolved (count, hit rate, Brier); unresolved (midpoint drift, CLV — not truth); attribution by `strategy_version` / `thesis_id` / `feature_tags` / `source_providers` / `learning_intent`. Explore vs exploit slices reported separately.
   - **Smartness scorecard:** read from `state/scorecard.json` if `updated_at >= now - 12h`; else recompute from `state/forecasts.resolved.jsonl`. Embed as fenced JSON. Schema:
     - `exploit.{brier_agent, brier_market_p, brier_skill, calibration_slope, calibration_intercept, auc, kl_vs_market, drift_skill, resolved_n, unresolved_n}`
     - `explore.{brier_explore, brier_market_p, calibration_slope, buckets_filled, resolved_n, unresolved_n}`
     - `by_provider[]`, `by_feature_tag[]`
     - Recap-derived: `brier_skill_trend_14d`, `last_good_version`, `days_since_last_improvement`, `exploration_due_today`, `reflection_outcomes_30d = {accepted, regression_blocked, auto_revert}`.

3. **Write `recaps/YYYY-MM-DD.md`** with frontmatter:
   ```yaml
   ---
   kind: daily
   date: <YYYY-MM-DD>
   cycle_id: <cid>
   strategy_version: <vN>
   ---
   ```
   Sections: Summary, Activity by phase, P&L, Open positions, Learning scorecard, Smartness scorecard (fenced JSON), Notes. Both scorecards must be structured tables/JSON — `reflect` reads programmatically.

4. **`recap` event** via `journal`:
   ```json
   {"event_type":"recap","kind":"daily","date":"<YYYY-MM-DD>","path":"recaps/<YYYY-MM-DD>.md","nav_usdc":<n>,"pnl_pct_24h":<p>}
   ```

5. Hand off → `notify daily_summary`.

## Weekly (Sundays only)

1. Caller passes `is_weekly=true` when `date('+%u')==7`.
2. Dedupe with `kind:"weekly" iso_week:<YYYY-Www>`.
3. Aggregate last 7d: total fills + fees; hit rate; Brier; NAV trajectory; best/worst call; strategy versions + reflection edits; halts; calibration by bucket + market class; hypotheses promoted/demoted/collecting; **7-day smartness delta** (`brier_skill` Δ, slope/intercept change, AUC change, penalties added/lifted, exploration retries, auto-reverts, regression-blocked edits). One-line verdict: sign of `brier_skill` Δ + slope trend toward 1.0.
4. **Write `recaps/YYYY-Www.md`** frontmatter `kind: weekly`, `iso_week: YYYY-Www`. Sections: Performance, Trade quality, Calibration, Strategy evolution, Risk events, Recommendations for human review. Groom `findings[]` (if `daily-close` passed any) go under *Recommendations for human review*.
5. `recap` event `kind:"weekly"`.
6. Hand off → `notify weekly_recap`.

## Phase-miss detection

Flag any of the 4 phases without today's `phase_completed`. Missing → emit `phase_missed` per gap; daily summary includes them.

## Failure modes

- No activity → still write file + emit `recap` (preserves dedupe).
- Cannot resolve Gamma outcomes → mark hit-rate/Brier `tbd`, proceed.
