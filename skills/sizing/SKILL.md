---
name: sizing
description: Convert a candidate market + your probability estimate into a sized BUY decision. Applies Kelly, fractional Kelly, the 5% per-token cap, correlation guard, and emits a forecast + decision event.
inputs: candidate record, current portfolio + NAV, strategy_version from strategy/current.md
outputs: forecast event, decision event (shares may be 0), idempotency_key
---

# Sizing

Convert evidence + price into a sized BUY decision. The `decision` event
emitted here is the input to the `trade` skill.

## Hard guardrails (see `config/guardrails.md`)

- **Per-token cap 5%:**
  `existing_token_risk + new_order_notional + estimated_fees <= 0.05 * NAV`
  AND `new_order_notional + estimated_fees <= cash_usdc`.
- **Correlation bucket:** related markets share one 5% bucket. Uncertain
  correlation → reject.
- **Long BUY only.** SELL reduces/closes existing positions only.

## Steps

1. **Re-check the midpoint** (call into `markets` skill's fresh-price helper —
   does **not** count as a research source). If `stale: true` or both
   bid/ask absent, reject this candidate.

2. **Apply learned calibration.** Read `strategy/current.md` for active
   calibration adjustments, demoted feature tags, source penalties, and
   market-class rules. Preserve both `raw_your_p` (from research / markets)
   and calibrated `your_p` (the probability used for sizing). If no empirical
   adjustment exists yet, set them equal and record `calibration_applied:false`.

3. **Emit a `forecast` event** via `journal` for every candidate considered
   (even if not traded):

   ```json
   {"event_type":"forecast","forecast_id":"<cycle_id>-<market_id>-<token_id>","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<o>","side":"BUY","price":<midpoint>,"shares":0,"notional_usdc":0,"fee_usdc":0,"idempotency_key":null,"order_id":null,"strategy_version":"<vN>","thesis_id":"<id>","evidence_refs":["research/YYYY-MM-DD/<slug>.md#<thesis_id>"],"feature_tags":["<tag>"],"source_providers":["<provider>"],"prior_p":<p0>,"raw_your_p":<p_raw>,"your_p":<p>,"market_p":<midpoint>,"confidence":<0..1>,"calibration_bucket":"50-60","calibration_applied":false,"close_time":"<iso>","resolution_criteria":"<how outcome resolves>","disconfirming_signals":["<signal>"]}
   ```

4. **If `mode.observation_only == true`:** stop here. Forecast is the entire
   output of sizing during the observation window.

5. **Compute fractional Kelly** (default `f = 0.25`, override from
   `strategy/current.md`):

   ```
   edge               = your_p - market_p
   kelly_fraction     = edge / (1 - market_p)        # binary BUY at market_p
   strategy_frac      = <from strategy/current.md, default 0.25>

   # Apply learned multipliers from strategy/current.md:
   thesis_sizing_mult = hypothesis_registry[thesis_id].sizing_mult  # default 1.0
   source_penalty     = product over each cited provider:
                          0.5 if provider.status == "penalized" else 1.0
   effective_frac     = strategy_frac * thesis_sizing_mult * source_penalty

   desired_notional   = clamp(kelly_fraction * effective_frac * NAV,
                              0, 0.05 * NAV)
   shares             = floor(desired_notional / market_p / share_lot)
   new_order_notional = shares * market_p
   estimated_fees     = <Polymarket fee schedule>
   ```

   Theses with `status: "demoted"` are excluded from sizing entirely
   (emit `decision` with `reason: "thesis_demoted"`, shares 0).
   Theses with `status: "probation"` use `sizing_mult: 0.5` per the
   exploration policy.

6. **5% cap check.** `existing_token_risk` = sum of open-position cost basis
   - open orders for the same `token_id`. Reduce `shares` until both cap
     formulas pass. If `shares == 0`, emit a `decision` with
     `reason: "below_min_size"` and stop.

7. **Correlation guard.** Walk open positions + other top candidates. If two
   markets resolve on materially related facts (same election, same match,
   same regulatory event), treat as one bucket and apply 5% to the
   aggregate. Uncertain correlation = reject.

8. **Build `idempotency_key`:**

   ```
   <mode>:<market_id>:<token_id>:<side>:<price>:<shares>:<strategy_version>
   ```

   where `strategy_version` is the `version:` YAML field at the top of
   `strategy/current.md` (default `v0`).

9. **Duplicate check.** Grep `state/trade-log.jsonl` for the key. If a prior
   cycle already submitted under this key, emit a `decision` with
   `reason: "idempotency_duplicate"` and stop.

10. **Emit `decision`** via `journal`:

```json
{"event_type":"decision","forecast_id":"<forecast_id>","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<o>","side":"BUY","price":<midpoint>,"shares":<n>,"notional_usdc":<usdc>,"fee_usdc":<est>,"idempotency_key":"<key>","order_id":null,"strategy_version":"<vN>","kelly_fraction":<n>,"strategy_fraction":<n>,"expected_value_usdc":<n>,"risk_bucket_id":"<bucket>","thesis_id":"<id>","feature_tags":["<tag>"],"learning_intent":"test|exploit|risk_reduction","reason":"<short>"}
```

## Outputs to caller

`{decision: {...}, ready_to_trade: bool}`.

## Failure modes

- **Stale mark / one-sided book:** reject.
- **NAV stale:** all sizing rejected. Existing positions may still be closed
  by SELL flow (out of scope unless explicitly invoked).
- **5% or correlation reject:** acceptable. Decision logged with reason; no
  trade.
