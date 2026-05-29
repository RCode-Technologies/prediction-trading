---
name: sizing
description: Convert candidate + learning_intent into a forecast (always) and, past the binding edge gate, a tier-sized BUY decision — or a risk_reduction SELL on the disconfirmation stop. Edge gate (provenance + net-edge floor) runs first, then the conviction ladder (Tier 0–3), portfolio-heat cap, governors, correlation guard.
inputs: candidate record (with learning_intent + gate fields), portfolio, NAV, scorecard (by_edge_source), governor state, strategy_version
outputs: forecast event (always), decision event (exploit attempts — tier-sized fill on gate-pass, shares:0 + reason on gate-miss; risk_reduction SELL on stop), idempotency_key
---

# Sizing

Single entry for **exploit** (thesis-driven, may fill past the § Edge gate + ladder), **explore** (forecast-only, never fills), and **risk_reduction** (a reducing/closing SELL on the disconfirmation stop). Branch on `candidate.learning_intent`; a gate-miss demotes exploit→explore. Decision event = input to `trade` skill, emitted on a gate-pass-then-tier (BUY), a gate-miss (`shares:0` + reason), or a stop (SELL).

## Guardrails (canonical: `config/guardrails.md`)

- **Edge gate (binding, exploit only):** capital is risked only past the gate — see step 7. Any miss → forecast-only. **The gate runs first; only a gate-passer is eligible for a tier above 0.**
- **Conviction ladder (v3):** `sizing_tier ∈ {0,1,2,3}` with caps `{0, 2%, 5%, 10%}` NAV; size is *earned* by bucket skill (`clv_mean`/`brier_skill`). Replaces the flat 5% cap as the primary rule. 10% is the hard ceiling. Step 9a.
- **Portfolio heat:** `portfolio_heat ≤ 25%` across ≤ 4 uncorrelated buckets; reject a new exploit that would breach. Tier 3 only when heat < 10%. Step 9b.
- **Governors:** −8%-from-peak probation → `sizing_mult:0.5`; −15% freeze + heat-breach → reject new capital risk (exits exempt). Step 0.
- **Disconfirmation stop (`risk_reduction`):** −25% mark-from-entry or a named disconfirming event → reducing/closing SELL. Step R.
- Per-tier cap: `existing_token_risk + new_order_notional + fees <= tier_cap_pct * NAV` AND `new_order_notional + fees <= cash_usdc`.
- Correlation bucket: related markets share one tier cap + one heat bucket. Uncertain → reject.
- Long BUY only (entries); SELL only to reduce/close (`risk_reduction`).

## Inputs

`candidate.learning_intent ∈ {"exploit","explore","risk_reduction"}`. Absent → treat as `"explore"` and warn (upstream contract violation).

A `risk_reduction` candidate is a *held position* flagged by an exit check (a routine's disconfirmation-stop scan, see § Risk-reduction SELL path) — not a market discovery. It carries the open `position` + a `stop_reason ∈ {pnl_stop_25pct, disconfirming_event}`.

## Steps

0. **Governor read (v3).** Take the cycle's `circuit-breaker.evaluate()` result (the routine already ran it at a checkpoint):
   - `halted` (incl. `drawdown_freeze_15pct`) or `heat_breach` → **no new capital risk**: any `exploit` is demoted to forecast-only (`decision reason ∈ {"drawdown_freeze","heat_breach"}`, `shares:0`, `sizing_tier:0`). `risk_reduction` SELLs are **exempt** (always allowed — a freeze must never trap a loser). `explore` proceeds (forecast costs nothing).
   - `probation` (−8% from peak) → carry `sizing_mult:0.5` into step 9 (half size, still bets).

1. **Re-check book** via `markets.book()` (gives `best_bid`, `best_ask`, `spread`, `executable_price`, `midpoint`-reference). Stale/one-sided → reject (exploit: `decision reason:"stale_mark"`; explore: still emit forecast at last good midpoint, flag `stale:true`).

2. **Resolve `your_p` by intent.**

   **Exploit:** apply calibration from `strategy/current.md`. Preserve `raw_your_p` and `your_p`. Cold-start fallback (exploit bucket `resolved_n < 10`): if `raw_your_p == market_p`, nudge `your_p = clamp(market_p + sign(thesis_direction) * 0.01, 0.02, 0.98)`. `your_p == market_p` on exploit path is a contract violation — emit `decision reason:"no_thesis_edge"` and skip to step 5 (forecast only). Carry the candidate's `resolution_criteria`, `resolution_parsed`, `reference_class`, `source_providers`, `edge_source` forward — the step-7 gate reads them.

   **Explore (forecast-only — the default):** use the candidate's genuine `your_p` (research-informed where present, else the rank's honest judgment estimate). `feature_tags = ["explore"]`, `confidence` from the candidate (default 0.5), `calibration_applied: false`, `reference_class` may be null, `edge_source` default `"none"`. (The v2 ε-by-rank probe device is retired — see `strategy/current.md` § Forecast batch policy.)

3. **Compose forecast envelope** with all attribution fields per `strategy/current.md` § Forecast attribution + mandatory `learning_intent`. Include the v3 gate/cost fields: `resolution_criteria`, `resolution_parsed`, `reference_class`, `edge_source`, `best_bid`, `best_ask`, `spread`, `edge_net = your_p − best_ask`, and `sizing_tier: 0` (default until the Phase 5 ladder).

4. **Idempotency for explore probes.** `explore_dedupe_key = "<mode>:<market_id>:<token_id>:explore:<UTC-date>"`. Grep trade-log; if found, skip — caller's slate builder picks another candidate.

5. **Emit `forecast`** via `journal`.

6. **Branch:**
   - Explore → STOP. No decision (forecast-only is the entire output).
   - Risk-reduction → jump to **§ Risk-reduction SELL path** (step R). Skips the edge gate + ladder (you are *reducing* risk, not opening it).
   - Exploit → continue.

7. **Edge gate (BINDING — exploit only; `strategy/current.md` § Edge gate).** An exploit fill is allowed only if ALL hold:
   ```
   resolution_parsed == true          # else reason: resolution_unparsed
   reference_class    != null         # else reason: no_reference_class
   len(source_providers) >= 2         # else reason: insufficient_sources
   edge_net >= net_edge_floor (0.03)  # else reason: edge_below_net_threshold   (edge_net = your_p − best_ask)
   ```
   Any miss → **forecast-only**: emit a `decision` with the failing `reason ∈ {resolution_unparsed, no_reference_class, insufficient_sources, edge_below_net_threshold}`, `shares:0`, `sizing_tier:0`, `learning_intent:"explore"` (demoted), then STOP. Check provenance conjuncts first (they are the Iran lesson — block on *provenance*, not just magnitude), then the net-floor. **All four pass → the candidate is gate-eligible; continue (the conviction ladder in step 9a assigns its tier).** The gate runs **first**; tier assignment is downstream and never overrides a gate-miss.

8. **Observation short-circuit.** `mode.observation_only==true` → STOP, forecast is the entire output.

9a. **Conviction ladder — assign `sizing_tier` (v3; `config/guardrails.md` § Position sizing).** Read the candidate's `edge_source` bucket from `state/scorecard.json` `by_edge_source[]` (`clv_mean`, `clv_n`, `brier_skill`). A gate-passer (step 7) is at least Tier-1-eligible; climb only if every precondition for the higher tier holds:

    ```
    proven_bucket  = (bucket.clv_mean > 0 and bucket.clv_n >= 20) or (bucket.brier_skill > 0)
    catalyst       = candidate.hard_near_term_catalyst == true        # named, dated, near-term

    tier = 1 if (edge_net >= net_edge_floor and resolution_parsed and reference_class != null
                 and len(source_providers) >= 2 and bucket.clv_mean >= 0)            # Lean
    tier = 2 if (tier>=1 and proven_bucket and catalyst)                              # Conviction
    tier = 3 if (tier>=2 and edge_net >= 2*net_edge_floor
                 and high_calibration_confidence and uncorrelated
                 and portfolio_heat < 0.10)                                          # Degen (earned)
    ```

    - **Unproven bucket** (not `proven_bucket`) ⇒ **capped at ≤ Tier 1**, regardless of edge magnitude (the data must earn the size). Bucket `clv_mean < 0` ⇒ **Tier 0** (forecast-only): `decision reason:"bucket_clv_negative", shares:0, sizing_tier:0`, STOP.
    - `tier_cap_pct = {0:0.0, 1:0.02, 2:0.05, 3:0.10}[tier]`. Record the cleared preconditions (see step 14: `tier_preconditions[]`). **Tier ≥ 2 requires a logged proven-skill reference** — set `proven_skill_ref` to the scorecard bucket + metric (`"by_edge_source[news_latency].clv_mean=0.04,clv_n=23"`); absent ⇒ cannot exceed Tier 1.

9b. **Portfolio-heat cap (v3; `config/guardrails.md` § Portfolio heat).** `risk.portfolio_heat()`:
    - New order would push `heat_pct > 0.25` or open a **5th** uncorrelated bucket → reject: `decision reason:"heat_cap_exceeded", shares:0`, STOP (existing positions ride; this blocks *new* risk only).
    - `tier == 3` but current `heat_pct >= 0.10` → demote to Tier 2 (`tier_cap_pct = 0.05`), note `tier_capped_by:"heat"`.

9. **Fractional Kelly (exploit only)** — cost-honest: you buy at `best_ask`, so edge + price are taken at the ask (`strategy/current.md` § Net edge). The tier cap (9a) replaces the old flat 5% clamp:
   ```
   edge_net           = your_p - best_ask          # net of spread; the only edge that counts
   kelly_fraction     = edge_net / (1 - best_ask)
   strategy_frac      = 0.25
   thesis_sizing_mult = hypothesis_registry[thesis_id].sizing_mult  # default 1.0
   source_penalty     = Π provider: 0.5 if penalized else 1.0
   governor_mult      = 0.5 if probation (step 0) else 1.0           # −8%-from-peak governor
   effective_frac     = strategy_frac * thesis_sizing_mult * source_penalty * governor_mult
   desired_notional   = clamp(kelly_fraction * effective_frac * NAV, 0, tier_cap_pct * NAV)
   shares             = floor(desired_notional / best_ask / share_lot)
   new_order_notional = shares * best_ask
   fee_usdc           = round(fee_bps / 10000 * new_order_notional, 6)   # fee_bps from strategy (Polymarket taker = 0 bps today); field always present
   ```
   Kelly ≤ 0 → forecast-only (the step-7 gate already enforced `edge_net >= 0.03`). Demoted thesis → `decision reason:"thesis_demoted"`, shares 0.

10. **Tier cap + min size.** Reduce shares until both per-tier formulas pass (`existing_token_risk + new_order_notional + fees <= tier_cap_pct * NAV` AND `new_order_notional + fees <= cash_usdc`). **Tier 1 min:** `new_order_notional < 0.005 * NAV` (below the 0.5% Lean floor) → `decision reason:"below_min_size"`, shares 0, stop. `shares==0` for any other reason → `decision reason:"below_min_size"`, stop. **`new_order_notional` may never exceed `0.10 * NAV` (hard ceiling) under any path.**

11. **Correlation guard.** Same election/match/regulatory event → one 5% bucket aggregate. Uncertain → reject.

12. **`idempotency_key` = `<mode>:<market_id>:<token_id>:<side>:<price>:<shares>:<strategy_version>`.**

13. **Duplicate check.** Grep trade-log; found → `decision reason:"idempotency_duplicate"`, stop.

14. **Emit `decision`** via `journal` (exploit only). `price` is the executable buy price (`best_ask`), not midpoint; carry the book + `edge_net` + the **assigned `sizing_tier`** + the `tier_preconditions[]` it cleared (and, for Tier ≥ 2, the `proven_skill_ref`) so `trade` and learning are cost-honest and every decision is tier-auditable:
    ```json
    {"event_type":"decision","forecast_id":"<fid>","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<o>","side":"BUY","price":<best_ask>,"best_bid":<bid>,"best_ask":<ask>,"spread":<spread>,"edge_net":<your_p-best_ask>,"sizing_tier":<0-3>,"tier_preconditions":["edge_net>=floor","resolution_parsed","reference_class","sources>=2","bucket_clv>=0"],"proven_skill_ref":"<by_edge_source[..] metric or null>","tier_cap_pct":<0.02|0.05|0.10>,"governor_mult":<1.0|0.5>,"portfolio_heat":<pct>,"shares":<n>,"notional_usdc":<usdc>,"fee_bps":<bps>,"fee_usdc":<computed>,"idempotency_key":"<key>","order_id":null,"strategy_version":"<vN>","kelly_fraction":<n>,"strategy_fraction":<n>,"expected_value_usdc":<n>,"risk_bucket_id":"<bucket>","thesis_id":"<id>","feature_tags":["<tag>"],"learning_intent":"exploit","reason":"<short>"}
    ```

## Risk-reduction SELL path (step R; v3 — generalizes the manual Iran exit)

Fired when an **exit check** (a routine's disconfirmation-stop scan, see `routines/overnight-watch.md`, `daily-close.md`, `heartbeat.md`) flags a held position whose stop tripped. Skips the edge gate + conviction ladder (you are *reducing* risk, not opening it) and is **exempt from the freeze/halt** (you may always reduce risk).

R1. **Confirm the stop.** From `risk.pnl_from_entry(position)` and the position's `disconfirming_signals`:
   ```
   pnl_stop_25pct      : pnl_from_entry.pnl_pct <= -0.25         # −25% mark-from-entry (long), liquidation-marked
   disconfirming_event : a named disconfirming_signals[] item materialised (routine/research flagged it)
   ```
   Stale mark (`pnl_from_entry` flagged stale) → do **not** fire on the −25% rule alone (a stale book is not a real loss); a confirmed `disconfirming_event` still fires. No trip → STOP (no decision).

R2. **Re-check book** via `markets.book()`. SELL executable price = `best_bid` (cost-honest; `skills/trade` fills the SELL at `best_bid`). One-sided/stale book → `decision reason:"stale_mark"`, retry next cycle (the position is flagged; the exit re-attempts).

R3. **Sizing the reduction.** Default **full close** (`shares = position.shares`) on `disconfirming_event` or a hard `pnl_stop_25pct`; a partial reduce is permitted (`shares = ceil(position.shares * reduce_frac)`) when strategy specifies trimming. Long BUY-only still holds for *opening*; this is the sole SELL path.

R4. **`idempotency_key` = `<mode>:<market_id>:<token_id>:SELL:risk_reduction:<UTC-date>`.** Grep trade-log; found → `decision reason:"idempotency_duplicate"`, stop (prevents double-selling on re-runs / overlapping cycles).

R5. **Emit `decision`** via `journal` then hand to `skills/trade` (which fills the SELL at `best_bid` and updates the portfolio):
    ```json
    {"event_type":"decision","forecast_id":"<origin_fid>","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<o>","side":"SELL","price":<best_bid>,"best_bid":<bid>,"best_ask":<ask>,"spread":<spread>,"sizing_tier":0,"shares":<n>,"notional_usdc":<usdc>,"fee_bps":<bps>,"fee_usdc":<computed>,"idempotency_key":"<key>","order_id":null,"strategy_version":"<vN>","pnl_from_entry_pct":<pct>,"stop_reason":"pnl_stop_25pct|disconfirming_event","disconfirming_event":"<name or null>","thesis_id":"<id>","feature_tags":["risk_reduction"],"learning_intent":"risk_reduction","reason":"disconfirmation_stop"}
    ```
    `sizing_tier:0` (an exit is not a sized opening). `trade`'s paper path logs the reducing/closing `paper_fill` at `best_bid`. The 2026-05-27 Iran exit is the inaugural manual instance of exactly this decision; this path makes it automatic.

## Failure modes

- Stale mark / one-sided book → exploit rejects; explore still emits forecast; `risk_reduction` retries next cycle (position stays flagged), but a confirmed `disconfirming_event` still fires.
- NAV stale → all exploit sizing rejected; explore still emits; `risk_reduction` exits unaffected (exempt).
- **Edge-gate miss** (unparsed resolution / null reference class / <2 sources / `edge_net` < floor) → forecast-only `decision` with the binding `reason`; acceptable (this is the common case in early v3).
- **Tier 0 / unproven bucket** (`bucket_clv_negative`, or no proven skill ⇒ capped ≤ Tier 1) → forecast-only or Tier-1-capped; acceptable (size is earned — early v3 mostly Tier ≤ 1 by design).
- **Heat cap / 5th bucket** → `decision reason:"heat_cap_exceeded"`, `shares:0`; new risk blocked, existing positions ride.
- **Governor** — freeze (`drawdown_freeze`) or heat-breach → new exploits demoted to forecast-only; probation → `governor_mult:0.5` (still bets at half size); `risk_reduction` exempt throughout.
- Tier cap / correlation reject → `decision` with reason; acceptable.
- Missing `learning_intent` → treat as explore, emit `preflight_failed reason:"missing_learning_intent"`.
