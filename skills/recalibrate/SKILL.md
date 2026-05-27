---
name: recalibrate
description: Continuous scorecard + calibration update. tick() runs on every relevant journal append; sweep() runs in overnight-watch and daily-close. reflect/recap read its outputs.
inputs: event (from journal hook) | sweep mode | open-forecast ledger
outputs: state/scorecard.json, state/calibration.json, state/forecasts.{open,resolved}.jsonl, recalibration event
---

# Recalibrate

Adaptation runs whenever journal is touched, not only when `daily-close` fires. Two entrypoints:

- `tick(event)` — fast incremental update from `skills/journal` post-append hook.
- `sweep()` — full recompute + Gamma resolution lookup, from `overnight-watch` and `daily-close`.

## State files owned

### `state/scorecard.json`

```json
{
  "schema_version": 1,
  "updated_at": "<iso>",
  "window_days": 30,
  "exploit": {"resolved_n":0,"unresolved_n":0,"brier_agent":null,"brier_market_p":null,"brier_skill":null,"calibration_slope":null,"calibration_intercept":null,"auc":null,"kl_vs_market":null,"drift_skill":null},
  "explore": {"resolved_n":0,"unresolved_n":0,"brier_explore":null,"brier_market_p":null,"calibration_slope":null,"buckets_filled":0},
  "by_provider": [],
  "by_feature_tag": []
}
```

### `state/calibration.json`

Per-bucket × intent. Mirrors `strategy/current.md` tables but machine-updated.

```json
{
  "schema_version": 1,
  "updated_at": "<iso>",
  "exploit": {"50-60": {"resolved_n":0,"brier":null,"hit_rate":null,"adjustment":0.0,"status":"collect"}, ...},
  "explore": {"30-40": {"resolved_n":0,"brier_explore":null,"brier_market_p":null,"calibration_slope":null,"status":"collect"}, ...}
}
```

### `state/forecasts.open.jsonl`

Append-only index of unresolved forecasts. One line per forecast:
```json
{"forecast_id":"<id>","market_id":"<id>","token_id":"<tid>","learning_intent":"<intent>","your_p":<p>,"market_p":<p>,"close_time":"<iso>","emitted_at":"<iso>","calibration_bucket":"<lo-hi>","resolved":false}
```

`sweep()` compacts by rewriting only `resolved:false` rows (atomic via `.tmp` + `mv`).

## `tick(event)`

Synchronous from `skills/journal` step 4. Must be cheap; must not block the append.

1. Filter event_type to `{forecast, paper_fill, mainnet_fill}`. Else no-op.
2. **`forecast`**: append to `state/forecasts.open.jsonl` (`resolved:false`). Increment `scorecard.<intent>.unresolved_n`. Bump `updated_at`.
3. **`paper_fill` / `mainnet_fill`**: find parent forecast by `forecast_id` (or `idempotency_key`). Annotate the open-ledger entry with `fill_price`, `fill_shares`, `fill_ts`. Portfolio MTM = `risk.nav()` responsibility, not recalibrate's.
4. Emit `recalibration` via `journal` (won't loop — `tick` filters event_type):
   ```json
   {"event_type":"recalibration","trigger":"<event_type>","forecast_id":"<id>","status":"ok","scorecard_path":"state/scorecard.json"}
   ```
5. Return. Heavy lifting (Brier, slope/intercept) deferred to `sweep()`.

## `sweep()`

Source-budget aware. Spends Gamma only when open forecasts have passed `close_time`.

1. Read `state/forecasts.open.jsonl`, filter `resolved:false`.
2. Group open forecasts past `close_time` by `market_id`.
3. Query Gamma (`GET /markets/<market_id>`) for resolution. ≤1 source/cycle. Skip if budget exhausted.
4. For each resolved market: mark all open forecasts on it `resolved:true, outcome:0|1, resolution_ts:<iso>`. Move row to `state/forecasts.resolved.jsonl`.
5. **Recompute scorecard** from trailing 30d resolved:
   - Exploit slice (`learning_intent=="exploit"`):
     - `brier_agent = mean((your_p - outcome)^2)`
     - `brier_market_p = mean((market_p - outcome)^2)`
     - `brier_skill = brier_market_p - brier_agent`
     - `calibration_slope, calibration_intercept` = OLS(outcome ~ your_p)
     - `auc` = rank-AUC, ties=0.5
     - `kl_vs_market = mean(your_p*log(your_p/market_p) + (1-your_p)*log((1-your_p)/(1-market_p)))` (clamped)
     - `drift_skill`: fraction of unresolved exploit forecasts whose current midpoint moved toward `your_p` more than toward forecast-time `market_p`. Capped at 5 CLOB book calls/sweep, oldest first.
   - Explore slice (`learning_intent=="explore"`): same formulas with `your_p = market_p + ε`.
6. **Recompute calibration** per bucket × intent: `resolved_n`, `hit_rate = mean(outcome)`, `brier`, `adjustment` (per `strategy/current.md` convergent update law). `status = collect` if `n<10`, else `active`.
7. Per-provider / per-feature_tag slices: filter by exact `source_providers[]` / `feature_tags[]`. Compute Brier vs market baseline.
8. Atomic write `state/scorecard.json`, `state/calibration.json`, `state/forecasts.open.jsonl` via `.tmp` + `mv`.
9. Emit `recalibration` via `journal`:
   ```json
   {"event_type":"recalibration","trigger":"sweep","resolved_new":<n>,"unresolved_total":<n>}
   ```

## Source budget

`tick()` — 0 sources. `sweep()` — ≤1 Gamma (resolution), ≤5 CLOB book calls (drift_skill). CLOB doesn't count toward research budget.

## Failure modes

- `state/forecasts.open.jsonl` corrupted → reconstruct from `trade-log.jsonl` (`forecast` events without matching resolution).
- Gamma resolution lookup fails → keep `resolved:false`, retry next sweep. Never guess outcomes.
- Lock contention during write → retry once after 100ms, then log `recalibration status:"failed" reason:"lock_contention"`.
- Missing state files on first run → create with empty schema.

## `reflect` integration

Read `state/scorecard.json` + `state/calibration.json` first. Recompute only the slice needed for the current decision (e.g. the simulation in `reflect` step 8). Full scorecard is always fresh because `tick()` ran on every relevant event. Reflection's role narrows to **governance** (snapshot, version bump, regression gate).
