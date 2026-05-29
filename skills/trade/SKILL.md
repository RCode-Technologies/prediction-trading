---
name: trade
description: Execute the sized decision. Paper = synthetic fill at the executable price (best_ask BUY / best_bid SELL), fees modeled. Mainnet = py-clob-client limit BUY with pre/post-submit push. Only skill that touches WALLET_SEED.
inputs: decision event, config/mode.json
outputs: paper_fill OR mainnet_order_submitted + mainnet_fill OR preflight_failed; updated portfolio.json
---

# Trade

Branches on `mode.network`.

## Paper

1. `observation_only==true` → exit (sizing's `forecast` was the output).
2. Fresh book via 1 CLOB call (not research; `markets.book()`). **Cost-honest fill price — never the midpoint:**
   ```
   fill_price = best_ask   # BUY
   fill_price = best_bid   # SELL (reduce/close)
   notional_usdc = shares * fill_price
   fee_usdc      = round(fee_bps / 10000 * notional_usdc, 6)   # fee_bps from strategy; Polymarket taker = 0 bps today
   ```
   One-sided/stale book → no fill (treat as `sizing` stale-mark reject). `fee_bps` defaults to **0** (current Polymarket taker schedule), but the field + formula are **always present and logged** — a future non-zero schedule only changes `fee_bps`.
3. **`paper_fill`** via `journal` (`fill_price` = executable side, `fee_usdc` computed — never silently omitted):
   ```json
   {"event_type":"paper_fill","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<o>","side":"BUY","fill_price":<best_ask|best_bid>,"best_bid":<bid>,"best_ask":<ask>,"midpoint":<mid>,"shares":<n>,"notional_usdc":<usdc>,"fee_bps":<bps>,"fee_usdc":<computed>,"idempotency_key":"<key>","order_id":null}
   ```
4. Update `state/portfolio.json` atomically: subtract `notional_usdc + fee_usdc` from `cash_usdc`; upsert position with `market_id`, `condition_id`, `token_id`, `outcome`, `side`, `shares`, `avg_price` (= `fill_price` blended), `mark_mid`, `mark_liquidation` (= `best_bid` for a long; the mark NAV uses — see `skills/risk`), `market_value_usdc` (at `mark_liquidation`), `cost_basis_usdc`, `opened_at`, `updated_at`, `status:"open"`.
5. **Never** import a Polymarket SDK, read `WALLET_SEED`, or sign in paper.

## Mainnet — preflights (fail-closed; first fail → `preflight_failed`, exit)

Never infer eligibility, never VPN, never bypass platform restrictions.

1. `mode.network == "mainnet"`.
2. `mode.observation_only == false`.
3. `mode.mainnet_attestation.polymarket_eligible == true`, non-null `attested_by` + `attested_at`.
4. Env vars present (check only): `WALLET_SEED`, `POLYMARKET_FUNDER_ADDRESS`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
5. `skills/polymarket/SKILL.md` exists after `git submodule update --init --recursive`. Else halt.
6. SDK install/import: `uvx --from py-clob-client python -c 'from py_clob_client.client import ClobClient'` (fallback `pip install py-clob-client`). Fail → preflight.
7. Init client per `skills/polymarket/authentication.md`. API creds via `createOrDeriveApiCreds`. USDC allowance for exchange contract ≥ `notional + fees`.
8. Funder check: derived wallet == `POLYMARKET_FUNDER_ADDRESS` (case-insensitive). Mismatch → preflight.
9. Re-check market/decision: open + unpaused, `token_id` matches outcome, midpoint fresh (≤15 min), all sizing guardrails still pass vs current NAV.
10. **Idempotency search:** prior `mainnet_order_submitted` or `mainnet_fill` with this `idempotency_key` → `decision reason:"idempotency_duplicate"`, abort.
10a. **Prior-intent reconciliation.** `idempotency_key` includes `price`+`shares` (change between retries) — exact-key miss isn't proof the prior intent didn't reach the exchange. Grep trade-log for any prior mainnet `decision` with same `market_id`/`token_id`/`side` and no closing `mainnet_order_submitted`+`mainnet_fill` (or `decision_cleared`):
    - Query exchange: `client.get_orders(market=...)` + `client.get_trades(market=...)` filtered to `token_id`/`side`/funder. Any matching open order or 24h-recent fill → abort `decision reason:"prior_unresolved_intent"` + notify. Humans clear by appending `decision_cleared` referencing prior `forecast_id`.
    - Exchange shows nothing → append `decision_cleared reason:"exchange_confirmed_absent"`, continue.
11. **Pre-submit push.** Commit + push `decision`:
    ```bash
    git add state/trade-log.jsonl
    git commit -m "feat(decision): pre-submit <idempotency_key> [cycle <cid>]"
    git pull --rebase origin main && git push
    ```
    Push fail → `preflight_failed reason:"pre_submit_push_failed"`.

## Mainnet — submission

12. Bounded limit BUY via `createAndPostOrder`: `side:BUY`, `price:midpoint`, `size:shares`, TIF GTC. **No market orders. ≤1 order/cycle.**
13. **`mainnet_order_submitted`** via `journal`:
    ```json
    {"event_type":"mainnet_order_submitted","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<o>","side":"BUY","price":<mid>,"shares":<n>,"notional_usdc":<usdc>,"fee_usdc":<est>,"idempotency_key":"<key>","order_id":"<sdk_id>"}
    ```
14. Poll fill 10-30s via `client.get_trades(market=...)`. Emit `mainnet_fill` with actual `shares`, `price`, `fee_usdc`, `order_id`, `transaction_hash` (Polygon settlement tx hex), and cached `event_slug` + `market_question` (Gamma-captured at decision time). Missing `transaction_hash` triggers the "settlement pending" template variant.
14a. Notify `trade_placed` per fill — never aggregate across cycles.
15. Partial fill: SDK cancel remainder. Cancel fail → `circuit-breaker.halt("mainnet_cancel_failed")`, notify, persist, exit.
16. Update `state/portfolio.json` with **actual** fill.
17. Post-submit push via `persist`. Push fail → `circuit-breaker.halt("post_submit_push_failed")`. Pre-submit decision already durable; retried run sees idempotency key and skips.

## Failure modes

- Any preflight fail → `preflight_failed`, no order.
- SDK exception during submit → `preflight_failed reason:"sdk_exception"`. Pre-submit push protects against ghost orders.
- Cancel failure on partial → halt + notify.
- Post-submit push failure → halt + notify.
