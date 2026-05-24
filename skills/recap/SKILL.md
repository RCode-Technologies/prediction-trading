---
name: recap
description: Aggregates trade-log into daily + weekly reports. Daily at end-of-day; weekly Sundays. Pure derivation; only emits a recap event.
inputs: state/trade-log.jsonl, portfolio.json, cycle-index.json
outputs: recaps/YYYY-MM-DD.md, recaps/YYYY-Www.md (Sun), recap event
---

# Recap

Invoked by `daily-close`. Writes the scorecard handoff consumed by `reflect`.

## Daily

1. **Dedupe.** Grep trade-log for `event_type=="recap" kind:"daily" date:<today UTC>` → if present, exit.

2. **Aggregate today's events** (`ts` within current UTC date):
   - Cycles started / completed (from `phase_completed`).
   - Phases run vs expected 4.
   - Research notes written.
   - Candidates ranked / top market each phase.
   - Forecasts count + average `your_p - market_p`.
   - Paper fills (count + total notional).
   - Mainnet fills (count + total notional + fees).
   - Halts.
   - NAV start-of-day vs now (Δ%).
   - Open positions count + cost basis + MTM.
   - **Learning scorecard:** resolved (count, hit rate, Brier, optional log loss); unresolved (midpoint drift, CLV — not truth); attribution by `strategy_version` / `thesis_id` / `feature_tags` / `source_providers`; missing learning fields that blocked attribution.
   - **Smartness scorecard** (rolling 30 UTC dates, **fenced JSON block** so `reflect` can `jq` it):
     - `brier_agent`, `brier_market_p`, `brier_skill = brier_market_p - brier_agent`
     - `calibration_slope`, `calibration_intercept` (OLS outcome ~ your_p)
     - `auc`, `kl_vs_market`, `drift_skill`, `rejected_drift`
     - per-`source_providers`: `{provider, resolved_n, brier_provider, brier_market_p, penalty_active}`
     - per-`feature_tag`: `{tag, resolved_n, brier_tag, brier_market_p}`
     - `brier_skill_trend_14d` = OLS slope of daily `brier_skill` over trailing 14d
     - `last_good_version`, `days_since_last_improvement`
     - `exploration_due_today` = thesis IDs whose `next_retry_date <= today`
     - `reflection_outcomes_30d` = `{accepted, regression_blocked, auto_revert}` counts

3. **Write `recaps/YYYY-MM-DD.md`** with frontmatter:
   ```yaml
   ---
   kind: daily
   date: <YYYY-MM-DD>
   cycle_id: <cid>
   strategy_version: <vN>
   ---
   ```
   Sections: **Summary**, **Activity by phase**, **P&L**, **Open positions**, **Learning scorecard**, **Smartness scorecard** (fenced JSON), **Notes**. Both scorecards must be structured tables/JSON — `reflect` reads programmatically.

4. **`recap` event** via `journal`:
   ```json
   {"event_type":"recap","kind":"daily","date":"<YYYY-MM-DD>","path":"recaps/<YYYY-MM-DD>.md","nav_usdc":<n>,"pnl_pct_24h":<p>}
   ```

5. **Hand off** to `notify` → `daily_summary`.

## Weekly (Sundays only)

1. Trigger: caller passes `is_weekly=true` when `date('+%u')==7`.
2. Dedupe with `kind:"weekly" iso_week:<YYYY-Www>`.
3. Aggregate last 7 days: total fills + fees; hit rate on resolved; Brier; NAV trajectory (7 snapshots); best/worst call (realized P&L); strategy versions used + reflection edits; halts; calibration by bucket + market class; hypotheses promoted/demoted/collecting; decision quality (accepted vs rejected drift); **7-day smartness delta:** this week's `brier_skill` minus last week's, calibration slope/intercept change, AUC change, source-quality penalties added/lifted, exploration retries fired + outcome, auto-reverts, regression-blocked edits. One-line verdict: sign of `brier_skill` delta + calibration slope trend toward 1.0.
4. **Write `recaps/YYYY-Www.md`** with frontmatter `kind: weekly`, `iso_week: YYYY-Www`. Sections: **Performance**, **Trade quality**, **Calibration**, **Strategy evolution**, **Risk events**, **Recommendations for human review**.
5. `recap` event with `kind:"weekly"`.
6. Hand off to `notify` → `weekly_recap`.

## Phase-miss detection

Recap also flags whether `phase_completed` exists today for the 4 phases. Missing → emit `phase_missed` per gap; `notify` includes in daily summary.

## Failure modes

- No activity → still write file (empty sections OK) and emit `recap` (preserves dedupe).
- Cannot resolve Gamma outcomes → mark hit-rate/Brier as `tbd`, proceed.
