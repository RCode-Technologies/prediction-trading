# 50 — Execute Trade

**Trigger:** after `40-decide-and-size.md` produces a `decision` event with
`shares > 0`. Also entered when `observation_only == true` — in that case it
runs the forecast-only branch and exits.

**Reads:** `config/mode.json`, the just-written `decision`, env vars (presence
only). Mainnet branch reads `skills/polymarket/SKILL.md`.

**Writes:** `state/trade-log.jsonl` (`paper_fill` OR `mainnet_order_submitted` +
`mainnet_fill` OR `preflight_failed`), `state/portfolio.json`.

## Branch on `config/mode.json.network`

### Paper branch

1. If `observation_only == true`: exit. The `forecast` event was the output.
   **Do not write paper fills during observation.**

2. After observation: fetch a fresh midpoint (one CLOB book call — does not
   count as a research source) and synthesize a fill at that midpoint.

3. Append a `paper_fill` event:
   ```json
   {"schema_version":1,"event_id":"<cycle_id>-paper_fill-1","cycle_id":"<cycle_id>","event_type":"paper_fill","ts":"<now>","mode":"paper","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<label>","side":"BUY","price":<midpoint>,"shares":<n>,"notional_usdc":<usdc>,"fee_usdc":0,"idempotency_key":"<key>","order_id":null}
   ```

4. Update `state/portfolio.json`: subtract `notional_usdc` from `cash_usdc`,
   add or update the position entry (`market_id`, `condition_id`, `token_id`,
   `outcome`, `side`, `shares`, `avg_price`, `mark_price`, `market_value_usdc`,
   `cost_basis_usdc`, `opened_at`, `updated_at`, `status: "open"`). Write
   atomically (temp file + `mv`).

5. Never import a Polymarket SDK, never read `WALLET_SEED`, never sign anything.

### Mainnet branch — fail-closed preconditions

**Every** item below must pass. The first failure writes a `preflight_failed`
event with the failing item name and exits to `60-log-and-persist.md`. The
agent must never infer eligibility, use a VPN, or bypass platform restrictions.

1. `config/mode.json.network == "mainnet"`.
2. `config/mode.json.observation_only == false`.
3. `config/mode.json.mainnet_attestation.polymarket_eligible == true` with
   non-null `attested_by` and `attested_at`.
4. Env vars present (check only, never print): `WALLET_SEED`,
   `POLYMARKET_FUNDER_ADDRESS`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
5. `skills/polymarket/SKILL.md` exists after
   `git submodule update --init --recursive`. If missing, halt.
6. Install SDK in the ephemeral env: `uvx --from py-clob-client python -c
   'from py_clob_client.client import ClobClient'` (or `pip install
   py-clob-client` if `uvx` unavailable). If install/import fails: preflight
   fail.
7. Initialize client using `WALLET_SEED` per
   `skills/polymarket/authentication.md`. Confirm wallet address derives, API
   credentials retrieved (createOrDeriveApiCreds), and the wallet's USDC
   allowance for the Polymarket exchange contract is sufficient for
   `notional_usdc + fee_usdc`.
8. Funder address check: derived wallet matches
   `POLYMARKET_FUNDER_ADDRESS` (case-insensitive). If not, preflight fail.
9. Re-check market: open, not paused, token id matches the intended outcome,
   midpoint fresh (≤15 min), and the decision still satisfies all of `40`'s
   guardrail formulas (NAV may have moved).
10. Search `state/trade-log.jsonl` for the decision's `idempotency_key`. If a
    prior `mainnet_order_submitted` or `mainnet_fill` carries the same key,
    abort — log a duplicate-suppressed `decision`.
11. **Pre-submit push.** Append the `decision` event (with the `idempotency_key`)
    if not already written, then `git add state/trade-log.jsonl && git commit
    -m "cycle <cycle_id>: pre-submit decision" && git pull --rebase && git
    push`. If the push fails, **do not submit the order**. Log
    `preflight_failed` with reason `pre_submit_push_failed`.

### Mainnet branch — submission

12. Build a bounded **limit** order via `createAndPostOrder` (see
    `skills/polymarket/order-patterns.md`):
    - `side: BUY`, `price: midpoint`, `size: shares`,
    - time-in-force GTC or matching `order-patterns.md` recommendation.
    **No market orders.** Place at most one order per cycle.

13. Append `mainnet_order_submitted`:
    ```json
    {"schema_version":1,"event_id":"<cycle_id>-mainnet_order_submitted-1","cycle_id":"<cycle_id>","event_type":"mainnet_order_submitted","ts":"<now>","mode":"mainnet","market_id":"<id>","condition_id":"<cid>","token_id":"<tid>","outcome":"<label>","side":"BUY","price":<midpoint>,"shares":<n>,"notional_usdc":<usdc>,"fee_usdc":<est>,"idempotency_key":"<key>","order_id":"<sdk_order_id>"}
    ```

14. Wait briefly (e.g. 10–30s) and query fill status. Append `mainnet_fill`
    with actual filled `shares`, `price`, `fee_usdc`, and `order_id`.

15. **Partial fill handling.** If only part of the order filled, immediately
    call the SDK cancel for the remainder. Log the cancel result. If
    cancellation itself fails:
    - Set `halts.json.active = true`, `reason: "mainnet_cancel_failed"`.
    - Notify Telegram.
    - Commit, push, exit.

16. Update `state/portfolio.json` with actual fill (not intended).

17. **Post-submit push.** Commit and push. If push fails, log `persist_conflict`
    and halt. The pre-submit decision is already durable on the remote, so a
    retried run sees the idempotency key and will not re-submit.

## Failure modes

- **Any preflight item fails:** `preflight_failed` event, no order, exit clean.
- **SDK exception during submit:** treat order as not placed; log
  `preflight_failed` with reason `sdk_exception`, exit. (Pre-submit decision
  push has already happened, which is intentional — it prevents a later retry
  from re-submitting the same trade if the order *did* actually go through and
  we just couldn't read the response.)
- **Partial fill cancel failure:** halt + notify (step 15).
- **Push failure post-submit:** halt + notify; idempotency key on the remote
  protects against duplicates.
