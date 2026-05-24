---
name: sizing
description: Convert candidate + your_p into sized BUY decision. Kelly, fractional Kelly, 5% cap, correlation guard. Emits forecast + decision.
inputs: candidate record, portfolio, NAV, strategy_version
outputs: forecast event, decision event (shares may be 0), idempotency_key
---

# Sizing

Decision event = input to `trade` skill.

## Guardrails (canonical: `config/guardrails.md`)

- 5% per token: `existing_token_risk + new_order_notional + fees <= 0.05 * NAV` AND `new_order_notional + fees <= cash_usdc`.
- Correlation bucket: related markets share one 5% bucket. Uncertain → reject.
- Long BUY only.

## Steps

1. **Re-check midpoint** via `markets` fresh-price helper (not a research source). Stale or one-sided → reject.

2. **Apply learned calibration** from `strategy/current.md`. Preserve both `raw_your_p` and calibrated `your_p`. No empirical adjustment yet → set equal, record `calibration_applied:false`.

3. **Emit `forecast`** via `journal` for **every** candidate considered (even untraded):
   ```json
   {"event_type":"forecast","forecast_id":"<cid>-<mid>-<tid>","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<o>","side":"BUY","price":<mid>,"shares":0,"notional_usdc":0,"fee_usdc":0,"idempotency_key":null,"order_id":null,"strategy_version":"<vN>","thesis_id":"<id>","evidence_refs":["research/YYYY-MM-DD/<slug>.md#<thesis_id>"],"feature_tags":["<tag>"],"source_providers":["<provider>"],"prior_p":<p0>,"raw_your_p":<p_raw>,"your_p":<p>,"market_p":<mid>,"confidence":<0..1>,"calibration_bucket":"50-60","calibration_applied":false,"close_time":"<iso>","resolution_criteria":"<how>","disconfirming_signals":["<signal>"]}
   ```

4. **Observation mode** (`mode.observation_only==true`) → stop. Forecast is sizing's entire output.

5. **Fractional Kelly:**
   ```
   edge               = your_p - market_p
   kelly_fraction     = edge / (1 - market_p)
   strategy_frac      = <from strategy/current.md, default 0.25>
   thesis_sizing_mult = hypothesis_registry[thesis_id].sizing_mult  # default 1.0
   source_penalty     = Π provider: 0.5 if penalized else 1.0
   effective_frac     = strategy_frac * thesis_sizing_mult * source_penalty
   desired_notional   = clamp(kelly_fraction * effective_frac * NAV, 0, 0.05 * NAV)
   shares             = floor(desired_notional / market_p / share_lot)
   new_order_notional = shares * market_p
   estimated_fees     = <Polymarket fee schedule>
   ```
   `status:demoted` theses → excluded entirely (emit `decision reason:"thesis_demoted"`, shares 0). `status:probation` → `sizing_mult:0.5`.

6. **5% cap.** `existing_token_risk = Σ open-position cost basis + open orders for same token_id`. Reduce shares until both cap formulas pass. `shares==0` → `decision reason:"below_min_size"`, stop.

7. **Correlation guard.** Walk open positions + other top candidates. Same election/match/regulatory event → one bucket, apply 5% to aggregate. Uncertain → reject.

8. **`idempotency_key`:**
   ```
   <mode>:<market_id>:<token_id>:<side>:<price>:<shares>:<strategy_version>
   ```
   `strategy_version` from frontmatter `version:` in `strategy/current.md` (default `v0`).

9. **Duplicate check.** Grep trade-log for key. Found → `decision reason:"idempotency_duplicate"`, stop.

10. **Emit `decision`** via `journal`:
    ```json
    {"event_type":"decision","forecast_id":"<fid>","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<o>","side":"BUY","price":<mid>,"shares":<n>,"notional_usdc":<usdc>,"fee_usdc":<est>,"idempotency_key":"<key>","order_id":null,"strategy_version":"<vN>","kelly_fraction":<n>,"strategy_fraction":<n>,"expected_value_usdc":<n>,"risk_bucket_id":"<bucket>","thesis_id":"<id>","feature_tags":["<tag>"],"learning_intent":"test|exploit|risk_reduction","reason":"<short>"}
    ```

## Failure modes

- Stale mark / one-sided book → reject.
- NAV stale → all sizing rejected.
- 5% / correlation reject → acceptable; log `decision` with reason.
