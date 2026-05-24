---
name: circuit-breaker
description: Owns the breaker decision + write. Two entrypoints: evaluate() and halt(reason). Invoked at checkpoints inside every routine and by skills/trade on internal failures.
inputs: state/portfolio.json, cycle-index.json.nav_snapshots, halts.json, optional forced reason
outputs: halts.json (on trip), halt event, optional notify
---

# Circuit Breaker

Not a routine. `skills/risk` provides the math; this skill owns the decision and writes `halts.json`.

## Entrypoints

- `evaluate()` — compute rolling 24h P&L, fire halt if breach.
- `halt(reason)` — force halt for non-loss triggers.

## Checkpoints

| routine | checkpoints |
| --- | --- |
| `research-window` | (1) post-boot |
| `trade-window` | (1) post-boot, (2) post-marks, (3) post-fill, (4) post-final-snapshot |
| `daily-close` | (1) post-boot, (2) post-marks, (3) post-final-snapshot, (4) post-recap |
| `overnight-watch` | (1) post-boot, (2) post-marks, (3) post-opportunistic-fill |

Any fire → routine stops phase work, calls `notify` + `persist` to commit + push halt.

## Triggers

### Loss (`evaluate()`)
- `current = risk.nav()` (cash + Σ shares * fresh_mark).
- `baseline = nav_snapshots[i]` with most recent `ts <= now - 24h`. Else `portfolio.starting_capital`.
- Fire when `(current - baseline) / baseline <= -0.10`.

### Forced (`halt(reason)`)

| reason | source |
| --- | --- |
| `mainnet_cancel_failed` | `trade` partial fill, cancel of remainder failed |
| `post_submit_push_failed` | `trade` post-submit push failed |
| `no_baseline_nav` | no snapshots and no `starting_capital` |
| `unreconciled_cash_delta` | `evaluate` saw unexplained cash movement (v1 has no deposit/withdrawal path) |
| `push_permission_missing` | `persist` push preflight failed |
| `manual_pause` | human-set, not auto |
| `stale_marks_skip_breaker` | NOT a halt — `evaluate` emits `preflight_failed` when >50% positions stale |

## `evaluate()` steps

1. `halts.json.active==true` → `{halted:true, already_active:true}`.
2. **Cash reconciliation.** `risk.detect_unreconciled_cash_delta()`. If unexplained delta (cash change not accounted for by logged fills + fees since last `nav_snapshot`) → `halt("unreconciled_cash_delta", delta_usdc)`. Run **before** NAV/baseline math so a corrupted cash figure never reaches the PnL trigger.
3. `risk.nav()`. If `stale_ratio > 0.5` → emit `preflight_failed reason:"stale_marks_skip_breaker"` via `journal`, return `{halted:false, degraded:true}`.
4. No baseline → `halt("no_baseline_nav")`.
5. `pnl_pct = (current - baseline) / baseline`. If ≤ -0.10 → `halt("24h_loss_exceeds_10pct", pnl_pct, baseline, current)`.
6. Else return `{halted:false, pnl_pct, baseline, current}`.

## `halt(reason, ...)` steps

1. Atomic write `halts.json`:
   ```json
   {"schema_version":1,"active":true,"reason":"<reason>","triggered_at":"<now>","cycle_id":"<cid>"}
   ```
2. `journal` emit `halt`:
   ```json
   {"event_type":"halt","reason":"<r>","baseline_nav":<n>,"current_nav":<n>,"pnl_usdc":<n>,"pnl_pct":<p>}
   ```
   Loss-related fields null for non-loss reasons.
3. `notify` kind `circuit_breaker` (sent in paper + mainnet).
4. Return `{halted:true, reason}`. Routine then `persist`s with `fix(halt): <reason> [cycle <cid>]`.

## Recovery (human-only)

Agent **never** clears. Human edits `halts.json`:
```bash
jq '.active=false | .reason=null | .triggered_at=null | .cycle_id=null' \
   state/halts.json > state/halts.json.tmp && mv state/halts.json.tmp state/halts.json
git add state/halts.json && git commit -m "chore(halt): cleared by <handle>" && git push origin main
```

## Failure modes

- Can't write `halts.json` → retry once → notify if possible → abort. Next cycle retries.
- No `cycle-index.json` / empty `nav_snapshots` → treat as cold start (use `starting_capital`).
