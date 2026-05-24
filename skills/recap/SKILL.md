---
name: recap
description: Aggregates trade-log into daily and weekly benchmark reports. Daily report runs at end-of-day; weekly recap fires on Sunday end-of-day. Outputs markdown files under recaps/.
inputs: state/trade-log.jsonl, state/portfolio.json, state/cycle-index.json
outputs: recaps/YYYY-MM-DD.md (daily), recaps/YYYY-Www.md (weekly on Sunday), recap event
---

# Recap

Generates the human-readable rollups. Skill is invoked from
`end-of-day` routine. Pure derivation — never mutates state besides emitting
a `recap` event.

## Daily — every end-of-day

1. **Dedupe.** Grep trade-log for `event_type=="recap"` with
   `kind:"daily"` and `date:<today UTC>`. If present, exit.

2. **Aggregate today's events** (`ts` within current UTC date):
   - Cycles started / completed (look at `phase_completed` events)
   - Phases run vs expected 4 (pre_market, market_open, midday, end_of_day)
   - Research notes written
   - Candidates ranked / top market each phase
   - Forecasts (count + average `your_p - market_p` edge)
   - Paper fills (count + total notional)
   - Mainnet fills (count + total notional + total fees)
   - Halt events
   - NAV at start of day vs now (Δ%)
   - Open positions count + total cost basis + mark-to-market value
   - Learning scorecard:
     - resolved forecasts: count, hit rate, Brier score, optional log loss
     - unresolved forecasts: midpoint drift and closing-line value since the
       forecast, never counted as truth
     - attribution by `strategy_version`, `thesis_id`, `feature_tags`, and
       `source_providers` where available
     - missing learning fields that blocked attribution
   - **Smartness scorecard** (rolling 30 UTC dates, the structured handoff
     to `skills/reflect` — emit as a fenced JSON block in the markdown so
     reflection can `jq` it without parsing prose):
     - `brier_agent`, `brier_market_p`, `brier_skill = brier_market_p - brier_agent`
     - `calibration_slope`, `calibration_intercept` (OLS of outcome on `your_p`)
     - `auc`, `kl_vs_market`, `drift_skill`, `rejected_drift`
     - per `source_providers`: `{provider, resolved_n, brier_provider, brier_market_p, penalty_active}`
     - per `feature_tag`: `{tag, resolved_n, brier_tag, brier_market_p}`
     - `brier_skill_trend_14d` = OLS slope of daily `brier_skill` over the
       trailing 14 UTC dates; sign drives the "is the agent improving?" verdict
     - `last_good_version`, `days_since_last_improvement`
     - `exploration_due_today` = thesis IDs whose `next_retry_date <= today`
     - `reflection_outcomes_30d` = `{accepted, regression_blocked, auto_revert}`
       counts of the last 30 reflection events

3. **Write `recaps/YYYY-MM-DD.md`** with frontmatter:

   ```yaml
   ---
   kind: daily
   date: <YYYY-MM-DD>
   cycle_id: <cycle_id>
   strategy_version: <vN>
   ---
   ```

   Body sections: **Summary**, **Activity by phase**, **P&L**,
   **Open positions**, **Learning scorecard**, **Smartness scorecard**,
   **Notes** (reflection hints if any). The learning scorecard + smartness
   scorecard together are the handoff to `skills/reflect`; both must use
   structured tables / fenced JSON, not prose, so reflection can read them
   programmatically.

4. **Emit `recap` event** via `journal`:

   ```json
   {"event_type":"recap","kind":"daily","date":"<YYYY-MM-DD>","path":"recaps/<YYYY-MM-DD>.md","nav_usdc":<n>,"pnl_pct_24h":<p>}
   ```

5. **Hand off** to `notify` skill: send `daily_summary` (paper + mainnet).

## Weekly — Sundays only

1. **Trigger condition:** caller passes `is_weekly=true` (end-of-day routine
   sets this when `date('+%u') == 7`).

2. **Dedupe** as in daily, with `kind:"weekly"` and `iso_week:<YYYY-Www>`.

3. **Aggregate last 7 days:**
   - Total fills (paper + mainnet) and total fees
   - Hit rate for resolved markets in window
   - Brier score across resolved forecasts
   - NAV trajectory (7 snapshots)
   - Best call (max realized P&L) and worst call (min realized P&L)
   - Strategy versions used in window + number of reflection edits
   - Halt incidents
   - Calibration by probability bucket and market class
   - Hypotheses promoted, demoted, or still collecting evidence
   - Decision quality: accepted vs rejected candidates and their later drift
   - **7-day smartness delta**: this week's `brier_skill` minus last week's,
     calibration slope/intercept change, AUC change, source-quality
     penalties added or lifted, exploration retries fired and their outcome,
     auto-reverts triggered, regression-blocked edits. Surface "is the agent
     getting smarter week-over-week?" as a one-line verdict driven by the
     sign of the `brier_skill` delta and the calibration-slope movement
     toward 1.0.

4. **Write `recaps/YYYY-Www.md`** (ISO week) with frontmatter `kind: weekly`,
   `iso_week: YYYY-Www`. Body: **Performance**, **Trade quality**,
   **Calibration**, **Strategy evolution**, **Risk events**,
   **Recommendations for human review**.

5. **Emit `recap` event** with `kind: weekly`.

6. **Hand off** to `notify`: send `weekly_recap` (paper + mainnet).

## Cross-phase detection helper

Recap also computes `phase_missed` flags: did `pre_market`, `market_open`,
`midday`, and `end_of_day` all log a `phase_completed` today? If any
missing, emit a `phase_missed` event with the gap and ask `notify` to
include it in the daily summary.

## Outputs to caller

`{daily_path, weekly_path|null, missed_phases: [...]}`.

## Failure modes

- **No activity in the window:** still write the file (empty sections OK)
  and emit `recap` so dedupe holds.
- **Cannot resolve resolved-market outcomes from Gamma:** mark hit-rate /
  Brier as `tbd` and proceed.
