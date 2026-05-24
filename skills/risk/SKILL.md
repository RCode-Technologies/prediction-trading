---
name: risk
description: Pure math — NAV, baseline, freshness, 24h P&L. Does NOT write halts (circuit-breaker owns that) or notify.
inputs: state/portfolio.json, cycle-index.json.nav_snapshots, fresh CLOB midpoints
outputs: returned values; optional in-memory recommendation buffer for notify
---

# Risk

Stateless math helpers. Callers: `circuit-breaker`, `sizing`, `reflect`.

## Helpers

### `nav() → {nav_usdc, cash_usdc, positions_value_usdc, stale_flags[]}`

```
nav_usdc = cash_usdc + Σ position.shares * mark_used
```

Per open position:
- Both sides + quote ≤15 min → use midpoint.
- One side + ≤15 min → use last trade price.
- Else → `stale:true`, use most recent value, append `{token_id, reason}` to `stale_flags`.

### `baseline_nav() → {nav_usdc, source} | null`

- Most recent `nav_snapshots[i]` with `ts <= now - 24h` → source `"snapshot"`.
- Else `portfolio.starting_capital` → source `"starting_capital"`.
- Else `null` → caller (`circuit-breaker`) → `halt("no_baseline_nav")`.

### `rolling_24h_pnl() → {current, baseline, pnl_usdc, pnl_pct, source}`

`current - baseline` + pct.

### `freshness_summary() → {total_positions, stale_count, stale_ratio}`

`circuit-breaker.evaluate()` uses `stale_ratio > 0.5` to skip the breaker check.

## Guardrail recommendation buffer

`reflect` may want to suggest a `guardrails.md` change (which it can't edit). Calls `risk.surface_recommendation(text)`; in-memory buffer for this cycle. `notify` reads it when composing `daily_summary` and embeds a "Guardrail recommendation for human review" section if non-empty. Not persisted as its own file.

## Deposit/withdrawal detection

v1 has no deposit/withdrawal path. `detect_unreconciled_cash_delta()` is called by `circuit-breaker.evaluate()`; unexplained delta → `halt("unreconciled_cash_delta")`.

## Failure modes

- Missing `state/portfolio.json` → raise to caller (boot should have caught it).
- CLOB book call fails → mark position stale, continue.
