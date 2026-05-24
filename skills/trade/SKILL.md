---
name: trade
description: Execute the sized decision — paper (synthetic fill at fresh midpoint) or mainnet (py-clob-client limit BUY, partial-fill cancel, pre/post-submit push). Only skill that touches WALLET_SEED.
inputs: decision event from sizing skill, config/mode.json
outputs: paper_fill OR mainnet_order_submitted + mainnet_fill OR preflight_failed events; updated state/portfolio.json
---

# Trade

The only skill permitted to read wallet secrets or import the Polymarket SDK
(ADR 0003). Branches on `config/mode.json.network`.

## Paper branch (`network == "paper"`)

1. **If `observation_only == true`:** exit. Sizing's `forecast` was the
   output. Do **not** write paper fills during observation.

2. **Fetch fresh midpoint** (one CLOB book call — does not count as a
   research source) and synthesize a fill at that midpoint.

3. **Emit `paper_fill`** via `journal`:
   ```json
   {"event_type":"paper_fill","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<o>","side":"BUY","price":<midpoint>,"shares":<n>,"notional_usdc":<usdc>,"fee_usdc":0,"idempotency_key":"<key>","order_id":null}
   ```

4. **Update `state/portfolio.json`** atomically (temp + `mv`):
   - subtract `notional_usdc` from `cash_usdc`
   - add/update position with `market_id`, `condition_id`, `token_id`,
     `outcome`, `side`, `shares`, `avg_price`, `mark_price`,
     `market_value_usdc`, `cost_basis_usdc`, `opened_at`, `updated_at`,
     `status: "open"`.

5. **Never** import a Polymarket SDK in the paper branch. **Never** read
   `WALLET_SEED`. **Never** sign anything.

## Mainnet branch — fail-closed preconditions

Every item must pass; first failure → `preflight_failed` event, exit. The
agent must never infer eligibility, use a VPN, or bypass platform
restrictions.

1. `mode.network == "mainnet"`.
2. `mode.observation_only == false`.
3. `mode.mainnet_attestation.polymarket_eligible == true`, non-null
   `attested_by`, `attested_at`.
4. Env vars present (check only — never print): `WALLET_SEED`,
   `POLYMARKET_FUNDER_ADDRESS`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
5. `skills/polymarket/SKILL.md` exists after
   `git submodule update --init --recursive`. Else halt.
6. SDK install/import:
   `uvx --from py-clob-client python -c 'from py_clob_client.client import ClobClient'`
   (fallback `pip install py-clob-client`). Install/import fail → preflight.
7. Initialize client per `skills/polymarket/authentication.md`. Confirm
   wallet address derives, API creds via `createOrDeriveApiCreds`, and the
   wallet's USDC allowance for the Polymarket exchange contract is ≥
   `notional + fees`.
8. **Funder check:** derived wallet address matches
   `POLYMARKET_FUNDER_ADDRESS` (case-insensitive). Mismatch → preflight.
9. **Re-check market + decision:** market open and unpaused, token id
   matches intended outcome, midpoint fresh (≤15 min), all of `sizing`'s
   guardrail formulas still pass against current NAV.
10. **Idempotency search:** if any prior `mainnet_order_submitted` or
    `mainnet_fill` carries the decision's `idempotency_key`, abort and emit
    `decision` with `reason: "idempotency_duplicate"`.
11. **Pre-submit push.** Ensure the `decision` event is committed and
    **pushed** to the memory branch before any SDK call. Use the `persist`
    skill: `git add state/trade-log.jsonl && git commit -m "feat(decision):
    pre-submit <idempotency_key>" && git pull --rebase && git push`. If push
    fails → `preflight_failed` with `reason: "pre_submit_push_failed"`,
    do not submit.

## Mainnet branch — submission

12. **Place a bounded limit BUY** via `createAndPostOrder` (see
    `skills/polymarket/order-patterns.md`):
    - `side: BUY`, `price: midpoint`, `size: shares`, TIF GTC.
    - **No market orders.** **At most one order per cycle.**

13. **Emit `mainnet_order_submitted`** via `journal`:
    ```json
    {"event_type":"mainnet_order_submitted","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<o>","side":"BUY","price":<midpoint>,"shares":<n>,"notional_usdc":<usdc>,"fee_usdc":<est>,"idempotency_key":"<key>","order_id":"<sdk_id>"}
    ```

14. **Poll fill status** briefly (10–30 s). Emit `mainnet_fill` with actual
    filled `shares`, `price`, `fee_usdc`, `order_id`.

15. **Partial fill:** immediately call SDK cancel for the unfilled
    remainder; log cancel result. **If cancel itself fails:** invoke `risk`
    skill to set `halts.json.active = true`, `reason:
    "mainnet_cancel_failed"`, notify Telegram, persist, exit.

16. **Update `state/portfolio.json`** with the **actual** fill (not intended).

17. **Post-submit push** (via `persist` skill). If post-submit push fails,
    invoke `risk` to halt; the pre-submit decision is already durable so a
    retried run sees the idempotency key and will not re-submit.

## Failure modes

- Any preflight fail → `preflight_failed`, no order.
- SDK exception during submit → treat as not-placed; log `preflight_failed`
  with `reason: "sdk_exception"`. Pre-submit decision push protects against
  ghost-order duplicates on retry.
- Cancel failure on partial fill → halt + notify.
- Push failure post-submit → halt + notify.
