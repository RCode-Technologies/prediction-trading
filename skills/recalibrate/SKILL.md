---
name: recalibrate
description: Continuous scorecard + calibration update. tick() runs on every relevant journal append; snap_clv() takes CLV snapshots on pulse/overnight-watch/daily-close; sweep() runs in overnight-watch and daily-close. reflect/recap read its outputs.
inputs: event (from journal hook) | snap_clv pulse | sweep mode | open-forecast ledger
outputs: state/scorecard.json, state/calibration.json, state/forecasts.{open,resolved}.jsonl, recalibration event
---

# Recalibrate

> **Protected-core rail (HARD) — human-authored only.** The agent runs this skill but never edits it. The verdict is mechanical, not narrated: `config/autonomy.md` § Enforcement (intent gate · write gate · `boot` audit · `.githooks/pre-commit`). A `protected_core_violation` is valid only when `skills/boot/protected-core-audit.sh` exits 3 — never from authorship reasoning, a recalled hash, or which files the last fix touched.

Adaptation runs whenever journal is touched, not only when `daily-close` fires. Three entrypoints:

- `tick(event)` — fast incremental update from `skills/journal` post-append hook; appends each `forecast` to the open ledger.
- `snap_clv()` — cheap CLV snapshot of due open forecasts, from **pulse (heartbeat)**, `overnight-watch`, and `daily-close`. The primary fast-learning signal; rides existing cycles (zero added invocations, no new forecasts).
- `sweep()` — full recompute + Gamma resolution lookup, from `overnight-watch` and `daily-close` (calls `snap_clv()` first + runs the open-ledger self-check).

## State files owned

### `state/scorecard.json`

```json
{
  "schema_version": 1,
  "updated_at": "<iso>",
  "window_days": 30,
  "exploit": {"resolved_n":0,"unresolved_n":0,"brier_agent":null,"brier_market_p":null,"brier_skill":null,"calibration_slope":null,"calibration_intercept":null,"auc":null,"kl_vs_market":null,"drift_skill":null,"clv_mean":null,"clv_hit_rate":null,"clv_n":0},
  "explore": {"resolved_n":0,"unresolved_n":0,"brier_explore":null,"brier_market_p":null,"calibration_slope":null,"buckets_filled":0,"clv_mean":null,"clv_hit_rate":null,"clv_n":0},
  "by_edge_source": [],
  "by_provider": [],
  "by_feature_tag": []
}
```

**v3 CLV fields** (the primary fast-learning signal while `resolved_n < 30` — see `strategy/current.md` § Smartness scorecard):
- `<intent>.clv_mean` — mean `clv` across all `clv_snaps` of that intent's open+resolved forecasts (any window). Non-null once ≥1 forecast has a snap (i.e. has aged ≥6h).
- `<intent>.clv_hit_rate` — fraction of snaps with `clv > 0` (market moved toward our view).
- `<intent>.clv_n` — snap count backing the two above.
- `by_edge_source[]` — same `{clv_mean, clv_hit_rate, clv_n}` triple sliced by `edge_source` tag: `[{"edge_source":"news_latency","clv_mean":<n>,"clv_hit_rate":<n>,"clv_n":<n>}, ...]`. CLV is computed unconditionally (no Gamma resolution needed), so these populate days before any Brier does.

`drift_skill` is the legacy single-number seed for `clv_mean` (exploit slice): until `clv_n > 0`, recaps may read `drift_skill`; once CLV snaps exist, `clv_mean` supersedes it.

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
{"forecast_id":"<id>","market_id":"<id>","token_id":"<tid>","learning_intent":"<intent>","edge_source":"<tag>","your_p":<p>,"market_p":<p>,"market_p_t0":<p>,"clv_snaps":[],"close_time":"<iso>","emitted_at":"<iso>","calibration_bucket":"<lo-hi>","resolved":false}
```

**v3 CLV fields** (populated by recalibrate at runtime — never hand-edit this file):
- `market_p_t0` — CLOB midpoint at forecast time (seeded from the forecast's `market_p` on append; the reference all CLV deltas are measured from).
- `edge_source` — copied from the forecast (for per-`edge_source` CLV aggregation); `"none"` if absent.
- `clv_snaps` — array of midpoint snapshots, one per due window:
  ```json
  [{"t":"+6h","market_p":<p>,"ts":"<iso>","clv":<signed>},
   {"t":"+24h","market_p":<p>,"ts":"<iso>","clv":<signed>},
   {"t":"close","market_p":<p>,"ts":"<iso>","clv":<signed>}]
  ```
  A snap is *due* when `now - emitted_at >= window` (close: `now >= close_time`) and that `t` is not yet present. Each window snaps at most once.

`sweep()` compacts by rewriting only `resolved:false` rows (atomic via `.tmp` + `mv`).

## `tick(event)`

Synchronous from `skills/journal` step 4. Must be cheap; must not block the append.

1. Filter event_type to `{forecast, paper_fill, mainnet_fill}`. Else no-op.
2. **`forecast`** (MUST append — this is the open-ledger contract; a missed append is the bug `sweep()` step 0 self-checks): append one line to `state/forecasts.open.jsonl` (`resolved:false`) with `market_p_t0` seeded from the event's `market_p`, `edge_source` copied (else `"none"`), and `clv_snaps:[]`. Skip only if a line with this `forecast_id` already exists (idempotent re-tick). Increment `scorecard.<intent>.unresolved_n`. Bump `updated_at`.
3. **`paper_fill` / `mainnet_fill`**: find parent forecast by `forecast_id` (or `idempotency_key`). Annotate the open-ledger entry with `fill_price`, `fill_shares`, `fill_ts`. Portfolio MTM = `risk.nav()` responsibility, not recalibrate's. A fill with `forecast_id:null` (human restatement — see `skills/journal`) annotates nothing: portfolio-only, excluded from calibration; emit the step-4 `recalibration` event with `status:"skipped_no_forecast_id"`.
4. Emit `recalibration` via `journal` (won't loop — `tick` filters event_type):
   ```json
   {"event_type":"recalibration","trigger":"<event_type>","forecast_id":"<id>","status":"ok","scorecard_path":"state/scorecard.json"}
   ```
5. Return. Heavy lifting (Brier, slope/intercept) deferred to `sweep()`.

## `snap_clv()` — CLV snapshot (the fast-learning pulse)

The cheap recurring CLV step. Runs from **pulse (heartbeat)**, **overnight-watch**, and **daily-close** (`sweep()` calls it first, so daily-close gets it via the sweep). Adds **zero** forecasts and **zero** invocations — it rides cycles we already pay for. CLV needs no Gamma resolution; it reads the live CLOB only.

1. Read `state/forecasts.open.jsonl`, filter `resolved:false`.
2. Select forecasts **due a snap**: some window `t ∈ {+6h,+24h,close}` where (`+6h`/`+24h`: `now - emitted_at >= window`; `close`: `now >= close_time`) AND that `t` is absent from `clv_snaps`. Cap at **≤8 CLOB book calls/cycle** (oldest-emitted first; remainder caught next cycle). Pulse stays cheap.
3. For each due forecast, one `markets.book()` → midpoint `market_p_later`. Compute per due window:
   ```
   clv = (market_p_later - market_p_t0) * sign(your_p - market_p_t0)   # >0 ⇒ market moved toward our view
   ```
   (`sign(0)=0` ⇒ a forecast that matched the market scores `clv=0`, neutral.) Append `{"t":<t>,"market_p":market_p_later,"ts":<now>,"clv":clv}` to that row's `clv_snaps`. One book call covers all windows due for the same forecast this cycle.
4. **Aggregate into scorecard** (across both open + resolved rows' `clv_snaps`):
   - Per intent: `clv_mean = mean(clv)`, `clv_hit_rate = mean(clv > 0)`, `clv_n = count`.
   - Per `edge_source`: same triple into `by_edge_source[]`.
   - Seed: if a slice has `clv_n == 0` but legacy `drift_skill != null`, leave `drift_skill` as the displayed proxy; once `clv_n > 0`, `clv_mean` is authoritative.
5. Atomic write `state/forecasts.open.jsonl` + `state/scorecard.json` (`.tmp` + `mv`). Bump `updated_at`.
6. Emit `recalibration` via `journal`:
   ```json
   {"event_type":"recalibration","trigger":"snap_clv","snaps_new":<n>,"clv_n_exploit":<n>,"clv_n_explore":<n>}
   ```

## `sweep()`

Source-budget aware. Spends Gamma only when open forecasts have passed `close_time`.

0. **Open-ledger self-check (append-bug guard).** Compare `count(forecasts.open.jsonl) + count(forecasts.resolved.jsonl)` against `count(trade-log forecast events)` (`jq -c 'select(.event_type=="forecast")' | wc -l`, plus any rotated into `state/archive/`). On divergence: emit `recalibration status:"ledger_divergence" open_plus_resolved:<n> trade_log_forecasts:<m> delta:<d>` + `notify` (suppression-exempt), then **back-fill** any trade-log `forecast` whose `forecast_id` is missing from both ledgers (reconstruct the open-ledger line per the § state schema, `resolved:false`, `clv_snaps:[]`). This is the recovery path for the historical bug where `tick()` failed to append (e.g. the 05-27 reconstruct).
1. **`snap_clv()`** — take any due CLV snapshots first (so daily-close + overnight-watch refresh CLV every sweep), then continue.
2. Read `state/forecasts.open.jsonl`, filter `resolved:false`.
3. Group open forecasts past `close_time` by `market_id`.
4. Query Gamma (`GET /markets/<market_id>`) for resolution. ≤1 source/cycle. Skip if budget exhausted.
5. For each resolved market: mark all open forecasts on it `resolved:true, outcome:0|1, resolution_ts:<iso>`. Move row to `state/forecasts.resolved.jsonl` (CLV snaps travel with it — resolved rows still feed `clv_mean`).
6. **Recompute scorecard** from trailing 30d resolved:
   - Exploit slice (`learning_intent=="exploit"`):
     - `brier_agent = mean((your_p - outcome)^2)`
     - `brier_market_p = mean((market_p - outcome)^2)`
     - `brier_skill = brier_market_p - brier_agent`
     - `calibration_slope, calibration_intercept` = OLS(outcome ~ your_p)
     - `auc` = rank-AUC, ties=0.5
     - `kl_vs_market = mean(your_p*log(your_p/market_p) + (1-your_p)*log((1-your_p)/(1-market_p)))` (clamped)
     - `drift_skill`: legacy seed for `clv_mean` — fraction of unresolved exploit forecasts whose current midpoint moved toward `your_p` more than toward forecast-time `market_p`. Capped at 5 CLOB book calls/sweep, oldest first. (`snap_clv()` step 1 is now the primary CLV source; `drift_skill` is retained only as the cold-start proxy until `clv_n > 0`.)
   - Explore slice (`learning_intent=="explore"`): same formulas with `your_p = market_p + ε`.
   - **CLV** (`clv_mean`, `clv_hit_rate`, `clv_n` per intent + `by_edge_source[]`) was already refreshed by `snap_clv()` at step 1 — do not recompute, just carry it through.
7. **Recompute calibration** per bucket × intent: `resolved_n`, `hit_rate = mean(outcome)`, `brier`, `adjustment` (per `strategy/current.md` convergent update law). `status = collect` if `n<10`, else `active`.

7b. **Historical prior (cold start).** For any exploit bucket with `resolved_n == 0`: if
   `tools/bootstrap-calibration.json` exists, copy the matching `price_bin` row into the bucket as
   `historical_prior: {n, realized_freq, mean_forecast_p, source:"historical_bootstrap"}`.
   **Reference-only**: it never increments `resolved_n`, never sets `adjustment`, never flips `status` —
   it gives `reflect`/`sizing` a base-rate anchor from 538 resolved Polymarket markets instead of a void
   while live data accumulates. Drop the field once the bucket's live `resolved_n >= 10` (live data
   supersedes the prior). Zero sources — local file read.
8. Per-provider / per-feature_tag slices: filter by exact `source_providers[]` / `feature_tags[]`. Compute Brier vs market baseline.
9. Atomic write `state/scorecard.json`, `state/calibration.json`, `state/forecasts.open.jsonl` via `.tmp` + `mv`.
10. Emit `recalibration` via `journal`:
   ```json
   {"event_type":"recalibration","trigger":"sweep","resolved_new":<n>,"unresolved_total":<n>}
   ```

## Source budget

`tick()` — 0 sources. `snap_clv()` — ≤8 CLOB book calls (CLV snapshots), 0 Gamma. `sweep()` — ≤1 Gamma (resolution), ≤5 CLOB book calls (legacy `drift_skill`), plus its embedded `snap_clv()`. CLOB doesn't count toward research budget. Pulse runs `snap_clv()` only (cheap; ≤8 CLOB, 0 Gamma).

## Failure modes

- `state/forecasts.open.jsonl` corrupted or short → reconstruct from `trade-log.jsonl` (`forecast` events without matching resolution). The `sweep()` step 0 self-check is the routine guard that catches a silent `tick()` append miss and back-fills before it skews CLV/Brier.
- `snap_clv()` book-call fails for a forecast → skip that snap, leave the window unfilled, retry next cycle. Never synthesize a midpoint. A few missed windows only thin `clv_n`.
- Gamma resolution lookup fails → keep `resolved:false`, retry next sweep. Never guess outcomes.
- Lock contention during write → retry once after 100ms, then log `recalibration status:"failed" reason:"lock_contention"`.
- Missing state files on first run → create with empty schema.

## `reflect` integration

Read `state/scorecard.json` + `state/calibration.json` first. Recompute only the slice needed for the current decision (e.g. the simulation in `reflect` step 8). Full scorecard is always fresh because `tick()` ran on every relevant event. Reflection's role narrows to **governance** (snapshot, version bump, regression gate).
