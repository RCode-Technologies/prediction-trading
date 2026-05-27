---
name: notify
description: Telegram Bot API alerts via curl. Per-mode suppression. Never logs or echoes secrets.
inputs: notification kind + payload
outputs: HTTP POST to api.telegram.org, notification event
---

# Notify

Only outbound human channel. Never block the cycle.

## Transport

Plain HTTPS `curl` to `https://api.telegram.org/bot<TOKEN>/<method>`. No MCP. `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` injected by runtime (ADR 0004).

## Suppression

- **Paper:** `routine_summary`, `discovery_summary`, `daily_summary`, `weekly_recap`, `circuit_breaker`, `null_cycle`, `liveness_gap`. Per-trade suppressed.
- **Mainnet:** all of paper + `trade_placed`, `preflight_failed`, `persist_conflict`, `phase_missed`.
- **Suppression-exempt (always send if creds present):** `null_cycle`, `liveness_gap`, `circuit_breaker`, `persist_conflict`. These break silent-failure modes.
- Missing creds in paper → silent skip. Missing creds in mainnet → handled by `trade` as `preflight_failed`.

## Steps

1. Resolve kinds to send (mode + caller).
2. **`daily_summary` dedupe.** Grep trade-log for prior `notification kind:"daily_summary"` with `date:<today>` → skip if present.
3. **Compose payload.** Load only the template file matching the `kind` (see § Templates). Substitute placeholders; sanitize external content (`<market>`, `<reason>`, leads) for unbalanced `*` `_` `` ` ``. Never include secrets, wallet addrs, raw env vars, token-bearing URLs.
4. **Pick transport by size.** Telegram `sendMessage` caps `text` at 4096 chars (`printf '%s' "$payload" | wc -c`).
   - ≤4096 → `sendMessage` (4a).
   - >4096 or sending a repo file → `sendDocument` (4b). Don't chunk-send multiple messages.

4a. **`sendMessage`** (text ≤4096):
   ```bash
   curl -sS -X POST \
     "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
     --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
     --data-urlencode "text=<payload>" \
     --data-urlencode "parse_mode=Markdown"
   ```

4b. **`sendDocument`** (large text or file). Existing file: attach by path. Else write payload to temp file first. Caption ≤1024 chars:
   ```bash
   curl -sS -X POST \
     "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendDocument" \
     -F "chat_id=${TELEGRAM_CHAT_ID}" \
     -F "document=@<path>" \
     -F "caption=<≤1024-char summary>"
   ```
   Never echo the token. Never log token-bearing URLs. Check `ok` field — 200 with `ok:false` is still failure; log as `notification kind:"<original>_failed"`.

5. **`notification` event** via `journal`:
   ```json
   {"event_type":"notification","kind":"<kind>","transport":"sendMessage|sendDocument","date":"<YYYY-MM-DD>"}
   ```

## Templates (load only the one needed)

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
| `null_cycle`        | routine missed its floor      | [templates/null_cycle.md](templates/null_cycle.md)                                      |
| `liveness_gap`      | scheduler skipped cycles      | [templates/liveness_gap.md](templates/liveness_gap.md)                                  |

### Markdown safety (every template)

- Balance `*`, `_`, `` ` ``. Unbalanced → `400: can't parse entities`.
- No nested formatting.
- Wrap identifiers / paths / mode tag in backticks.
- External content untrusted — strip or backtick-wrap before substitution.

## Failure modes

- Telegram error → retry once with backoff → log `notification kind:"<original>_failed"` and continue.
- `400 message is too long` → retry once as `sendDocument` (4b) with payload in temp file.
- Missing creds (paper) → silent skip. Missing creds (mainnet) → caller handles as preflight.

## Operator-invoked send (out-of-cycle)

Human asks to deliver a repo file to Telegram (e.g. "send README.md"). Not suppressed by mode rules. Resolve path, send via step 4b regardless of size, append `notification kind:"operator_send" path:"<repo-relative>" transport:"sendDocument"`.
