---
name: circuit-breaker
description: Owns the breaker decision + write. evaluate() and halt(reason). Invoked at checkpoints inside every routine and by skills/trade on internal failures.
inputs: state/portfolio.json, cycle-index.json.nav_snapshots, halts.json, optional forced reason
outputs: halts.json (on trip), halt event, optional notify
---

# Circuit Breaker

`skills/risk` provides the math; this skill owns the decision and writes `halts.json`.

## Entrypoints

- `evaluate()` — rolling 24h P&L **+ drawdown-from-peak governors + portfolio-heat breach** (v3), fire halt/governor on breach.
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

### Loss (`evaluate()`) — catastrophic 24h hard halt (UNCHANGED)
- `current = risk.nav()` (cash + Σ shares * fresh_mark).
- `baseline = nav_snapshots[i]` most recent `ts <= now - 24h`. Else `portfolio.starting_capital`.
- Fire when `(current - baseline) / baseline <= -0.10`.

### Drawdown-from-peak governors (`evaluate()`; v3 — primary equity control)

`risk.drawdown_from_peak()` (current vs `peak_nav`, both liquidation-marked; `config/guardrails.md` § Equity governors):
- `drawdown_pct <= -0.15` → **forecast-only freeze**: `halt("drawdown_freeze_15pct", drawdown_pct, peak, current)`. New capital risk stops (every candidate → Tier 0); **human review to resume**. Exits (`risk_reduction`) still allowed.
- `-0.15 < drawdown_pct <= -0.08` → **probation** (NOT a halt): emit `preflight_failed reason:"governor_probation"` + `notify`, return `{halted:false, probation:true, sizing_mult:0.5, drawdown_pct}`. `sizing` applies `sizing_mult:0.5`. Lifts automatically when NAV recovers above the −8% line.

### Portfolio-heat breach (`evaluate()`; v3)

`risk.portfolio_heat()` (`config/guardrails.md` § Portfolio heat):
- `heat_pct > 0.25` OR `bucket_count > 4` → **NOT a halt**: emit `preflight_failed reason:"governor_heat_breach"` + `notify`, return `{halted:false, heat_breach:true, heat_pct, bucket_count}`. `sizing` rejects **new** exploits while breached (existing positions ride; exits always allowed). Surfaces the book is over-concentrated so a stale-marked tail can be caught under the per-token cap.

### Forced (`halt(reason)`)

| reason                     | source                                                  |
| -------------------------- | ------------------------------------------------------- |
| `mainnet_cancel_failed`    | `trade` partial fill, cancel of remainder failed        |
| `post_submit_push_failed`  | `trade` post-submit push failed                         |
| `no_baseline_nav`          | no snapshots and no `starting_capital`                  |
| `unreconciled_cash_delta`  | unexplained cash movement (v1 has no deposit/withdraw)  |
| `push_permission_missing`  | `persist` push preflight failed                         |
| `protected_core_violation` | `boot`/`persist` — agent-authored change to a protected-core file (`config/autonomy.md`) |
| `nav_reconciliation_failed` | `boot` (v3, AC #13) — `\|expected_cash − cash_usdc\| > $0.01` vs `starting_capital` ± logged fills/deposits/withdrawals, or a position's shares moved with no corresponding fill. Positions are never scaled to fit a baseline. |
| `manual_pause`             | human-set                                               |
| `drawdown_freeze_15pct`    | `evaluate()` — NAV ≤ −15% from peak; forecast-only freeze, human review to resume (v3) |
| `stale_marks_skip_breaker` | NOT a halt — emits `preflight_failed` when >50% stale   |
| `governor_probation`       | NOT a halt — `evaluate()` emits `preflight_failed` at −8% from peak; sizing × 0.5 (v3) |
| `governor_heat_breach`     | NOT a halt — `evaluate()` emits `preflight_failed` when heat > 25% or > 4 buckets; sizing rejects new exploits (v3) |

## `evaluate()`

1. `halts.json.active==true` → `{halted:true, already_active:true}`.
2. **Cash reconciliation** via `risk.detect_unreconciled_cash_delta()`. Unexplained delta → `halt("unreconciled_cash_delta", delta_usdc)`. Run **before** NAV math so corrupted cash can't reach the PnL trigger.
3. `risk.nav()`. `stale_ratio > 0.5` → emit `preflight_failed reason:"stale_marks_skip_breaker"`, return `{halted:false, degraded:true}`.
4. No baseline → `halt("no_baseline_nav")`.
5. `pnl_pct = (current - baseline) / baseline`. ≤ -0.10 → `halt("24h_loss_exceeds_10pct", pnl_pct, baseline, current)`. **(Catastrophic hard halt — unchanged.)**
6. **Drawdown-from-peak governor (v3).** `dd = risk.drawdown_from_peak().drawdown_pct`.
   - `dd <= -0.15` → `halt("drawdown_freeze_15pct", dd, peak, current)` (forecast-only freeze; human review to resume; exits stay allowed).
   - `-0.15 < dd <= -0.08` → emit `preflight_failed reason:"governor_probation"` + `notify`; return `{halted:false, probation:true, sizing_mult:0.5, drawdown_pct:dd, peak, current}`. (Not a halt — half-size sizing continues; lifts when NAV recovers above the −8% line.)
7. **Portfolio-heat breach (v3).** `h = risk.portfolio_heat()`. `h.heat_pct > 0.25` OR `h.bucket_count > 4` → emit `preflight_failed reason:"governor_heat_breach"` + `notify`; return `{halted:false, heat_breach:true, heat_pct:h.heat_pct, bucket_count:h.bucket_count, ...}`. (Not a halt — `sizing` rejects new exploits while breached; existing positions ride; exits allowed.)
8. Else `{halted:false, pnl_pct, baseline, current, drawdown_pct:dd, heat_pct:h.heat_pct}`.

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

Agent never clears. While the halt is active: `boot` re-notifies `halt_active` once per UTC date
(date-deduped, suppression-exempt) — an ongoing halt is never silent — and routines still run their
read-only `recalibrate` step (a halt stops capital actions, not calibration). Human edits `halts.json`:
```bash
jq '.active=false|.reason=null|.triggered_at=null|.cycle_id=null' \
   state/halts.json > state/halts.json.tmp && mv state/halts.json.tmp state/halts.json
git add state/halts.json && git commit -m "chore(halt): cleared by <handle>" && git push
```

## Failure modes

- Can't write `halts.json` → retry once → notify → abort. Next cycle retries.
- No `cycle-index.json` / empty `nav_snapshots` → treat as cold start (use `starting_capital`).
