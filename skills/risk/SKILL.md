---
name: risk
description: Pure math — NAV, baseline, freshness, 24h P&L. Does NOT write halts or notify.
inputs: state/portfolio.json, cycle-index.json.nav_snapshots, fresh CLOB midpoints
outputs: returned values; optional in-memory recommendation buffer for notify
---

# Risk

Stateless. Callers: `circuit-breaker`, `sizing`, `reflect`.

## Helpers

### `nav() → {nav_usdc, cash_usdc, positions_value_usdc, stale_flags[]}`

```
nav_usdc = cash_usdc + Σ position.shares * mark_used
```

Per position:
- Both sides + quote ≤15min → midpoint.
- One side + ≤15min → last trade.
- Else → `stale:true`, use most recent, append `{token_id, reason}` to `stale_flags`.

### `baseline_nav() → {nav_usdc, source} | null`

- Most recent `nav_snapshots[i]` with `ts <= now - 24h` → source `"snapshot"`.
- Else `portfolio.starting_capital` → source `"starting_capital"`.
- Else `null` → caller halts `no_baseline_nav`.

### `rolling_24h_pnl() → {current, baseline, pnl_usdc, pnl_pct, source}`

### `freshness_summary() → {total_positions, stale_count, stale_ratio}`

`circuit-breaker` uses `stale_ratio > 0.5` to skip the loss check.

### `detect_unreconciled_cash_delta()`

Cash change not accounted for by logged fills + fees since last `nav_snapshot` → `circuit-breaker.halt("unreconciled_cash_delta")`. v1 has no deposit/withdrawal path.

## Guardrail recommendation buffer

`reflect` may want a `guardrails.md` change (can't edit). `risk.surface_recommendation(text)` → in-memory buffer for this cycle. `notify` reads it when composing `daily_summary`.

## Failure modes

- Missing `state/portfolio.json` → raise (boot should have caught).
- CLOB book call fails → mark position stale, continue.
