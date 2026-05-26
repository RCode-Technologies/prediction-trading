---
name: journal
description: Append-only event logging to state/trade-log.jsonl + markdown notes. Single canonical writer.
inputs: event_type + payload, or markdown path + body
outputs: appended JSONL line, optional markdown file, {event_id, line_number}
---

# Journal

Only skill that writes `state/trade-log.jsonl`. Append-only.

## Envelope (auto-filled if absent)

```json
{"schema_version":1, "event_id":"<cid>-<event_type>-<seq>", "cycle_id":"<cid>", "event_type":"...", "ts":"<iso8601 UTC>", "mode":"paper|mainnet", "phase":"..."}
```

Caller fields merged in.

**Trade events also need:** `market_id`, `condition_id`, `token_id`, `outcome`, `side`, `price`, `shares`, `notional_usdc`, `fee_usdc`, `idempotency_key`, `order_id` (null in paper).

**Forecast events also need:** `strategy_version`, `forecast_id`, `thesis_id`, `evidence_refs`, `feature_tags`, `source_providers`, `prior_p`, `raw_your_p`, `your_p`, `market_p`, `confidence`, `calibration_bucket`, `close_time`, `resolution_criteria`, `disconfirming_signals`, **`learning_intent` (v2, mandatory: `"explore" | "exploit" | "risk_reduction"`)**.

**Decision events from a forecast:** at minimum `forecast_id`, `strategy_version`, `thesis_id`, `feature_tags`, `learning_intent`.

Do not bury attribution in markdown — reflection reads JSONL.

## Allowed `event_type` (v2)

`cycle_start`, `stale_lock_recovered`, `research_note`, `candidate_rank`, `forecast`, `decision`, `decision_cleared`, `paper_fill`, `mainnet_order_submitted`, `mainnet_fill`, `nav_snapshot`, `halt`, `reflection`, `notification`, `preflight_failed`, `persist_conflict`, `cycle_end`, `recap`, `phase_completed`, `phase_missed`, **`null_cycle`** (v2 — routine missed its action floor), **`liveness_gap`** (v2 — scheduler skipped one or more cycles), **`recalibration`** (v2 — incremental scorecard update by `skills/recalibrate`).

## Steps

1. Fill envelope. `event_id` seq = count of events of this type for `cycle_id` (start 1).
2. Validate: `printf '%s\n' "$json" | jq empty`. Reject malformed. For `forecast` events, also assert `.learning_intent` ∈ `{"explore","exploit","risk_reduction"}`; missing/invalid → reject as caller bug.
3. Append with `>>`. Atomic by POSIX. Never partial writes.
4. **Post-append hook (v2).** If the appended event_type ∈ `{forecast, paper_fill, mainnet_fill}`, invoke `skills/recalibrate.tick(event)` synchronously. `decision` events do not trigger the hook (no learning data in them; the matching fill will). Failure in the hook MUST NOT roll back the append — log a `recalibration` event with `status:"failed", reason:"<short>"` and continue.
5. Markdown notes (research/candidates/watchlists/recaps): write via temp + `mv`. JSONL event carries path + metadata only.

## Failure modes

- Disk full → retry once → raise to caller.
- Malformed payload → reject (caller bug).
- Duplicate `event_id` → reject (caller miscounted).

## Read helpers (callers grep directly)

```bash
jq -c 'select(.cycle_id=="<id>")'      state/trade-log.jsonl
jq -c 'select(.event_type=="forecast")' state/trade-log.jsonl
jq -c 'select(.phase=="trade_window")'  state/trade-log.jsonl
```
