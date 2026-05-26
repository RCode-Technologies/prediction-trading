---
name: notify
description: Telegram Bot API alerts. Per-mode suppression. Never logs/echoes secrets.
inputs: notification kind + payload
outputs: HTTP POST to api.telegram.org, notification event
---

# Notify

Only outbound human channel. Never block the cycle.

## How Telegram is invoked

Telegram = plain HTTPS `curl` to `https://api.telegram.org/bot<TOKEN>/<method>` via `Bash`. No MCP tool exists. Env vars `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` are injected by the runtime (ADR 0004) — if both present, run step 4a/4b; if either empty, apply the missing-creds rule below. Never substitute Slack/Drive/inline display.

## Suppression rules

- **Paper:** `routine_summary`, `discovery_summary`, `daily_summary`, `weekly_recap`, `circuit_breaker`, `null_cycle` (v2), `liveness_gap` (v2). Skip per-trade.
- **Mainnet:** `routine_summary`, `discovery_summary`, `trade_placed`, `daily_summary`, `weekly_recap`, `circuit_breaker`, `preflight_failed`, `persist_conflict`, `phase_missed`, `null_cycle` (v2), `liveness_gap` (v2).
- **Suppression-exempt (always send if creds present, paper + mainnet):** `null_cycle`, `liveness_gap`, `circuit_breaker`, `persist_conflict`. These exist to break silent-failure modes; never suppress them by mode.

Keep automated Telegram concise. If a routine opened no positions and has no human action item, prefer a one-line `routine_summary` over a verbose recap.

Missing `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID`:
- Paper → silently skip.
- Mainnet → handled as `preflight_failed` upstream by `trade`.

## Steps

1. Resolve which kinds to send based on mode + caller request.
2. **`daily_summary` dedupe.** Grep trade-log for prior `notification kind:"daily_summary"` with `date:<today UTC>` → skip if present.
3. **Compose payload.** Load **only** the template file matching the `kind` being sent (see § Templates). Substitute placeholders; sanitize external content (`<market>`, `<reason>`, leads) for unbalanced `*` / `_` / `` ` ``. Never include secrets, wallet addrs, raw env vars, or token-bearing URLs.
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

## Templates

One file per kind/variant — **load exactly the one you need, never preload the directory**. Resolve the variant from the data in hand (e.g. count candidates before choosing between the empty / candidates `discovery_summary` files); load the file; substitute; send.

| Kind                | Variant / when                | Template                                                                                |
| ------------------- | ----------------------------- | --------------------------------------------------------------------------------------- |
| `routine_summary`   | no-action one-liner           | [templates/routine_summary.md](templates/routine_summary.md)                            |
| `discovery_summary` | 0 candidates                  | [templates/discovery_summary_empty.md](templates/discovery_summary_empty.md)            |
| `discovery_summary` | 1–3 candidates                | [templates/discovery_summary_candidates.md](templates/discovery_summary_candidates.md)  |
| `daily_summary`     | no positions + no fills       | [templates/daily_summary_empty.md](templates/daily_summary_empty.md)                    |
| `daily_summary`     | positions open or fills today | [templates/daily_summary_full.md](templates/daily_summary_full.md)                      |
| `weekly_recap`      | Sundays                       | [templates/weekly_recap.md](templates/weekly_recap.md)                                  |
| `trade_placed`      | mainnet only, per fill        | [templates/trade_placed.md](templates/trade_placed.md)                                  |
| `circuit_breaker`   | any breaker trip              | [templates/circuit_breaker.md](templates/circuit_breaker.md)                            |
| `preflight_failed`  | trade preflight gate          | [templates/preflight_failed.md](templates/preflight_failed.md)                          |
| `persist_conflict`  | push rejected after retry     | [templates/persist_conflict.md](templates/persist_conflict.md)                          |
| `phase_missed`      | per missed phase              | [templates/phase_missed.md](templates/phase_missed.md)                                  |
| `null_cycle`        | v2 — routine missed its floor | [templates/null_cycle.md](templates/null_cycle.md)                                      |
| `liveness_gap`      | v2 — scheduler skipped cycles | [templates/liveness_gap.md](templates/liveness_gap.md)                                  |

### Markdown safety (applies to every template)

- Balance every `*`, `_`, `` ` ``. Unbalanced → `400 Bad Request: can't parse entities`.
- No nested formatting (no bold inside code, no code inside bold).
- Wrap identifiers / paths / mode tag in backticks so `_` doesn't parse as italic.
- External content (`<market>`, `<reason>`, leads) is untrusted: strip or backtick-wrap the four chars above before substitution.

## Failure modes

- Telegram error → retry once with backoff → log `notification` `kind:"<original>_failed"` and continue.
- `sendMessage` returns `400 message is too long` → retry **once** as `sendDocument` (step 4b) with the same payload written to a temp file; this is the canonical recovery path, not a special case.
- Missing creds (paper) → silent skip.
- Missing creds (mainnet) → caller (`trade`) handles as preflight upstream.

## Operator-invoked send (out-of-cycle)

When a human asks the agent to deliver a file from the repo to Telegram (e.g. "send README.md", "send today's recap") because a routine didn't reach them: this is **not** suppressed by the per-mode rules in `Suppression rules` — those govern automated cycle traffic. Resolve the file path, send via step 4b (`sendDocument`) regardless of size, and append a `notification kind:"operator_send" path:"<repo-relative>" transport:"sendDocument"` event. Env vars come from the runtime environment per ADR 0004; the agent does **not** read `.env` files itself.
