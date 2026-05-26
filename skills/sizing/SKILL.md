---
name: sizing
description: Convert candidate + learning_intent into a forecast (always) and an optional sized BUY decision (exploit path only). Kelly, fractional Kelly, 5% cap, correlation guard.
inputs: candidate record (with learning_intent), portfolio, NAV, strategy_version
outputs: forecast event (always), decision event (exploit path only), idempotency_key
---

# Sizing

Single entry point for both **exploit** (thesis-driven, may fill) and **explore** (ε-probe, never fills). The branch is driven by `candidate.learning_intent`. Decision event = input to `trade` skill — only emitted on the exploit path.

## Guardrails (canonical: `config/guardrails.md`)

- 5% per token: `existing_token_risk + new_order_notional + fees <= 0.05 * NAV` AND `new_order_notional + fees <= cash_usdc`.
- Correlation bucket: related markets share one 5% bucket. Uncertain → reject.
- Long BUY only.

## Inputs

Caller (`markets.rank()` or `trade-window` exploration filler) supplies `candidate.learning_intent ∈ {"exploit", "explore"}`. Absent → treat as `"explore"` and warn (this is a contract violation upstream).

Exploration candidates also carry `explore_rank ∈ {1, 2, 3}` (position in the cycle's probe slot), used to pick ε.

## Steps

1. **Re-check midpoint** via `markets` fresh-price helper (not a research source). Stale or one-sided → reject (emit `decision reason:"stale_mark"` if the intent was exploit; explore probes still emit forecast at the last good midpoint and flag `stale:true`).

2. **Resolve `your_p` by intent.**

   **Exploit path** (`learning_intent == "exploit"`):
   - Apply learned calibration from `strategy/current.md`. Preserve both `raw_your_p` and calibrated `your_p`.
   - **Cold-start fallback** (per exploit bucket `resolved_n < 10`): if `raw_your_p == market_p`, nudge by thesis sign: `your_p = clamp(market_p + sign(thesis_direction) * 0.01, 0.02, 0.98)`. `your_p == market_p` on the exploit path is a contract violation — emit `decision reason:"no_thesis_edge"` and skip to step 11 (forecast only).
   - Record `calibration_applied: <bool>`.

   **Explore path** (`learning_intent == "explore"`):
   - ε by rank: `1 → +0.05, 2 → 0.0, 3 → -0.05`.
   - `raw_your_p = market_p + ε`, `your_p = clamp(raw_your_p, 0.02, 0.98)`.
   - `thesis_id = "explore-rank<N>-eps<Pos|Zero|Neg>"`.
   - `feature_tags = ["explore"]`, `source_providers = []`, `confidence = 0.5`.
   - `calibration_applied: false`.

3. **Compose forecast envelope.**
   ```json
   {
     "event_type": "forecast",
     "forecast_id": "<cid>-<mid>-<tid>",
     "market_id": "<id>", "condition_id": "<cid>", "token_id": "<tid>",
     "outcome": "<o>", "side": "BUY", "price": <mid>,
     "shares": 0, "notional_usdc": 0, "fee_usdc": 0,
     "idempotency_key": null, "order_id": null,
     "strategy_version": "<vN>",
     "thesis_id": "<id>",
     "evidence_refs": [...],
     "feature_tags": [...],
     "source_providers": [...],
     "prior_p": <p0>, "raw_your_p": <p_raw>, "your_p": <p>, "market_p": <mid>,
     "confidence": <0..1>,
     "calibration_bucket": "<lo-hi>",
     "calibration_applied": <bool>,
     "close_time": "<iso>",
     "resolution_criteria": "<how>",
     "disconfirming_signals": [...],
     "learning_intent": "explore|exploit|risk_reduction"
   }
   ```

4. **Idempotency for explore probes.** Build `explore_dedupe_key = "<mode>:<market_id>:<token_id>:explore:<UTC-date>"`. Grep trade-log for any prior `forecast` event today with the same `market_id`/`token_id`/`learning_intent:"explore"`. Found → skip emission; the cycle filler must pick a different rank slot. (Exploit forecasts skip this check; the duplicate guard at step 9 covers them.)

5. **Emit `forecast`** via `journal`.

6. **Branch on intent.**
   - **Explore** → STOP. Forecast is the entire output. No `decision` event.
   - **Risk-reduction** → not implemented in v2; reject.
   - **Exploit** → continue to step 7.

7. **Observation mode short-circuit.** `mode.observation_only==true` → STOP, forecast is the entire output.

8. **Fractional Kelly (exploit only):**
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

9. **5% cap.** `existing_token_risk = Σ open-position cost basis + open orders for same token_id`. Reduce shares until both cap formulas pass. `shares==0` → `decision reason:"below_min_size"`, stop.

10. **Correlation guard.** Walk open positions + other top candidates. Same election/match/regulatory event → one bucket, apply 5% to aggregate. Uncertain → reject.

11. **`idempotency_key`:**
    ```
    <mode>:<market_id>:<token_id>:<side>:<price>:<shares>:<strategy_version>
    ```
    `strategy_version` from frontmatter `version:` in `strategy/current.md` (default `v0`).

12. **Duplicate check.** Grep trade-log for key. Found → `decision reason:"idempotency_duplicate"`, stop.

13. **Emit `decision`** via `journal` (exploit only):
    ```json
    {"event_type":"decision","forecast_id":"<fid>","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<o>","side":"BUY","price":<mid>,"shares":<n>,"notional_usdc":<usdc>,"fee_usdc":<est>,"idempotency_key":"<key>","order_id":null,"strategy_version":"<vN>","kelly_fraction":<n>,"strategy_fraction":<n>,"expected_value_usdc":<n>,"risk_bucket_id":"<bucket>","thesis_id":"<id>","feature_tags":["<tag>"],"learning_intent":"exploit","reason":"<short>"}
    ```

## Failure modes

- Stale mark / one-sided book → exploit reject; explore still emits forecast tagged `stale:true` (the probe is valuable even at stale price for calibration; `recalibrate` filters at scoring time).
- NAV stale → all exploit sizing rejected; explore still emits forecast.
- 5% / correlation reject → acceptable; log `decision` with reason.
- Missing `learning_intent` on candidate → treat as `"explore"`, emit `preflight_failed reason:"missing_learning_intent"` for upstream diagnosis.
