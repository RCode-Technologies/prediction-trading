---
name: circuit-breaker
description: Owns the breaker decision + write. evaluate() and halt(reason). Invoked at checkpoints inside every routine and by skills/trade on internal failures.
inputs: state/portfolio.json, cycle-index.json.nav_snapshots, halts.json, optional forced reason
outputs: halts.json (on trip), halt event, optional notify
---

# Circuit Breaker

`skills/risk` provides the math; this skill owns the decision and writes `halts.json`.

## Entrypoints

- `evaluate()` — rolling 24h P&L, fire halt on breach.
- `halt(reason)` — force halt for non-loss triggers.

## Checkpoints

| routine            | checkpoints                                                          |
| ------------------ | -------------------------------------------------------------------- |
| `research-window`  | post-boot                                                            |
| `trade-window`     | post-boot, post-marks, post-fill, post-final-snapshot                |
| `daily-close`      | post-boot, post-marks, post-final-snapshot, post-recap               |
| `overnight-watch`  | post-boot, post-marks, post-opportunistic-fill                       |

Any fire → routine stops phase work, calls `notify` + `persist` to commit + push halt.

## Triggers

### Loss (`evaluate()`)
- `current = risk.nav()` (cash + Σ shares * fresh_mark).
- `baseline = nav_snapshots[i]` most recent `ts <= now - 24h`. Else `portfolio.starting_capital`.
- Fire when `(current - baseline) / baseline <= -0.10`.

### Forced (`halt(reason)`)

| reason                     | source                                                  |
| -------------------------- | ------------------------------------------------------- |
| `mainnet_cancel_failed`    | `trade` partial fill, cancel of remainder failed        |
| `post_submit_push_failed`  | `trade` post-submit push failed                         |
| `no_baseline_nav`          | no snapshots and no `starting_capital`                  |
| `unreconciled_cash_delta`  | unexplained cash movement (v1 has no deposit/withdraw)  |
| `push_permission_missing`  | `persist` push preflight failed                         |
| `manual_pause`             | human-set                                               |
| `stale_marks_skip_breaker` | NOT a halt — emits `preflight_failed` when >50% stale   |

## `evaluate()`

1. `halts.json.active==true` → `{halted:true, already_active:true}`.
2. **Cash reconciliation** via `risk.detect_unreconciled_cash_delta()`. Unexplained delta → `halt("unreconciled_cash_delta", delta_usdc)`. Run **before** NAV math so corrupted cash can't reach the PnL trigger.
3. `risk.nav()`. `stale_ratio > 0.5` → emit `preflight_failed reason:"stale_marks_skip_breaker"`, return `{halted:false, degraded:true}`.
4. No baseline → `halt("no_baseline_nav")`.
5. `pnl_pct = (current - baseline) / baseline`. ≤ -0.10 → `halt("24h_loss_exceeds_10pct", pnl_pct, baseline, current)`.
6. Else `{halted:false, pnl_pct, baseline, current}`.

## `halt(reason, ...)`

1. Atomic write `halts.json`:
   ```json
   {"schema_version":1,"active":true,"reason":"<r>","triggered_at":"<now>","cycle_id":"<cid>"}
   ```
2. `journal` emit `halt` (loss fields null for non-loss reasons):
   ```json
   {"event_type":"halt","reason":"<r>","baseline_nav":<n>,"current_nav":<n>,"pnl_usdc":<n>,"pnl_pct":<p>}
   ```
3. `notify` kind `circuit_breaker` (paper + mainnet).
4. Return `{halted:true, reason}`. Routine persists with `fix(halt): <reason> [cycle <cid>]`.

## Recovery (human-only)

Agent never clears. Human edits `halts.json`:
```bash
jq '.active=false|.reason=null|.triggered_at=null|.cycle_id=null' \
   state/halts.json > state/halts.json.tmp && mv state/halts.json.tmp state/halts.json
git add state/halts.json && git commit -m "chore(halt): cleared by <handle>" && git push
```

## Failure modes

- Can't write `halts.json` → retry once → notify → abort. Next cycle retries.
- No `cycle-index.json` / empty `nav_snapshots` → treat as cold start (use `starting_capital`).
