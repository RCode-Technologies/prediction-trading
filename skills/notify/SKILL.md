---
name: notify
description: Telegram Bot API alerts. Per-mode suppression. Never logs/echoes secrets.
inputs: notification kind + payload
outputs: HTTP POST to api.telegram.org, notification event
---

# Notify

Only outbound human channel. Never block the cycle.

## How Telegram is invoked (read before anything else)

There is **no Telegram MCP server, no `mcp__telegram__*` tool, no plugin integration**, and there will never be one. Telegram is reached by plain HTTPS `curl` to `https://api.telegram.org/bot<TOKEN>/<method>` using the `Bash` tool. The `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` env vars are injected by the runtime (ADR 0004) and are the entire integration surface.

**Do not refuse a notify request on the grounds that "no Telegram integration is available."** If `[ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]` returns true in `Bash`, you have everything you need — run the `curl` in step 4a/4b. If either var is empty, follow the missing-creds rule (silent skip in paper, `preflight_failed` in mainnet), but never propose Slack/Drive/"showing contents here" as a substitute. Telegram is the contract; alternative channels are out of scope.

## Suppression rules

- **Paper:** `routine_summary`, `discovery_summary`, `daily_summary`, `weekly_recap`, `circuit_breaker`. Skip per-trade.
- **Mainnet:** `routine_summary`, `discovery_summary`, `trade_placed`, `daily_summary`, `weekly_recap`, `circuit_breaker`, `preflight_failed`, `persist_conflict`, `phase_missed`.

Keep automated Telegram concise. If a routine opened no positions and has no human action item, prefer a one-line `routine_summary` over a verbose recap.

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

- `routine_summary`: one line for no-action runs, e.g. `[<mode>] overnight_watch: no open positions; no trades opened.` Include NAV only if it helps explain a halt or cash-only state.
- `discovery_summary`: sent by research/discovery routines. If `candidates_passing_min_edge == 0`, keep it direct: `[<mode>] research_window: no bettable candidates passed checks. Watchlist <N>; leads: <up to 3 short thesis labels or none>.` If candidates passed checks, summarize up to 3 with question, side, edge bps, liquidity, close time, and thesis id, then add `Review: resolution, liquidity, correlation, freshness.`
- `daily_summary`: `[<mode>] Daily summary <YYYY-MM-DD>` + NAV (Δ24h%), cycles N/4, forecasts/paper_fills/mainnet_fills counts, open positions + cash, top movers. If no open positions and no fills, compress to one line: `[<mode>] Daily <YYYY-MM-DD>: NAV <n>; no open positions; no fills; cycles <n>/4.`
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
