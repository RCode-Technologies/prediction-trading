# Guardrails

Human-owned, non-negotiable. Reflection **cannot** edit this file; it surfaces recommendations via daily summary.

## Position sizing — 5% per token

```
existing_token_risk + new_order_notional + estimated_fees <= 0.05 * NAV
new_order_notional + estimated_fees                       <= cash_usdc
```

- `NAV = cash_usdc + Σ(open_position.shares * fresh_mark_price)`.
- Fresh mark = CLOB midpoint with quote `ts <= 15 min` old.
- `existing_token_risk = Σ(position.cost_basis_usdc for same token_id) + Σ(open_order.notional_usdc + fee_usdc for same token_id)`.
- Stale NAV → no new trades.

## Correlation

Related-fact markets (same election/match/regulatory event) share one 5% bucket; aggregate applies. Uncertain correlation → reject.

## Order direction

Long BUY only. SELL only to reduce/close.

## Mark freshness

Quotes >15 min = stale → no sizing, no trade.

## Circuit breaker — -10% / 24h

`rolling_24h_pnl <= -0.10 * baseline_NAV` → write `halts.json.active=true`, log `halt`, notify, commit, push, stop. Baseline = latest `nav_snapshot` with `ts <= now - 24h`, else `starting_capital`. Only humans clear. Unexplained cash delta also halts (v1 = no deposits/withdrawals).

## Research cap — 3 sources/cycle

Shared counter across `skills/research` + `skills/markets`. Includes native WebSearch/WebFetch. Safety re-checks in `sizing`/`trade` don't count.

## Append-only log

`state/trade-log.jsonl`: append only. Never edit prior lines. Each line = valid JSON with `schema_version`, `event_id`, `cycle_id`, `event_type`, `ts`, `mode`.

## Push = success

Every cycle: commit, pull --rebase, push. Never `--force`. No push = `persist_conflict` + notify + non-zero exit.

## Mainnet gate

`skills/trade` is the only skill that reads wallet secrets. Preflights are fail-closed. Never infer Polymarket eligibility, never use VPN, never bypass platform restrictions.

## Secrets

`WALLET_SEED` is the only wallet secret. Presence check only: `[ -n "${WALLET_SEED:-}" ]`. Never print, log, or commit.
