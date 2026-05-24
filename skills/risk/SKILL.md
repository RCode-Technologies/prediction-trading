---
name: risk
description: Circuit-breaker evaluation and halt management. Computes rolling 24h P&L from nav_snapshots; flips state/halts.json on breach; surfaces guardrail-recommendation hints for the human.
inputs: state/portfolio.json, state/cycle-index.json.nav_snapshots, state/halts.json
outputs: state/halts.json, halt event, optional notify call
---

# Risk

Circuit-breaker and halt state. Invoked at the end of `midday` and
`end-of-day` routines, by `trade` on mainnet errors that demand a halt, and
by the dedicated `circuit-breaker` routine when explicitly triggered.

## Formulas

- **Current NAV:** `cash_usdc + sum(position.shares * fresh_mark_price)`.
  If any open position lacks a fresh mark, use the most recent value but
  flag the computation. Breaker still fires if formula crosses threshold.
- **Baseline NAV:** most recent `nav_snapshots[i]` with
  `ts <= now - 24h`. If none (cold start), use `portfolio.starting_capital`.
- **Rolling 24h P&L:** `current_NAV - baseline_NAV`.
- **Trigger:** `rolling_24h_pnl <= -0.10 * baseline_NAV`.

## Steps

1. **If `halts.active == true` already:** do nothing here. The halt is in
   effect. (The daily summary in `notify` should still surface status.)

2. **Else compute** the formulas above. If trigger fires:
   - Atomic write `state/halts.json`:
     ```json
     {"schema_version":1,"active":true,"reason":"24h_loss_exceeds_10pct","triggered_at":"<now>","cycle_id":"<cycle_id>"}
     ```
   - Emit `halt` event via `journal`:
     ```json
     {"event_type":"halt","reason":"24h_loss_exceeds_10pct","baseline_nav":<n>,"current_nav":<n>,"pnl_usdc":<n>,"pnl_pct":<pct>}
     ```
   - Call `notify` with `circuit_breaker` payload (both paper and mainnet
     per ADR 0008).
   - Caller proceeds to `persist` skill to commit + push the halt.

3. **No new trades** may be placed in the same cycle after a halt fires.
   Cycle's already-executed trades remain logged (the breaker is a stop on
   *future* cycles, not a retroactive undo).

## Manual halt API for `trade` skill

`trade` may invoke `risk` directly with `reason` and `notify=true` for
non-loss halt triggers (e.g. `mainnet_cancel_failed`,
`post_submit_push_failed`).

## Recovery

The agent **never** clears `halts.active`. Only a human edits
`state/halts.json` to `active: false` after reviewing the situation. Next
cycle sees `active: false` and proceeds.

## Guardrail-recommendation hint

If the agent's reflection analysis suggests `config/guardrails.md` should
change (per ADR 0005, the agent cannot edit it), the `reflect` skill writes
a recommendation that the `recap` skill includes in the next daily summary
Telegram message. Risk skill exposes a helper `surface_recommendation(text)`
that appends a `recap_hint` field to the latest in-flight daily summary
payload buffer (in-memory; not persisted as its own file).

## Failure modes

- **Stale marks across >50% of positions:** do not fire breaker this cycle.
  Emit `preflight_failed` with `reason: "stale_marks_skip_breaker"`. Next
  cycle re-evaluates with fresh data.
- **No baseline and no `starting_capital`:** portfolio never seeded
  properly. Halt for human attention with `reason: "no_baseline_nav"`.
