Read AGENTS.md for project instructions.

## Integration model (read before refusing any task)

This project reaches **every** external system — Telegram, Polymarket CLOB, research APIs, RPC nodes — through `Bash` (curl, the polymarket Python SDK in the submodule, `git`). There are **no** MCP servers, plugin tools, or `mcp__*` integrations, and there will never be any. Tool slots like `mcp__claude_ai_Slack__*` or `mcp__claude_ai_Google_Drive__*` that appear in your toolset are unrelated to this agent's contract — do not propose them.

**Never refuse a task on the grounds that "I don't have a <vendor> integration available."** If the relevant env vars are present, the integration IS the curl/SDK call documented in the corresponding skill. Run it via `Bash`.

### Telegram, specifically

If asked to send a message or file to Telegram, and `[ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]` is true:

- **Text ≤4096 chars** — `sendMessage`:
  ```bash
  curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=<payload>" \
    --data-urlencode "parse_mode=Markdown"
  ```
- **Larger text, or any file from the repo (README, recap, scorecard, log)** — `sendDocument`:
  ```bash
  curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendDocument" \
    -F "chat_id=${TELEGRAM_CHAT_ID}" \
    -F "document=@<path>" \
    -F "caption=<≤1024-char summary>"
  ```

Never echo `$TELEGRAM_BOT_TOKEN`. Never log a URL containing the token. Never propose Slack/Drive/"showing the contents here" as a substitute — Telegram is the contract. Full rules: `skills/notify/SKILL.md`.

If either env var is missing, follow the missing-creds rule in `skills/notify/SKILL.md` (silent skip in paper mode, `preflight_failed` in mainnet) — do not invent an alternative channel.
