---
name: risk
description: Pure math helpers for NAV computation, mark-price freshness, and rolling P&L. Does not write halts (that's skills/circuit-breaker). Also surfaces guardrail-recommendation hints for the human via the daily summary.
inputs: state/portfolio.json, state/cycle-index.json.nav_snapshots, fresh CLOB midpoints
outputs: returned values (no file writes); optional recommendation buffer for skills/notify
---

# Risk

Math + freshness helpers. Pure functions where possible. Callers:
`skills/circuit-breaker` (for breaker evaluation), `skills/sizing` (for NAV
in the 5% cap formula), `skills/reflect` (for hit-rate / Brier context).

## Public helpers

### `nav() -> {nav_usdc, cash_usdc, positions_value_usdc, stale_flags[]}`

```
nav_usdc = cash_usdc + Σ position.shares * fresh_mark_price
```

A "fresh mark" is a CLOB midpoint whose quote timestamp is ≤15 min old.
For each open position:

- If both sides exist and quote ≤15 min: use midpoint.
- If one side, ≤15 min: use last trade price.
- Otherwise: mark `stale: true` for that position, use most recent value,
  append `{token_id, reason}` to `stale_flags`.

`positions_value_usdc` = `Σ position.shares * mark_used`.

### `baseline_nav() -> {nav_usdc, source} | null`

- Most recent `nav_snapshots[i]` with `ts <= now - 24h`. Source =
  `"snapshot"`.
- Else: `portfolio.starting_capital`. Source = `"starting_capital"`.
- Else: `null` (cold start with no seed). Caller (`circuit-breaker`)
  treats this as `no_baseline_nav` and forces a halt.

### `rolling_24h_pnl() -> {current, baseline, pnl_usdc, pnl_pct, source}`

Wrapper: returns `nav().nav_usdc - baseline_nav().nav_usdc` plus the
percentage. `source` carried through from `baseline_nav()`.

### `freshness_summary() -> {total_positions, stale_count, stale_ratio}`

Used by `circuit-breaker.evaluate()` to decide whether to skip a breaker
check (`stale_ratio > 0.5` → skip + emit `preflight_failed` with
`stale_marks_skip_breaker`).

## Guardrail-recommendation surface

`reflect` may identify changes to `config/guardrails.md` it cannot apply
itself (ADR 0005). It calls `risk.surface_recommendation(text)`. The
function appends to an in-memory buffer for the current cycle. `notify`
reads the buffer when composing the daily summary and embeds a
"Guardrail recommendation for human review" section if non-empty.

This buffer is not persisted as its own file; the recommendation lives
inside the daily-summary Telegram message and the daily `recaps/` file.

## Deposit / withdrawal detection

v1 has no deposit/withdrawal pathway. If `cash_usdc` changes
unexpectedly between cycles (delta unexplained by logged fills + fees),
`risk` exposes a `detect_unreconciled_cash_delta()` helper that
`circuit-breaker.evaluate()` calls; on detected mismatch, it forces
`halt("unreconciled_cash_delta")` for human reconciliation.

## What this skill does NOT do

- Does **not** write `state/halts.json` — `skills/circuit-breaker` owns
  that.
- Does **not** send Telegram — `skills/notify` owns that.
- Does **not** decide to trade or not — `skills/sizing` owns that.

Keep this skill mathematically pure: stateless calls returning structured
values.

## Failure modes

- **Missing `state/portfolio.json`:** raise to caller. Boot validation
  should have caught this earlier.
- **CLOB book call fails for a position:** mark that position stale,
  continue. The freshness summary will reflect this.
