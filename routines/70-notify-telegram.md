# 70 — Notify Telegram

**Trigger:** invoked from the dispatch in `00-wake-up.md` near the end of the
cycle, and from `99-circuit-breaker.md` when a halt fires.

**Reads:** `config/mode.json`, env vars (presence only): `TELEGRAM_BOT_TOKEN`,
`TELEGRAM_CHAT_ID`. Recent `state/trade-log.jsonl` for content.

**Writes:** `state/trade-log.jsonl` (`notification` event). No file in `state/`
or `config/` is mutated except the log.

## Suppression rule (per ADR 0008)

- **Paper mode:** send **only** `daily_summary` and `circuit_breaker` events.
  Skip per-trade alerts entirely.
- **Mainnet mode:** send `trade_placed`, `daily_summary`, `circuit_breaker`,
  `preflight_failed`, and `persist_conflict`.

If `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID` is missing in mainnet mode, this
is a preflight failure (handled in `50`). In paper mode, missing tokens just
skip all alerts.

## Steps

1. **Determine which messages to send.** Iterate candidate notification types:
   - `trade_placed` — only if mainnet AND `mainnet_order_submitted` or
     `mainnet_fill` is in this cycle's events.
   - `daily_summary` — once per UTC date. Check the trade-log for a prior
     `notification` event with `kind: "daily_summary"` and the same UTC date.
     If found, skip.
   - `circuit_breaker` — only if `99-circuit-breaker.md` set
     `halts.json.active = true` this cycle.
   - `preflight_failed` (mainnet) — if such an event was logged this cycle.
   - `persist_conflict` (mainnet) — if such an event was logged this cycle.

2. **Compose payloads** (markdown safe; do NOT include secret values, wallet
   addresses, raw env vars, or full URLs with tokens):

   - `daily_summary`:
     ```
     [<mode>] Daily summary <YYYY-MM-DD>
     NAV: $<nav> (Δ24h: <pct>%)
     Cycles run: <n>
     Forecasts: <n>  Paper fills: <n>  Mainnet fills: <n>
     Open positions: <n>  Cash: $<cash>
     Top movers: <list>
     ```
   - `trade_placed`:
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
   - `preflight_failed`: which check, brief reason, no secrets.
   - `persist_conflict`: branch, last commit attempted.

3. **Send via Bot API:**
   ```
   curl -sS -X POST \
     "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
     --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
     --data-urlencode "text=<payload>" \
     --data-urlencode "parse_mode=Markdown"
   ```
   Never log the URL with the token. Never echo `$TELEGRAM_BOT_TOKEN`.

4. **Append a `notification` event** for each message actually sent:
   ```json
   {"schema_version":1,"event_id":"<cycle_id>-notification-<i>","cycle_id":"<cycle_id>","event_type":"notification","ts":"<now>","mode":"<network>","kind":"<daily_summary|trade_placed|circuit_breaker|preflight_failed|persist_conflict>","date":"<YYYY-MM-DD>"}
   ```

## Failure modes

- **Telegram API error:** retry once with backoff. If still failing, do not
  block the cycle; log a single `notification` event with `kind:
  "<original>_failed"` and continue.
- **Missing credentials in paper mode:** silently skip.
- **Missing credentials in mainnet mode:** handled as preflight failure in `50`.
