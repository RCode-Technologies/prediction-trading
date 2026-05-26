---
name: recalibrate
description: Continuous, hook-driven scorecard + calibration update. Runs on every relevant journal append (forecast, paper_fill, mainnet_fill, resolution); reflect/recap read its outputs instead of recomputing.
inputs: event (from journal hook) | sweep mode | open-forecast ledger
outputs: state/scorecard.json, state/calibration.json, state/forecasts.open.jsonl, recalibration event
---

# Recalibrate

The structural fix for v1's "improvement only happens in `reflect` which only runs in `daily-close` which may never fire." In v2, adaptation runs **every time the journal is touched**.

Two entry points:

- `tick(event)` — fast incremental update fired by `skills/journal` post-append (see journal step 4).
- `sweep()` — full recompute + Gamma resolution lookup, called by `overnight-watch` and `daily-close`.

## State files owned

### `state/scorecard.json`

Single source of truth for the smartness scorecard. Read by `recap`, `reflect`, `notify daily_summary`.

```json
{
  "schema_version": 1,
  "updated_at": "<iso>",
  "window_days": 30,
  "exploit": {
    "resolved_n": 0,
    "unresolved_n": 0,
    "brier_agent": null,
    "brier_market_p": null,
    "brier_skill": null,
    "calibration_slope": null,
    "calibration_intercept": null,
    "auc": null,
    "kl_vs_market": null,
    "drift_skill": null
  },
  "explore": {
    "resolved_n": 0,
    "unresolved_n": 0,
    "brier_explore": null,
    "brier_market_p": null,
    "calibration_slope": null,
    "buckets_filled": 0
  },
  "by_provider": [],
  "by_feature_tag": []
}
```

### `state/calibration.json`

Per-bucket ledger, sliced by `learning_intent`. Mirrors the table in `strategy/current.md` but is machine-updated.

```json
{
  "schema_version": 1,
  "updated_at": "<iso>",
  "exploit": {
    "50-60": {"resolved_n": 0, "brier": null, "hit_rate": null, "adjustment": 0.0, "status": "collect"},
    "60-70": {...},
    "70-80": {...},
    "80-90": {...}
  },
  "explore": {
    "30-40": {...},
    "40-50": {...},
    "50-60": {...},
    "60-70": {...},
    "70-80": {...}
  }
}
```

### `state/forecasts.open.jsonl`

Append-only index of unresolved forecasts. Each line:

```json
{"forecast_id":"<id>","market_id":"<id>","token_id":"<tid>","learning_intent":"<intent>","your_p":<p>,"market_p":<p>,"close_time":"<iso>","emitted_at":"<iso>","calibration_bucket":"<lo-hi>","resolved":false}
```

`sweep()` compacts by writing only `resolved:false` rows on rewrite (atomic via `.tmp` + `mv`).

## `tick(event)` steps

Called synchronously from `skills/journal` step 4 after a successful append. Must be cheap and **must never block the append**.

1. **Filter event_type.** Operate only on `forecast`, `paper_fill`, `mainnet_fill`. Other types → no-op, return.
2. **For `forecast`:**
   - Append to `state/forecasts.open.jsonl` with `resolved:false`.
   - Increment `scorecard.<intent>.unresolved_n` (atomic jq update).
   - Update `scorecard.updated_at = now`.
3. **For `paper_fill` or `mainnet_fill`:**
   - Look up the parent forecast by `forecast_id` (or `idempotency_key`).
   - Annotate the open-forecasts ledger entry with `fill_price`, `fill_shares`, `fill_ts`.
   - Update portfolio MTM (delegated to `risk.nav()` — recalibrate does NOT write portfolio.json).
4. **Emit `recalibration`** via `journal` (note: this is a recursive write but `tick` filters on event_type so it does not loop):
   ```json
   {"event_type":"recalibration","trigger":"<event_type>","forecast_id":"<id>","status":"ok","scorecard_path":"state/scorecard.json"}
   ```
5. **Return** immediately. Heavy lifting (Brier recompute, slope/intercept) deferred to `sweep()`.

## `sweep()` steps

Called explicitly by `overnight-watch` (light) and `daily-close` (full). Source-budget-aware: prefers cached resolution data; only spends Gamma sources when an open forecast has passed `close_time` and is not yet resolved.

1. **Read open forecasts.** Filter `state/forecasts.open.jsonl` to `resolved:false`.
2. **Identify candidates for resolution lookup.** Open forecasts with `close_time < now`. Group by `market_id` to dedupe Gamma calls.
3. **Query Gamma** for resolution status. ≤1 source per cycle for this sweep. Skip if budget exhausted.
   ```
   GET https://gamma-api.polymarket.com/markets/<market_id>
   ```
   Look for `closed:true` + outcome resolution (`umaResolutionStatuses`, `resolvedBy`, or per-market resolution field per Polymarket schema).
4. **For each resolved market:**
   - Mark all open forecasts on that market `resolved:true, outcome:0|1, resolution_ts:<iso>`.
   - Move the row to `state/forecasts.resolved.jsonl` (append-only archive).
5. **Recompute scorecard.** Read trailing 30d from `state/forecasts.resolved.jsonl`:
   - **Exploit slice:** filter `learning_intent=="exploit"`.
     - `brier_agent = mean((your_p - outcome)^2)`
     - `brier_market_p = mean((market_p - outcome)^2)`
     - `brier_skill = brier_market_p - brier_agent`
     - `calibration_slope, calibration_intercept`: OLS of `outcome ~ your_p`.
     - `auc`: rank-AUC of `your_p` vs outcome (ties = 0.5).
     - `kl_vs_market = mean(your_p*log(your_p/market_p) + (1-your_p)*log((1-your_p)/(1-market_p)))` clamped away from 0/1.
     - `drift_skill`: for unresolved exploit forecasts, fraction whose current midpoint moved toward `your_p` more than toward forecast-time `market_p`. Requires a fresh CLOB book call per market — capped at 5 per sweep, oldest first.
   - **Explore slice:** filter `learning_intent=="explore"`. Same formulas with `your_p` = `market_p + ε`.
6. **Recompute calibration.** Per bucket × intent:
   - `resolved_n` = count
   - `hit_rate` = mean(outcome) among forecasts in that bucket
   - `brier` = mean((your_p - outcome)^2)
   - `adjustment` = per `strategy/current.md` § convergent update law (shrinkage formula).
   - `status` = `collect` if `resolved_n < 10`, else `active`.
7. **Per-provider / per-feature_tag slices.** Filter by exact match of `source_providers[]` and `feature_tags[]`. Compute Brier vs market baseline. Write into `scorecard.by_provider` and `scorecard.by_feature_tag`.
8. **Atomic write** all three state files via `.tmp` + `mv`.
9. **Emit `recalibration`** via `journal`:
   ```json
   {"event_type":"recalibration","trigger":"sweep","resolved_new":<n>,"unresolved_total":<n>,"scorecard_path":"state/scorecard.json","calibration_path":"state/calibration.json"}
   ```
10. **Return** scorecard + calibration to caller.

## Source budget

`tick()` — 0 sources. `sweep()` — ≤1 Gamma source (resolution lookup), ≤5 CLOB book calls (drift_skill on unresolved). CLOB calls do not count as research sources.

## Failure modes

- `state/forecasts.open.jsonl` corrupted → reconstruct from `trade-log.jsonl` (filter `event_type=="forecast"`, exclude those with matching resolution).
- Gamma resolution lookup fails for a market → keep `resolved:false`, retry next sweep. Never guess outcomes.
- Hook fires during a cycle with the trade-log locked by an atomic write → retry once with 100ms backoff, then log `recalibration status:"failed" reason:"lock_contention"` and continue.
- Recursive write (tick emits recalibration which appends to journal which would re-tick) → `tick` filters on event_type and ignores `recalibration` events. No loop.

## What `reflect` should now do

Read `state/scorecard.json` + `state/calibration.json` first. Recompute only the slices needed for the current decision (e.g. the simulation in step 8 of `reflect`). The full scorecard is always fresh because `tick` ran on every relevant event. Reflection's job shrinks to **governance** (snapshot, version bump, regression gate) — adaptation is already done.
