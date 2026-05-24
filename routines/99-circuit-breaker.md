# 99 — Circuit Breaker

**Trigger:** evaluated near the end of every cycle, after `60-log-and-persist.md`
has written the `nav_snapshot`. Also re-evaluated from `00-wake-up.md` if
`halts.json.active` is already true (to surface status to Telegram).

**Reads:** `state/portfolio.json`, `state/cycle-index.json.nav_snapshots`,
`state/trade-log.jsonl`, `state/halts.json`.

**Writes:** `state/halts.json`, `state/trade-log.jsonl` (`halt` event).

## Trigger formula

- **Current NAV:** `cash_usdc + sum(position.shares * fresh_mark_price)`. If
  any open position lacks a fresh mark, use the most recent value but flag the
  computation; the breaker still fires if the formula crosses the threshold.
- **Baseline NAV:** the most recent `nav_snapshots[i]` with `ts <= now - 24h`.
  If no such snapshot exists (cold start), use `portfolio.starting_capital`.
- **Rolling 24h P&L:** `current_NAV - baseline_NAV`.
- **Trigger condition:**
  `rolling_24h_pnl <= -0.10 * baseline_NAV`.

## Steps

1. **If `halts.json.active == true` already:** do nothing here (the halt is
   already in effect). Daily summary in `70` should still be sent so the human
   knows status.

2. **Else, compute the formula above.** If the trigger fires:
   - Set `state/halts.json`:
     ```json
     {"schema_version":1,"active":true,"reason":"24h_loss_exceeds_10pct","triggered_at":"<now>","cycle_id":"<cycle_id>"}
     ```
   - Append a `halt` event to `state/trade-log.jsonl`:
     ```json
     {"schema_version":1,"event_id":"<cycle_id>-halt-1","cycle_id":"<cycle_id>","event_type":"halt","ts":"<now>","mode":"<network>","reason":"24h_loss_exceeds_10pct","baseline_nav":<n>,"current_nav":<n>,"pnl_usdc":<n>,"pnl_pct":<pct>}
     ```
   - Invoke `routines/70-notify-telegram.md` to send the `circuit_breaker`
     payload. This applies in both paper and mainnet (ADR 0008).
   - Continue to `60-log-and-persist.md` to commit the halt state.

3. **No new trades** may be placed in the same cycle after the halt fires. If
   `50-execute-trade.md` was already entered before the breaker evaluated,
   that's fine — the breaker is a stop on *future* cycles. The current
   cycle's already-executed trade still gets logged.

## Recovery

- The agent never clears `halts.json.active`. Only a human can edit
  `state/halts.json` to set `active: false` after reviewing the situation.
- After human clears the halt, the next cycle proceeds normally.

## Failure modes

- **Stale marks across all positions:** breaker may compute a misleading P&L.
  Conservatively, if more than half of positions have stale marks, do not
  fire the breaker this cycle; instead append a diagnostic `preflight_failed`
  with reason `stale_marks_skip_breaker` and let the next cycle re-evaluate
  with fresh data.
- **No baseline available and no `starting_capital`:** the portfolio was never
  seeded properly. Halt for human attention (`reason: "no_baseline_nav"`).
