# Guardrails

Human-owned. Reflection cannot edit this file; recommendations surface via daily summary.

## Position sizing — 5% per token (`skills/sizing`)

```
existing_token_risk + new_order_notional + fees <= 0.05 * NAV
new_order_notional + fees                       <= cash_usdc
```

`NAV = cash + Σ(shares * fresh_mark)`. Fresh mark = CLOB midpoint with `ts ≤ 15min`. `existing_token_risk` includes open positions + open orders on same token. Stale NAV → no new trades.

## Correlation

Related-fact markets (same election/match/regulatory event) share one 5% bucket. Uncertain → reject.

## Order direction

Long BUY only. SELL only to reduce/close.

## Mark freshness

Quotes >15 min stale → no sizing, no trade.

## Circuit breaker — -10% / 24h (`skills/circuit-breaker`)

`rolling_24h_pnl <= -0.10 * baseline_NAV` → halt, log, notify, commit, push, stop. Baseline = latest `nav_snapshot` with `ts ≤ now - 24h`, else `starting_capital`. Only humans clear. Unexplained cash delta also halts.

## Research cap — 3 sources/cycle

Shared between `skills/research` + `skills/markets`. Native WebSearch/WebFetch count. Safety re-checks in `sizing`/`trade` don't.

## Append-only log

`state/trade-log.jsonl`: append only, never edit. Each line = valid JSON with `schema_version`, `event_id`, `cycle_id`, `event_type`, `ts`, `mode`.

## Push = success

Every cycle: one Conventional Commit + pull --rebase + push. No `--force` / `--no-verify`. `--force-with-lease` only for human-directed history consolidation after verifying clean tree + unchanged remote. No push = `persist_conflict`.

## Mainnet gate

`skills/trade` is the only skill that reads wallet secrets. Preflights are fail-closed. Never infer Polymarket eligibility, never VPN, never bypass platform restrictions.

## Secrets

`WALLET_SEED` is the only wallet secret. Presence check only: `[ -n "${WALLET_SEED:-}" ]`. Never print, log, or commit values.
