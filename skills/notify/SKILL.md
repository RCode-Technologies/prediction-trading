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
4. **Pick transport by size.** Telegram `sendMessage` hard-caps `text` at **4096 chars** — longer payloads return `400 Bad Request: message is too long`. Measure the composed payload with `printf '%s' "$payload" | wc -c`.
   - **≤4096 chars** → `sendMessage` (step 4a).
   - **>4096 chars or sending a file from the repo** (recap, README, scorecard, log excerpt) → `sendDocument` with the content as a file attachment (step 4b). Do **not** try to chunk and emit multiple `sendMessage` calls — out-of-order delivery and per-chunk markdown parsing both break readability.
4a. **`sendMessage` (text ≤4096):**
   ```bash
   curl -sS -X POST \
     "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
     --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
     --data-urlencode "text=<payload>" \
     --data-urlencode "parse_mode=Markdown"
   ```
4b. **`sendDocument` (large text or file):** if you're sending a file that already exists on disk, attach it by path; otherwise write the payload to a temp file first. Caption is itself capped at 1024 chars.
   ```bash
   curl -sS -X POST \
     "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendDocument" \
     -F "chat_id=${TELEGRAM_CHAT_ID}" \
     -F "document=@<path/to/file>" \
     -F "caption=<≤1024-char summary>"
   ```
   Never echo `$TELEGRAM_BOT_TOKEN`. Never log a URL with the token. Capture HTTP status and `ok` field from the response body to detect silent failures — a 200 with `ok:false` (e.g. `error_code:400, description:"message is too long"`) is still a failure and must be logged as `notification kind:"<original>_failed" reason:"<description>"`.
5. **`notification` event** via `journal`:
   ```json
   {"event_type":"notification","kind":"<kind>","transport":"sendMessage|sendDocument","date":"<YYYY-MM-DD>"}
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
- `sendMessage` returns `400 message is too long` → retry **once** as `sendDocument` (step 4b) with the same payload written to a temp file; this is the canonical recovery path, not a special case.
- Missing creds (paper) → silent skip.
- Missing creds (mainnet) → caller (`trade`) handles as preflight upstream.

## Operator-invoked send (out-of-cycle)

When a human asks the agent to deliver a file from the repo to Telegram (e.g. "send README.md", "send today's recap") because a routine didn't reach them: this is **not** suppressed by the per-mode rules in `Suppression rules` — those govern automated cycle traffic. Resolve the file path, send via step 4b (`sendDocument`) regardless of size, and append a `notification kind:"operator_send" path:"<repo-relative>" transport:"sendDocument"` event. Env vars come from the runtime environment per ADR 0004; the agent does **not** read `.env` files itself.
