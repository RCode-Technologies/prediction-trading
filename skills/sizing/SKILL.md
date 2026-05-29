---
name: sizing
description: Convert candidate + learning_intent into a forecast (always) and an optional sized BUY decision (exploit path only). Kelly, fractional Kelly, 5% cap, correlation guard.
inputs: candidate record (with learning_intent), portfolio, NAV, strategy_version
outputs: forecast event (always), decision event (exploit path only), idempotency_key
---

# Sizing

Single entry for both **exploit** (thesis-driven, may fill) and **explore** (ε-probe, never fills). Branch on `candidate.learning_intent`. Decision event = input to `trade` skill, emitted only on exploit path.

## Guardrails (canonical: `config/guardrails.md`)

- 5% per token: `existing_token_risk + new_order_notional + fees <= 0.05 * NAV` AND `new_order_notional + fees <= cash_usdc`.
- Correlation bucket: related markets share one 5% bucket. Uncertain → reject.
- Long BUY only.

## Inputs

`candidate.learning_intent ∈ {"exploit","explore"}`. Absent → treat as `"explore"` and warn (upstream contract violation).

Explore candidates also carry `explore_rank ∈ {1,2,3}` (cycle probe slot), used to pick ε.

## Steps

1. **Re-check book** via `markets.book()` (gives `best_bid`, `best_ask`, `spread`, `executable_price`, `midpoint`-reference). Stale/one-sided → reject (exploit: `decision reason:"stale_mark"`; explore: still emit forecast at last good midpoint, flag `stale:true`).

2. **Resolve `your_p` by intent.**

   **Exploit:** apply calibration from `strategy/current.md`. Preserve `raw_your_p` and `your_p`. Cold-start fallback (exploit bucket `resolved_n < 10`): if `raw_your_p == market_p`, nudge `your_p = clamp(market_p + sign(thesis_direction) * 0.01, 0.02, 0.98)`. `your_p == market_p` on exploit path is a contract violation — emit `decision reason:"no_thesis_edge"` and skip to step 5 (forecast only).

   **Explore:** ε by rank `1→+0.05, 2→0.00, 3→-0.05`. `your_p = clamp(market_p + ε, 0.02, 0.98)`. `thesis_id = "explore-rank<N>-eps<Pos|Zero|Neg>"`, `feature_tags = ["explore"]`, `source_providers = []`, `confidence = 0.5`, `calibration_applied: false`.

3. **Compose forecast envelope** with all attribution fields per `strategy/current.md` § Forecast attribution + mandatory `learning_intent`.

4. **Idempotency for explore probes.** `explore_dedupe_key = "<mode>:<market_id>:<token_id>:explore:<UTC-date>"`. Grep trade-log; if found, skip — caller's slate builder picks another candidate.

5. **Emit `forecast`** via `journal`.

6. **Branch:**
   - Explore → STOP. No decision.
   - Risk-reduction → not implemented in v2; reject.
   - Exploit → continue.

7. **Observation short-circuit.** `mode.observation_only==true` → STOP, forecast is the entire output.

8. **Fractional Kelly (exploit only)** — cost-honest: you buy at `best_ask`, so edge + price are taken at the ask (`strategy/current.md` § Net edge):
   ```
   edge_net           = your_p - best_ask          # net of spread; the only edge that counts
   kelly_fraction     = edge_net / (1 - best_ask)
   strategy_frac      = 0.25
   thesis_sizing_mult = hypothesis_registry[thesis_id].sizing_mult  # default 1.0
   source_penalty     = Π provider: 0.5 if penalized else 1.0
   effective_frac     = strategy_frac * thesis_sizing_mult * source_penalty
   desired_notional   = clamp(kelly_fraction * effective_frac * NAV, 0, 0.05 * NAV)
   shares             = floor(desired_notional / best_ask / share_lot)
   new_order_notional = shares * best_ask
   fee_usdc           = round(fee_bps / 10000 * new_order_notional, 6)   # fee_bps from strategy (Polymarket taker = 0 bps today); field always present
   ```
   `edge_net <= 0` (or Kelly ≤ 0) → forecast-only. Demoted thesis → `decision reason:"thesis_demoted"`, shares 0. Probation → `sizing_mult:0.5`. (The binding net-edge **floor** gate lands in v3 Phase 2; Phase 1 just prices the edge honestly.)

9. **5% cap.** Reduce shares until both formulas pass. `shares==0` → `decision reason:"below_min_size"`, stop.

10. **Correlation guard.** Same election/match/regulatory event → one 5% bucket aggregate. Uncertain → reject.

11. **`idempotency_key` = `<mode>:<market_id>:<token_id>:<side>:<price>:<shares>:<strategy_version>`.**

12. **Duplicate check.** Grep trade-log; found → `decision reason:"idempotency_duplicate"`, stop.

13. **Emit `decision`** via `journal` (exploit only). `price` is the executable buy price (`best_ask`), not midpoint; carry the book + `edge_net` so `trade` and learning are cost-honest:
    ```json
    {"event_type":"decision","forecast_id":"<fid>","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<o>","side":"BUY","price":<best_ask>,"best_bid":<bid>,"best_ask":<ask>,"spread":<spread>,"edge_net":<your_p-best_ask>,"shares":<n>,"notional_usdc":<usdc>,"fee_bps":<bps>,"fee_usdc":<computed>,"idempotency_key":"<key>","order_id":null,"strategy_version":"<vN>","kelly_fraction":<n>,"strategy_fraction":<n>,"expected_value_usdc":<n>,"risk_bucket_id":"<bucket>","thesis_id":"<id>","feature_tags":["<tag>"],"learning_intent":"exploit","reason":"<short>"}
    ```

## Failure modes

- Stale mark / one-sided book → exploit rejects; explore still emits forecast.
- NAV stale → all exploit sizing rejected; explore still emits.
- 5% / correlation reject → `decision` with reason; acceptable.
- Missing `learning_intent` → treat as explore, emit `preflight_failed reason:"missing_learning_intent"`.
