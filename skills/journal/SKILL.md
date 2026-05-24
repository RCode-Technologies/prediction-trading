---
name: journal
description: Append-only event logging to state/trade-log.jsonl plus markdown notes. Single canonical writer for the agent's reasoning trail. All other skills emit events through this skill.
inputs: event_type + payload, or markdown path + body
outputs: appended JSONL line, optional markdown file
---

# Journal

Single canonical entry point for writing to the agent's memory trail.
Append-only. No skill outside this one touches `state/trade-log.jsonl`
directly.

## Event envelope

Every JSONL line is one JSON object with these **base fields** (auto-filled
by this skill if absent):

```json
{
  "schema_version": 1,
  "event_id": "<cycle_id>-<event_type>-<sequence>",
  "cycle_id": "<cycle_id>",
  "event_type": "<one of allowed types>",
  "ts": "<iso8601 UTC>",
  "mode": "<paper|mainnet>",
  "phase": "<pre_market|market_open|midday|end_of_day|circuit_breaker>"
}
```

Caller-supplied fields are merged in. Trade-related events additionally
require: `market_id`, `condition_id`, `token_id`, `outcome`, `side`,
`price`, `shares`, `notional_usdc`, `fee_usdc`, `idempotency_key`,
`order_id` (null in paper).

Forecast events must also carry enough structure for later learning:
`strategy_version`, `forecast_id`, `thesis_id`, `evidence_refs`,
`feature_tags`, `source_providers`, `prior_p`, `raw_your_p`, `your_p`,
`market_p`, `confidence`, `calibration_bucket`, `close_time`,
`resolution_criteria`, and `disconfirming_signals`. Decision events must at
minimum include `forecast_id`, `strategy_version`, `thesis_id`, and
`feature_tags` when they originate from a forecast. Do not bury these fields
only in markdown; reflection reads the JSONL first.

## Allowed `event_type` values (v1)

`cycle_start`, `stale_lock_recovered`, `research_note`, `candidate_rank`,
`forecast`, `decision`, `paper_fill`, `mainnet_order_submitted`,
`mainnet_fill`, `nav_snapshot`, `halt`, `reflection`, `notification`,
`preflight_failed`, `persist_conflict`, `cycle_end`, `recap`,
`phase_completed`, `phase_missed`.

## Steps

1. **Fill envelope.** Inject `schema_version`, `cycle_id`, `ts`, `mode`,
   `phase`. Compute `event_id` by counting existing events of this type for
   this `cycle_id` (sequence starts at 1).

2. **Validate.** `printf '%s\n' "$json" | jq empty` must succeed. Reject
   malformed payloads (do not silently truncate).

3. **Append** with a single `>>` to `state/trade-log.jsonl`. Atomic by
   POSIX — never use intermediate writes that could half-write a line.

4. **Markdown notes.** For research / candidates / watchlists / recaps,
   write the file via temp + `mv`. Do **not** include this body in JSONL —
   the JSONL event carries only the path + metadata.

## Outputs to caller

`{event_id, line_number}`.

## Failure modes

- **Disk full / write fail:** retry once. If still failing, raise to caller
  so the cycle can abort gracefully via `persist` skill.
- **Malformed payload:** reject; do not write. Caller bug — surface clearly.
- **Trade-log already has identical `event_id`:** reject; caller miscounted
  the sequence.

## Read helpers

Callers may grep the trade-log directly for filters (this skill is the
writer; reads are a one-liner):

```bash
jq -c 'select(.cycle_id=="<id>")'      state/trade-log.jsonl
jq -c 'select(.event_type=="forecast")' state/trade-log.jsonl
jq -c 'select(.phase=="market_open")'   state/trade-log.jsonl
```
