---
name: notify
description: Telegram Bot API alerts. Per-mode suppression rules (paper sends only daily summary + circuit-breaker per ADR 0008). Never logs or echoes secrets.
inputs: notification kind + payload data
outputs: HTTP POST to api.telegram.org, notification event in trade-log
---

# Notify

Telegram alerts. The agent's only outbound human channel.

## Suppression rules (ADR 0008)

- **Paper:** send only `daily_summary` (from end-of-day routine) and
  `circuit_breaker`. **Skip per-trade alerts.**
- **Mainnet:** send `trade_placed`, `daily_summary`, `weekly_recap`,
  `circuit_breaker`, `preflight_failed`, `persist_conflict`,
  `phase_missed`.

If `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID` is absent:
- **Paper:** silently skip.
- **Mainnet:** handled as a `preflight_failed` in `trade` skill.

## Steps

1. **Resolve which kinds to send** based on mode + the calling routine's
   request list.

2. **Daily-summary dedupe.** Grep `state/trade-log.jsonl` for a prior
   `notification` event with `kind: "daily_summary"` and `date: <today UTC>`.
   If present, skip.

3. **Compose payloads** (markdown-safe; never include secrets, wallet
   addresses, raw env vars, or token-bearing URLs):

   - `daily_summary`:
     ```
     [<mode>] Daily summary <YYYY-MM-DD>
     NAV: $<nav> (Δ24h: <pct>%)
     Cycles run: <n> / 4 phases
     Forecasts: <n>  Paper fills: <n>  Mainnet fills: <n>
     Open positions: <n>  Cash: $<cash>
     Top movers: <list>
     ```
   - `weekly_recap`:
     ```
     [<mode>] Weekly recap <YYYY-Www>
     NAV: $<nav> (Δ7d: <pct>%)
     Total fills: <n>  Hit rate: <pct>%  Brier: <score>
     Best call: <market> (+<usdc>)
     Worst call: <market> (-<usdc>)
     Strategy version: <vN>
     ```
   - `trade_placed` (mainnet only):
     ```
     [mainnet] Order placed
     Market: <question>
     Outcome: <label>  Side: BUY  Price: <p>  Shares: <n>  Notional: $<usdc>
     Order id: <id>
     ```
   - `circuit_breaker`:
     ```
     [<mode>] CIRCUIT BREAKER — trading halted
     Reason: <reason>  Triggered at: <ts>
     Rolling 24h P&L: <pct>%
     Resume requires manual edit of state/halts.json.
     ```
   - `preflight_failed`: which check + brief reason. No secrets.
   - `persist_conflict`: branch + last commit attempted.
   - `phase_missed`: which phase + last successful timestamp.

4. **Send:**
   ```bash
   curl -sS -X POST \
     "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
     --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
     --data-urlencode "text=<payload>" \
     --data-urlencode "parse_mode=Markdown"
   ```
   Never echo `$TELEGRAM_BOT_TOKEN`. Never log the URL with the token in it.

5. **Emit a `notification` event** via `journal` for each message sent:
   ```json
   {"event_type":"notification","kind":"<kind>","date":"<YYYY-MM-DD>"}
   ```

## Outputs to caller

`{sent: [...], skipped: [...]}`.

## Failure modes

- **Telegram API error:** retry once with backoff. Still failing → log
  `notification` event with `kind: "<original>_failed"` and continue. Do
  not block the cycle.
- **Missing creds (paper):** silently skip; do not log a noisy failure.
- **Missing creds (mainnet):** caller (`trade` skill) treats as preflight
  failure upstream.
