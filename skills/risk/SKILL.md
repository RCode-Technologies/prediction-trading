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
nav_usdc = cash_usdc + Σ position.shares * mark_liquidation
```

**Cost-honest (v3):** NAV marks longs at **liquidation value = `best_bid`** (what you'd actually receive selling now), never midpoint. Per position store both:
- `mark_mid` = `(best_bid + best_ask)/2` — reference / display only.
- `mark_liquidation` = `best_bid` for a long (the SELL-side executable price). **NAV, the 5% cap, and the breaker all use `mark_liquidation`.**

Per position freshness:
- Both sides + quote ≤15min → `best_bid` (liquidation) + `best_bid`/`best_ask` for `mark_mid`.
- One side + ≤15min → last trade (use for both marks; flag thin).
- Else → `stale:true`, use most recent, append `{token_id, reason}` to `stale_flags`.

### `baseline_nav() → {nav_usdc, source} | null`

- Most recent `nav_snapshots[i]` with `ts <= now - 24h` → source `"snapshot"`.
- Else `portfolio.starting_capital` → source `"starting_capital"`.
- Else `null` → caller halts `no_baseline_nav`.

### `rolling_24h_pnl() → {current, baseline, pnl_usdc, pnl_pct, source}`

### `peak_nav() → {peak_nav_usdc, ts}`

Max NAV over history: `max(nav_snapshots[].nav_usdc, current_nav)`. Empty snapshots → `starting_capital`. All values liquidation-marked (longs at `best_bid`). Used by the drawdown-from-peak governors.

### `drawdown_from_peak() → {current, peak, drawdown_pct}` (v3)

```
drawdown_pct = (current_nav - peak_nav) / peak_nav          # ≤ 0
```

`circuit-breaker` reads it for the −8% probation / −15% freeze governors (`config/guardrails.md` § Equity governors). `current` from `nav()` (liquidation-marked); `peak` from `peak_nav()`.

### `portfolio_heat() → {heat_pct, bucket_count, buckets[]}` (v3)

```
heat_pct = Σ_open (position.shares * mark_liquidation) / nav_usdc          # current liquidation-risk / NAV
```

Aggregates correlated positions into one bucket per § Correlation (`bucket_count` = distinct uncorrelated buckets). `circuit-breaker` (heat-breach trigger) and `sizing` (pre-fill heat check + Tier-3 `heat < 0.10` gate) both read it. Stale marks flow through `nav()`'s `stale_flags`.

### `pnl_from_entry(position) → {pnl_pct, pnl_usdc, mark_liquidation, avg_price}` (v3)

Per-position mark-from-entry, for the disconfirmation stop:

```
pnl_pct  = (mark_liquidation - position.avg_price) / position.avg_price    # long; ≤ -0.25 ⇒ stop
pnl_usdc = position.shares * (mark_liquidation - position.avg_price)
```

`mark_liquidation = best_bid` (the SELL-side executable price — what you'd actually realise). Stale book → flag stale, return last good mark (caller decides; the stop does not fire on a stale mark alone).

### `freshness_summary() → {total_positions, stale_count, stale_ratio}`

`circuit-breaker` uses `stale_ratio > 0.5` to skip the loss check.

### `detect_unreconciled_cash_delta()`

Cash change not accounted for by logged fills + fees since last `nav_snapshot` → `circuit-breaker.halt("unreconciled_cash_delta")`. v1 has no deposit/withdrawal path.

## Guardrail recommendation buffer

`reflect` may want a `guardrails.md` change (can't edit). `risk.surface_recommendation(text)` → in-memory buffer for this cycle. `notify` reads it when composing `daily_summary`.

## Failure modes

- Missing `state/portfolio.json` → raise (boot should have caught).
- CLOB book call fails → mark position stale, continue.
