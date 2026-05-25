# `trade_placed`

Sent by `skills/trade` step 14a (mainnet only). One message per fill — never aggregate across cycles.

## Primary template (fill observed, `<tx_hash>` known)

```
📈 *Trade placed* · `mainnet`

*<market_question>*

BUY *<outcome>*
Price       *$<price>*
Shares      *<shares>*
Notional    *$<notional>*

🔗 [View transaction](https://polygonscan.com/tx/<tx_hash>)
🔗 [Open on Polymarket](https://polymarket.com/event/<event_slug>)

Order `<order_id>` · Tx `<tx_hash_short>`
```

## Degraded template (fill polled out, no `<tx_hash>` yet)

```
📈 *Trade placed* · `mainnet` · _settlement pending_

*<market_question>*

BUY *<outcome>*
Price       *$<price>*
Shares      *<shares>*
Notional    *$<notional>*

🔗 [Open on Polymarket](https://polymarket.com/event/<event_slug>)

Order `<order_id>` · settlement tx not yet observed
```

A follow-up `trade_placed` with the full tx link is allowed once the settlement is observed in a later cycle.

## Field reference

| Placeholder         | Source                                                                                       |
| ------------------- | -------------------------------------------------------------------------------------------- |
| `<market_question>` | Gamma `markets.question`, cached on candidate record. Sanitize `*` `_` `` ` `` `[`.          |
| `<outcome>`         | `decision.outcome`. Same sanitization rule.                                                  |
| `<price>`           | `mainnet_fill.price` — actual filled price.                                                  |
| `<shares>`          | `mainnet_fill.shares` — actual filled shares.                                                |
| `<notional>`        | `mainnet_fill.notional_usdc`.                                                                |
| `<tx_hash>`         | `client.get_trades(market=<id>)[i].transaction_hash` (Polygon settlement, `0x…`).            |
| `<tx_hash_short>`   | First 8 + last 6 chars of `<tx_hash>` (e.g. `0x1a2b3c4d…f0a1b2`).                            |
| `<event_slug>`      | Gamma `events.slug`, cached on candidate record.                                             |
| `<order_id>`        | `response["orderID"]` from `create_and_post_order` — Polymarket CLOB ID. **Off-chain reference, NOT a tx hash.** Use it for SDK queries (`get_orders`, `cancel_order`), never for explorer URLs. |
