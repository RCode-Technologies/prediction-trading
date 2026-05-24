# Guardrails

Canonical, non-negotiable limits for the trading agent. Edited by humans only.
The reflection routine (`routines/80-reflect.md`) is **forbidden** from
modifying this file (ADR 0005). If the agent thinks a guardrail should change,
it surfaces a recommendation in the daily Telegram summary; the human decides.

## Position sizing — 5% per token

A new order may be placed only if **both** of the following hold:

```
existing_token_risk + new_order_notional + estimated_fees <= 0.05 * NAV
new_order_notional + estimated_fees             <= cash_usdc
```

Where:

- `NAV = cash_usdc + sum(open_position.shares * fresh_mark_price)` and a
  "fresh mark" means a CLOB midpoint whose quote timestamp is ≤15 minutes old.
- `existing_token_risk = sum(open_position.cost_basis_usdc for same token_id)
  + sum(open_order.notional_usdc + open_order.fee_usdc for same token_id)`.

If any position lacks a fresh mark, NAV is `stale` and **no new trades** may
open.

## Correlation bucket

When candidate markets resolve from materially related facts (same election,
same match, same regulatory action), they share **one** 5% risk bucket. The
formula above applies to the aggregate of all positions and orders in the
bucket. If correlation is uncertain, reject the new trade.

## Order direction

v1 may open **only long BUY** positions in outcome tokens. SELL orders are
allowed only to reduce or close an existing position; no short exposure.

## Mark-price freshness — 15 minutes

Quotes older than 15 minutes are stale. Stale → no sizing, no trade. See
`routines/40-decide-and-size.md`.

## Rolling 24h loss circuit breaker — -10%

If `rolling_24h_pnl <= -0.10 * baseline_NAV`, set `state/halts.json.active =
true`, log a `halt` event, notify Telegram, commit, push, and stop. Only a
human can clear the halt. Baseline NAV is the latest `nav_snapshot` with
`ts <= now - 24h`; if none, use `starting_capital`. v1 assumes no deposits
or withdrawals; any appearance of either halts the agent for manual
reconciliation. See `routines/99-circuit-breaker.md`.

## Research cap — 3 sources per cycle

`routines/20-research.md` and `routines/30-analyze-markets.md` share one
counter. Once 3 external sources are consumed, no further research or market
discovery fetches occur this cycle. Safety price re-checks in `40` and `50`
do not count. (ADR 0006.)

## Append-only log discipline

`state/trade-log.jsonl` is append-only. Never edit prior lines. Every line is
a single valid JSON object with `schema_version`, `event_id`, `cycle_id`,
`event_type`, `ts`, `mode`.

## Mandatory commit + push

Every cycle ends with `git add -A && git commit -m "cycle <cycle_id>" && git
pull --rebase && git push`. Never `--force`. A cycle that cannot push is not
successful — log `persist_conflict` and notify. (ADR 0009.)

## Paper-vs-mainnet gate

`routines/50-execute-trade.md` is the **only** routine permitted to read
wallet secret values. Mainnet preconditions in that file are fail-closed:
any missing item produces `preflight_failed` and no order. The agent must
never infer Polymarket eligibility, use a VPN, or bypass platform
restrictions. (ADR 0003.)

## Secrets

`WALLET_SEED` is the only wallet secret env var. The agent checks presence
with `[ -n "${WALLET_SEED:-}" ]` and never prints, logs, or commits the
value. (ADR 0004.)
