---
name: sizing
description: Convert candidate + learning_intent into a forecast (always) and, past the binding edge gate, a sized BUY decision. Edge gate (provenance + net-edge floor), Kelly, fractional Kelly, 5% cap, correlation guard.
inputs: candidate record (with learning_intent + gate fields), portfolio, NAV, strategy_version
outputs: forecast event (always), decision event (exploit attempts — sized fill on gate-pass, shares:0 + reason on gate-miss), idempotency_key
---

# Sizing

Single entry for both **exploit** (thesis-driven, may fill past the § Edge gate) and **explore** (forecast-only, never fills). Branch on `candidate.learning_intent`; a gate-miss demotes exploit→explore. Decision event = input to `trade` skill, emitted only when the gate passes (or, with `shares:0`, to record a gate-miss reason).

## Guardrails (canonical: `config/guardrails.md`)

- **Edge gate (binding, exploit only):** capital is risked only past the gate — see step 7. Any miss → forecast-only.
- 5% per token: `existing_token_risk + new_order_notional + fees <= 0.05 * NAV` AND `new_order_notional + fees <= cash_usdc`.
- Correlation bucket: related markets share one 5% bucket. Uncertain → reject.
- Long BUY only.

## Inputs

`candidate.learning_intent ∈ {"exploit","explore"}`. Absent → treat as `"explore"` and warn (upstream contract violation).

Explore candidates also carry `explore_rank ∈ {1,2,3}` (cycle probe slot), used to pick ε.

## Steps

1. **Re-check book** via `markets.book()` (gives `best_bid`, `best_ask`, `spread`, `executable_price`, `midpoint`-reference). Stale/one-sided → reject (exploit: `decision reason:"stale_mark"`; explore: still emit forecast at last good midpoint, flag `stale:true`).

2. **Resolve `your_p` by intent.**

   **Exploit:** apply calibration from `strategy/current.md`. Preserve `raw_your_p` and `your_p`. Cold-start fallback (exploit bucket `resolved_n < 10`): if `raw_your_p == market_p`, nudge `your_p = clamp(market_p + sign(thesis_direction) * 0.01, 0.02, 0.98)`. `your_p == market_p` on exploit path is a contract violation — emit `decision reason:"no_thesis_edge"` and skip to step 5 (forecast only). Carry the candidate's `resolution_criteria`, `resolution_parsed`, `reference_class`, `source_providers`, `edge_source` forward — the step-7 gate reads them.

   **Explore (forecast-only — the default):** use the candidate's genuine `your_p` (research-informed where present, else the rank's honest judgment estimate). `feature_tags = ["explore"]`, `confidence` from the candidate (default 0.5), `calibration_applied: false`, `reference_class` may be null, `edge_source` default `"none"`. (The v2 ε-by-rank probe device is retired — see `strategy/current.md` § Forecast batch policy.)

3. **Compose forecast envelope** with all attribution fields per `strategy/current.md` § Forecast attribution + mandatory `learning_intent`. Include the v3 gate/cost fields: `resolution_criteria`, `resolution_parsed`, `reference_class`, `edge_source`, `best_bid`, `best_ask`, `spread`, `edge_net = your_p − best_ask`, and `sizing_tier: 0` (default until the Phase 5 ladder).

4. **Idempotency for explore probes.** `explore_dedupe_key = "<mode>:<market_id>:<token_id>:explore:<UTC-date>"`. Grep trade-log; if found, skip — caller's slate builder picks another candidate.

5. **Emit `forecast`** via `journal`.

6. **Branch:**
   - Explore → STOP. No decision (forecast-only is the entire output).
   - Risk-reduction → not implemented until Phase 5; reject.
   - Exploit → continue.

7. **Edge gate (BINDING — exploit only; `strategy/current.md` § Edge gate).** An exploit fill is allowed only if ALL hold:
   ```
   resolution_parsed == true          # else reason: resolution_unparsed
   reference_class    != null         # else reason: no_reference_class
   len(source_providers) >= 2         # else reason: insufficient_sources
   edge_net >= net_edge_floor (0.03)  # else reason: edge_below_net_threshold   (edge_net = your_p − best_ask)
   ```
   Any miss → **forecast-only**: emit a `decision` with the failing `reason ∈ {resolution_unparsed, no_reference_class, insufficient_sources, edge_below_net_threshold}`, `shares:0`, `sizing_tier:0`, `learning_intent:"explore"` (demoted), then STOP. Check provenance conjuncts first (they are the Iran lesson — block on *provenance*, not just magnitude), then the net-floor. All four pass → continue to sizing with `sizing_tier:0` (the conviction ladder is Phase 5).

8. **Observation short-circuit.** `mode.observation_only==true` → STOP, forecast is the entire output.

9. **Fractional Kelly (exploit only)** — cost-honest: you buy at `best_ask`, so edge + price are taken at the ask (`strategy/current.md` § Net edge):
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
   Kelly ≤ 0 → forecast-only (the step-7 gate already enforced `edge_net >= 0.03`). Demoted thesis → `decision reason:"thesis_demoted"`, shares 0. Probation → `sizing_mult:0.5`.

10. **5% cap.** Reduce shares until both formulas pass. `shares==0` → `decision reason:"below_min_size"`, stop.

11. **Correlation guard.** Same election/match/regulatory event → one 5% bucket aggregate. Uncertain → reject.

12. **`idempotency_key` = `<mode>:<market_id>:<token_id>:<side>:<price>:<shares>:<strategy_version>`.**

13. **Duplicate check.** Grep trade-log; found → `decision reason:"idempotency_duplicate"`, stop.

14. **Emit `decision`** via `journal` (exploit only). `price` is the executable buy price (`best_ask`), not midpoint; carry the book + `edge_net` + `sizing_tier` so `trade` and learning are cost-honest:
    ```json
    {"event_type":"decision","forecast_id":"<fid>","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<o>","side":"BUY","price":<best_ask>,"best_bid":<bid>,"best_ask":<ask>,"spread":<spread>,"edge_net":<your_p-best_ask>,"sizing_tier":0,"shares":<n>,"notional_usdc":<usdc>,"fee_bps":<bps>,"fee_usdc":<computed>,"idempotency_key":"<key>","order_id":null,"strategy_version":"<vN>","kelly_fraction":<n>,"strategy_fraction":<n>,"expected_value_usdc":<n>,"risk_bucket_id":"<bucket>","thesis_id":"<id>","feature_tags":["<tag>"],"learning_intent":"exploit","reason":"<short>"}
    ```

## Failure modes

- Stale mark / one-sided book → exploit rejects; explore still emits forecast.
- NAV stale → all exploit sizing rejected; explore still emits.
- **Edge-gate miss** (unparsed resolution / null reference class / <2 sources / `edge_net` < floor) → forecast-only `decision` with the binding `reason`; acceptable (this is the common case in early v3).
- 5% / correlation reject → `decision` with reason; acceptable.
- Missing `learning_intent` → treat as explore, emit `preflight_failed reason:"missing_learning_intent"`.
