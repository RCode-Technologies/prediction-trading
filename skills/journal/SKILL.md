---
name: journal
description: Append-only event log writer to state/trade-log.jsonl + markdown notes. Single canonical writer. Post-append hook drives skills/recalibrate.
inputs: event_type + payload, or markdown path + body
outputs: appended JSONL line, optional markdown file, {event_id, line_number}
---

# Journal

Only skill that *appends* to `state/trade-log.jsonl`. Append-only here. The sole exception is
`skills/groom`, which may *rotate* (rewrite) the file weekly — atomic, no-drop, archived to
`state/archive/`. No other skill rewrites it.

## Envelope (auto-filled if absent)

```json
{"schema_version":1,"event_id":"<cid>-<event_type>-<seq>","cycle_id":"<cid>","event_type":"...","ts":"<iso8601 UTC>","mode":"paper|mainnet","phase":"..."}
```

Caller fields merged in.

**Trade events also need:** `market_id`, `condition_id`, `token_id`, `outcome`, `side`, `price`, `shares`, `notional_usdc`, `fee_usdc`, `idempotency_key`, `order_id` (null in paper). **SELL fills additionally require non-null `realized_pnl_usdc` = `shares × (fill_price − avg_entry_price)`** — recap/reflect read it from JSONL; a null breaks exit-P&L attribution (the 2026-05-29 Iran exit logged null and had to be reconstructed).

**Human restatement fills** (capital-integrity corrections booked interactively, e.g. the 2026-06-10 baseline-injection restatement) carry `authorized_by:"<handle>_interactive_recovery"` and may have `forecast_id:null`. They are portfolio-ledger events only — excluded from calibration (`recalibrate.tick` skips fills without a `forecast_id`).

**Forecast events also need:** `strategy_version`, `forecast_id`, `thesis_id`, `evidence_refs`, `feature_tags`, `source_providers`, `prior_p`, `raw_your_p`, `your_p`, `market_p`, `confidence`, `calibration_bucket`, `close_time`, `resolution_criteria`, `disconfirming_signals`, **`learning_intent ∈ {"explore","exploit","risk_reduction"}`**.

**v3 forecast gate/cost fields (also mandatory; produced by `skills/markets` book + `skills/sizing` gate, defined in `strategy/current.md` § Edge gate):**
- `resolution_criteria` — parsed from the Gamma market `description` (already listed; v3 makes it non-empty for exploit).
- `resolution_parsed` (bool) — true once `description` is fetched + parsed.
- `reference_class` (string|null) — named base-rate class; null on explore.
- `edge_source` (enum) — category-neutral signal tag ∈ {`news_latency`,`base_rate`,`structural`,`sentiment`,`none`}.
- `best_bid`, `best_ask`, `spread` — from `markets.book()` (cost-honest; never midpoint).
- `edge_net` — `your_p − best_ask` (YES BUY); the only edge the gate scores.
- `sizing_tier` (int 0–3) — conviction tier; default/stub `0` until the Phase 5 ladder.

Exploit forecasts MUST carry `resolution_parsed:true` + non-empty `resolution_criteria` + `reference_class != null` + `source_providers` len ≥ 2 (else `skills/sizing` demotes to explore). Explore forecasts may have `reference_class:null`, `edge_source:"none"`.

**Decision events:** at minimum `forecast_id`, `strategy_version`, `thesis_id`, `feature_tags`, `learning_intent`, `sizing_tier`. Gate-miss decisions carry `reason ∈ {resolution_unparsed, no_reference_class, insufficient_sources, edge_below_net_threshold}` + `shares:0`.

Never bury attribution in markdown — reflection reads JSONL.

## Allowed `event_type`

`cycle_start`, `stale_lock_recovered`, `research_note`, `candidate_rank`, `forecast`, `decision`, `decision_cleared`, `paper_fill`, `mainnet_order_submitted`, `mainnet_fill`, `nav_snapshot`, `halt`, `reflection`, `notification`, `preflight_failed`, `persist_conflict`, `cycle_end`, `recap`, `phase_completed`, `phase_missed`, `null_cycle` (v2), `liveness_gap` (v2), `recalibration` (v2), `groom` (v3), `vision` (v3), `proposal` (v3), `enactment` (v3), `deposit` (v3), `withdrawal` (v3).

## Steps

1. Fill envelope. `event_id` seq = count of this event_type for `cycle_id` (start 1).
2. Validate: `printf '%s\n' "$json" | jq empty`. Reject malformed. For `forecast` **and `decision`**: assert `.learning_intent ∈ {"explore","exploit","risk_reduction"}`; else reject (caller bug). For `paper_fill`/`mainnet_fill` with `side:"SELL"`: assert `realized_pnl_usdc` present and non-null; else reject.
3. Append via `>>`. POSIX-atomic. Never partial writes.
4. **Post-append hook.** event_type ∈ `{forecast, paper_fill, mainnet_fill}` → invoke `skills/recalibrate.tick(event)` synchronously. (Decisions don't trigger; the matching fill will.) Hook failure MUST NOT roll back the append — log a `recalibration status:"failed" reason:"<short>"` and continue.
5. Markdown notes (research/candidates/watchlists/recaps): write via temp + `mv`. JSONL event carries path + metadata only.

## Failure modes

- Disk full → retry once → raise.
- Malformed payload → reject (caller bug).
- Duplicate `event_id` → reject (caller miscounted).

## Read helpers (callers grep directly)

```bash
jq -c 'select(.cycle_id=="<id>")'      state/trade-log.jsonl
jq -c 'select(.event_type=="forecast")' state/trade-log.jsonl
jq -c 'select(.phase=="trade_window")'  state/trade-log.jsonl
```
