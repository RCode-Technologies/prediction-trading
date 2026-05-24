# 40 — Decide and Size

**Trigger:** after `30-analyze-markets.md` produces a ranked list. Skipped if
halts active or `observation_only == true` (then go straight to logging
forecasts via `50-execute-trade.md` paper branch).

**Reads:** `strategy/current.md`, `config/guardrails.md`, `state/portfolio.json`,
candidates from `30`. Fresh CLOB price re-check is allowed (does not count as
a research source).

**Writes:** `state/trade-log.jsonl` (`forecast`, `decision` events).

## Steps

1. **For the top candidate**, fetch a fresh CLOB price snapshot:
   - `GET https://clob.polymarket.com/book?token_id=<token_id>`
   - Compute `midpoint = (best_bid + best_ask) / 2` if both sides exist and the
     book timestamp is ≤15 minutes old. If only one side and ≤15 min, use last
     trade price. Otherwise: **stale → reject**.

2. **Write a `forecast` event** with your probability estimate, market price,
   and confidence:
   ```json
   {"schema_version":1,"event_id":"<cycle_id>-forecast-1","cycle_id":"<cycle_id>","event_type":"forecast","ts":"<now>","mode":"<network>","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<label>","side":"BUY","price":<midpoint>,"shares":0,"notional_usdc":0,"fee_usdc":0,"idempotency_key":null,"order_id":null,"your_p":<p>,"market_p":<midpoint>,"confidence":<0..1>}
   ```

3. **If `observation_only == true`:** stop here. The forecast is the cycle's
   output. Continue to `60-log-and-persist.md`.

4. **Sizing (fractional-Kelly default).**
   - `edge = your_p - market_p`
   - `kelly_fraction = edge / (1 - market_p)` for a long BUY on a binary
     outcome at price `market_p`.
   - `strategy_fraction` (e.g. 0.25 of full Kelly — set in `strategy/current.md`).
   - `desired_notional = clamp(kelly_fraction * strategy_fraction * NAV, 0, 0.05 * NAV)`
   - Compute `shares = floor(desired_notional / market_p / share_lot)`, then
     `new_order_notional = shares * market_p`, `estimated_fees` per Polymarket
     fee schedule.

5. **5% cap check.** Compute `existing_token_risk` = sum of open position cost
   basis + open orders for the same `token_id`. Require:
   - `existing_token_risk + new_order_notional + estimated_fees <= 0.05 * NAV`
   - `new_order_notional + estimated_fees <= cash_usdc`
   If either fails, reduce `shares` until both pass or `shares == 0`. If
   `shares == 0`, reject — log a `decision` with `shares: 0` and reason.

6. **Correlation guard.** Look through open positions and other top candidates.
   If two markets resolve from materially related facts (same election, same
   match, same regulatory event), treat them as one risk bucket and apply the
   5% cap to the aggregate. If correlation is uncertain, reject this trade.

7. **Build `idempotency_key`:**
   `<mode>:<market_id>:<token_id>:<side>:<price>:<shares>:<strategy_version>`
   where `strategy_version` is the YAML `version:` field at the top of
   `strategy/current.md` (default `v0`).

8. **Search trade-log for the idempotency_key.** If found (any prior cycle), do
   not re-submit. Log a `decision` with `shares: 0` and reason
   `"idempotency_duplicate"`. Continue to `60`.

9. **Write a `decision` event:**
   ```json
   {"schema_version":1,"event_id":"<cycle_id>-decision-1","cycle_id":"<cycle_id>","event_type":"decision","ts":"<now>","mode":"<network>","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<label>","side":"BUY","price":<midpoint>,"shares":<n>,"notional_usdc":<usdc>,"fee_usdc":<est>,"idempotency_key":"<key>","order_id":null,"strategy_version":"<vN>","reason":"<short>"}
   ```

10. **Hand off** to `50-execute-trade.md` with the decision in hand.

## Failure modes

- **Stale or one-sided book:** reject. Do not size on a stale mark.
- **NAV flagged stale by `10-load-state.md`:** reject all new trades; existing
  positions may still be closed by SELL (out of scope for v1 unless explicit).
- **5% or correlation reject:** acceptable outcome. Log and move on.
