# 0004 — Env vars injected by cloud environment or shell; no `.env`

- **Status:** Accepted
- **Date:** 2026-05-24
- **Related:** PRD v1-instruction-pack

## Context

The agent runs in CI-style ephemeral environments. In v1 cloud routine runs, secrets
are configured in the Claude cloud environment. In manual local dry runs, the human
may export the same vars into the shell. There is no `.env` file. We considered
keeping a `config/env-vars.md` enumerating expected vars for the agent to consult.

The two modes (paper, mainnet) have meaningfully different key requirements:
paper mode only needs optional research keys to look things up; mainnet requires
wallet credentials to sign on-chain orders.

## Decision

- No `.env` file. No `config/env-vars.md`.
- Routines check env var presence inline with shell parameter expansion, for example
  `[ -n "${WALLET_SEED:-}" ]`. They must never print, log, or commit secret values.
- The single human-facing enumeration of required env vars lives in the repo
  `README.md`.

### Paper mode — required

None. The agent can run a full cycle with no keys at all (reads Polymarket public
APIs unauthenticated; skips real-money signing).

### Paper mode — optional (research)

Providing at least one improves market intelligence. The agent tries each in order
and falls back gracefully to Polymarket public data if none is set. Perplexity and
X/Twitter API integrations are deferred for v1 due to cost/access constraints; the
agent must not require or request those keys.

| Env var | Provider |
|---|---|
| `BRAVE_API_KEY` | Brave Search |
| `TAVILY_API_KEY` | Tavily Search |
| `SERPER_API_KEY` | Serper (Google proxy) |

### Mainnet — required (in addition to any research keys above)

These must be configured in the Claude cloud environment for routines, or exported
locally for manual dry runs. The agent checks for their presence at the top of
`routines/50-execute-trade.md` mainnet branch and aborts with a Telegram alert if
either is missing.

| Env var | Purpose |
|---|---|
| `WALLET_SEED` | BIP-39 mnemonic seed phrase for the Polymarket trading wallet |
| `POLYMARKET_FUNDER_ADDRESS` | On-chain address that funds USDC collateral |

> The agent never logs, commits, or echoes these values. `routines/50-execute-trade.md`
> is the only routine permitted to read wallet secret values (ADR 0003).

### Notifications (both modes)

| Env var | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot API token for outbound alerts |
| `TELEGRAM_CHAT_ID` | Target chat/channel ID |

Optional in paper mode (per-trade alerts suppressed, ADR 0008), but required to
receive daily summary and circuit-breaker events. Required in mainnet mode because
mainnet preflight failures and real-order events must be visible to the human.

## Consequences

- Smaller boot context (no enumeration file to load).
- Secret hygiene: nothing referencing actual values is ever in the repo.
- Paper-mode dry runs need zero keys — easy local testing without any credentials.
- Mainnet promotion is gated on the human explicitly configuring wallet credentials
  and the eligibility attestation.
- If a new env var is added later, both `README.md` and this ADR must be updated.
