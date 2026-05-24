---
name: circuit-breaker
description: Evaluates the 24h loss circuit breaker and writes halts. Invoked at multiple checkpoints inside every routine — after boot, after any operation that may move NAV, and at end-of-cycle. Also exposes a forced-halt entrypoint for non-loss triggers (mainnet cancel failure, post-submit push failure).
inputs: state/portfolio.json, state/cycle-index.json.nav_snapshots, state/halts.json, optional forced reason
outputs: state/halts.json (on trip), halt event in trade-log, optional notify call
invoked_by: all 4 scheduled routines; skills/trade on mainnet failure modes
---

# Circuit Breaker

The agent's stop-loss. **Not a routine** — it is a skill invoked at
multiple checkpoints inside every scheduled routine. Two entrypoints:

- `evaluate()` — read state, compute rolling 24h P&L, fire halt if breach.
- `halt(reason)` — force a halt with a non-loss reason
  (e.g. `mainnet_cancel_failed`, `post_submit_push_failed`).

`skills/risk` provides the math helpers (NAV computation, freshness flags,
baseline lookup). This skill owns the **decision and the write**.

## When routines call `evaluate()`

Pattern across all four scheduled routines: **at least once after boot**,
plus **once more after any operation that may have moved NAV**. The check
is cheap — bounded by `state/portfolio.json` size and a single `jq` over
`state/cycle-index.json.nav_snapshots`.

| Routine | Checkpoints |
|---|---|
| `research-window` | (1) after boot |
| `trade-window` | (1) after boot, (2) after each mark-price refresh, (3) after each fill, (4) after final `nav_snapshot` |
| `daily-close` | (1) after boot, (2) after mark refresh, (3) after final `nav_snapshot`, (4) after recap |
| `overnight-watch` | (1) after boot, (2) after mark refresh, (3) after optional opportunistic fill |

If `evaluate()` fires a halt at any checkpoint, **the calling routine
must stop further phase work immediately** (no more sizing, no more
trades), then call `skills/notify` and `skills/persist` to commit + push
the halt before exiting.

## Trigger conditions

### Loss trigger (from `evaluate()`)

- **Current NAV** via `skills/risk.nav()` (cash + Σ position MTM at fresh
  marks).
- **Baseline NAV**: most recent `nav_snapshots[i]` with `ts <= now - 24h`.
  If none (cold start), use `portfolio.starting_capital`.
- **Trigger:** `current_NAV - baseline_NAV <= -0.10 * baseline_NAV`.

### Forced triggers (from `halt(reason)`)

| Reason | Source |
|---|---|
| `mainnet_cancel_failed` | `skills/trade` partial fill where cancel of remainder fails |
| `post_submit_push_failed` | `skills/trade` after order submission, git push fails |
| `no_baseline_nav` | `evaluate()` when neither nav_snapshots nor starting_capital exist |
| `stale_marks_skip_breaker` | NOT a halt — `evaluate()` emits `preflight_failed` with this reason when >50% of positions lack fresh marks; next cycle re-checks |
| `manual_pause` | NOT auto — humans set this by editing halts.json |

## Steps for `evaluate()`

1. **Short-circuit:** if `state/halts.json.active == true`, return
   `{halted: true, already_active: true}`. Caller proceeds to send daily
   summary if due, but no phase work.

2. **Compute current NAV** via `skills/risk.nav()`. If `stale_flags` cover
   more than 50% of positions: **do not fire**. Instead emit
   `preflight_failed` via `skills/journal` with
   `reason: "stale_marks_skip_breaker"`. Return `{halted: false,
   degraded: true}`.

3. **Lookup baseline NAV.** If neither a 24h-old snapshot nor
   `starting_capital` exists, call `halt("no_baseline_nav")`.

4. **Evaluate trigger.** Compute `pnl_pct = (current - baseline) / baseline`.
   If `pnl_pct <= -0.10`: call `halt("24h_loss_exceeds_10pct", pnl_pct,
   baseline, current)`.

5. Else: return `{halted: false, pnl_pct, baseline, current}`. Caller
   continues phase work.

## Steps for `halt(reason, ...)`

1. **Atomic write `state/halts.json`** (temp + `mv`):
   ```json
   {"schema_version":1,"active":true,"reason":"<reason>","triggered_at":"<now>","cycle_id":"<cycle_id>"}
   ```

2. **Emit `halt` event** via `skills/journal`:
   ```json
   {"event_type":"halt","reason":"<reason>","baseline_nav":<n>,"current_nav":<n>,"pnl_usdc":<n>,"pnl_pct":<pct>}
   ```
   Fields `baseline_nav`/`current_nav`/`pnl_usdc`/`pnl_pct` are null for
   non-loss reasons.

3. **Notify.** Call `skills/notify` with the `circuit_breaker` kind —
   sent in BOTH paper and mainnet per ADR 0008.

4. **Return `{halted: true, reason}` to caller.** The calling routine
   stops further phase work, then invokes `skills/persist` to commit +
   push the halt with message `fix(halt): <reason> [cycle <cycle_id>]`.

## Recovery (human-only)

The agent **never** clears `halts.active`. A human edits
`state/halts.json` to `active: false` after reviewing:

```bash
jq '.active=false | .reason=null | .triggered_at=null | .cycle_id=null' \
   state/halts.json > state/halts.json.tmp && mv state/halts.json.tmp state/halts.json
git add state/halts.json
git commit -m "chore(halt): cleared by <handle> after review"
git push
```

The next routine reads `active: false` and proceeds normally.

## Failure modes

- **Cannot write `halts.json`:** retry once. If still failing, the calling
  routine surfaces the failure to `notify` (if creds present) and aborts —
  next cycle should retry the halt write.
- **No `cycle-index.json`:** treat as cold start; use `starting_capital`.
- **`nav_snapshots` array empty:** same — cold start.
