---
name: notify
description: Telegram Bot API alerts. Per-mode suppression. Never logs/echoes secrets.
inputs: notification kind + payload
outputs: HTTP POST to api.telegram.org, notification event
---

# Notify

Only outbound human channel. Never block the cycle.

## Suppression rules

- **Paper:** `daily_summary` + `circuit_breaker` only. Skip per-trade.
- **Mainnet:** `trade_placed`, `daily_summary`, `weekly_recap`, `circuit_breaker`, `preflight_failed`, `persist_conflict`, `phase_missed`.

Missing `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID`:
- Paper → silently skip.
- Mainnet → handled as `preflight_failed` upstream by `trade`.

## Steps

1. Resolve which kinds to send based on mode + caller request.
2. **`daily_summary` dedupe.** Grep trade-log for prior `notification kind:"daily_summary"` with `date:<today UTC>` → skip if present.
3. **Compose payload** (markdown-safe; never include secrets, wallet addrs, raw env vars, token-bearing URLs).
4. **Send:**
   ```bash
   curl -sS -X POST \
     "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
     --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
     --data-urlencode "text=<payload>" \
     --data-urlencode "parse_mode=Markdown"
   ```
   Never echo `$TELEGRAM_BOT_TOKEN`. Never log URL with token.
5. **`notification` event** via `journal`:
   ```json
   {"event_type":"notification","kind":"<kind>","date":"<YYYY-MM-DD>"}
   ```

## Payload shapes

- `daily_summary`: `[<mode>] Daily summary <YYYY-MM-DD>` + NAV (Δ24h%), cycles N/4, forecasts/paper_fills/mainnet_fills counts, open positions + cash, top movers.
- `weekly_recap`: `[<mode>] Weekly recap <YYYY-Www>` + NAV (Δ7d%), total fills, hit rate, Brier, best/worst call, strategy version.
- `trade_placed` (mainnet): market, outcome, side BUY, price, shares, notional, order_id.
- `circuit_breaker`: `[<mode>] CIRCUIT BREAKER — trading halted` + reason, triggered_at, 24h P&L%, "Resume requires manual edit of state/halts.json".
- `preflight_failed`: which check + brief reason (no secrets).
- `persist_conflict`: branch + last commit attempted.
- `phase_missed`: which phase + last successful ts.

## Failure modes

- Telegram error → retry once with backoff → log `notification` `kind:"<original>_failed"` and continue.
- Missing creds (paper) → silent skip.
- Missing creds (mainnet) → caller (`trade`) handles as preflight upstream.
