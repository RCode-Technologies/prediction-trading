---
name: trade
description: Execute the sized decision. Paper = synthetic fill at fresh midpoint. Mainnet = py-clob-client limit BUY, partial-fill cancel, pre/post-submit push. Only skill touching WALLET_SEED.
inputs: decision event, config/mode.json
outputs: paper_fill OR mainnet_order_submitted + mainnet_fill OR preflight_failed; updated portfolio.json
---

# Trade

Branches on `mode.network`.

## Paper (`network == "paper"`)

1. `observation_only==true` → exit (sizing's `forecast` was the output).
2. **Fresh midpoint** (1 CLOB book call, not research). Synthesize fill at midpoint.
3. **`paper_fill`** via `journal`:
   ```json
   {"event_type":"paper_fill","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<o>","side":"BUY","price":<mid>,"shares":<n>,"notional_usdc":<usdc>,"fee_usdc":0,"idempotency_key":"<key>","order_id":null}
   ```
4. **Update `state/portfolio.json`** atomically: subtract `notional_usdc` from `cash_usdc`; add/update position with `market_id`, `condition_id`, `token_id`, `outcome`, `side`, `shares`, `avg_price`, `mark_price`, `market_value_usdc`, `cost_basis_usdc`, `opened_at`, `updated_at`, `status:"open"`.
5. **Never** import a Polymarket SDK / read `WALLET_SEED` / sign anything in paper.

## Mainnet — preflights (fail-closed; first fail → `preflight_failed`, exit)

Never infer eligibility, never VPN, never bypass platform restrictions.

1. `mode.network == "mainnet"`.
2. `mode.observation_only == false`.
3. `mode.mainnet_attestation.polymarket_eligible == true`, non-null `attested_by` + `attested_at`.
4. Env vars present (check only, never print): `WALLET_SEED`, `POLYMARKET_FUNDER_ADDRESS`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
5. `skills/polymarket/SKILL.md` exists after `git submodule update --init --recursive`. Else halt.
6. SDK install/import: `uvx --from py-clob-client python -c 'from py_clob_client.client import ClobClient'` (fallback `pip install py-clob-client`). Fail → preflight.
7. Init client per `skills/polymarket/authentication.md`. Wallet derives, API creds via `createOrDeriveApiCreds`, USDC allowance for exchange contract ≥ `notional + fees`.
8. **Funder check:** derived wallet address == `POLYMARKET_FUNDER_ADDRESS` (case-insensitive). Mismatch → preflight.
9. **Re-check market/decision:** open + unpaused, token_id matches outcome, midpoint fresh (≤15 min), all sizing guardrail formulas still pass vs current NAV.
10. **Idempotency search:** any prior `mainnet_order_submitted` or `mainnet_fill` with this `idempotency_key` → emit `decision reason:"idempotency_duplicate"`, abort.
10a. **Prior-intent reconciliation (stable-key check).** The `idempotency_key` includes `price` + `shares`, which change between retries; an exact-key miss is not proof the prior intent didn't reach the exchange. Grep trade-log for any prior `decision` event with `mode:"mainnet"`, same `market_id`/`token_id`/`side`, that has **no** subsequent `mainnet_order_submitted`+`mainnet_fill` pair (or explicit `decision_cleared` event) closing it out. If found:
    - Query the exchange first: `client.get_orders(market=<market_id>)` and `client.get_trades(market=<market_id>)` filtered to this `token_id`/`side`/funder wallet. Any matching open order or recent fill (within 24h) attributable to the prior intent → abort with `decision reason:"prior_unresolved_intent"` and notify; humans clear by appending a `decision_cleared` event (referencing the prior `forecast_id`) and re-running.
    - Exchange shows nothing → append `decision_cleared` with `reason:"exchange_confirmed_absent"` referencing the prior `forecast_id`, then continue.
    This gate is what actually protects against duplicate exposure across retries — the exact-key check in step 10 only catches identical replays.
11. **Pre-submit push.** Commit + push `decision` event via `persist`:
    ```bash
    git add state/trade-log.jsonl
    git commit -m "feat(decision): pre-submit <idempotency_key> [cycle <cid>]"
    git pull --rebase origin main && git push origin main
    ```
    Push fail → `preflight_failed reason:"pre_submit_push_failed"`, no submit.

## Mainnet — submission

12. **Bounded limit BUY** via `createAndPostOrder` (see `skills/polymarket/order-patterns.md`): `side:BUY`, `price:midpoint`, `size:shares`, TIF GTC. **No market orders. ≤1 order/cycle.**

13. **`mainnet_order_submitted`** via `journal`:
    ```json
    {"event_type":"mainnet_order_submitted","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<o>","side":"BUY","price":<mid>,"shares":<n>,"notional_usdc":<usdc>,"fee_usdc":<est>,"idempotency_key":"<key>","order_id":"<sdk_id>"}
    ```

14. **Poll fill** briefly (10-30 s). Emit `mainnet_fill` with **actual** `shares`, `price`, `fee_usdc`, `order_id`.

15. **Partial fill:** SDK cancel remainder. Cancel fails → `circuit-breaker.halt("mainnet_cancel_failed")`, notify, persist, exit.

16. **Update `state/portfolio.json`** with actual fill (not intended).

17. **Post-submit push** via `persist`. Push fail → `circuit-breaker.halt("post_submit_push_failed")`. Pre-submit decision already durable; retried run sees idempotency key and skips.

## Failure modes

- Any preflight fail → `preflight_failed`, no order.
- SDK exception during submit → `preflight_failed reason:"sdk_exception"`. Pre-submit push protects against ghost orders on retry.
- Cancel failure on partial → halt + notify.
- Post-submit push failure → halt + notify.
