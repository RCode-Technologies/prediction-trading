# 0003 — Paper-mode default with mainnet behind a flag

- **Status:** Accepted
- **Date:** 2026-05-24
- **Related:** PRD v1-instruction-pack

## Context

Real funds are involved ($54 USDC initial). The agent self-modifies its strategy via
the reflection routine, so wrong-strategy risk is non-trivial. We need a way to let
the agent run continuously and gather data without risking capital, then promote to
mainnet deliberately.

## Decision

`config/mode.json` carries `network`, `cadence_minutes`, `observation_only`,
`observation_started_at`, `observation_hours`, and `mainnet_attestation`.

- **Paper mode**: real Polymarket market data (Gamma + CLOB read APIs, no auth),
  synthetic fills at observed mid-price after the 48h observation window. Default.
- **Mainnet mode**: requires explicit human flip of `mode.json.network = "mainnet"`
  AND presence of `WALLET_SEED` + `POLYMARKET_FUNDER_ADDRESS` env vars.
- **First 48h paper-mode is `observation_only: true`** — agent records predictions
  but does not even paper-trade, to give reflection clean data. `00-wake-up.md`
  automatically flips it to `false` after `observation_started_at + observation_hours`
  and commits that state change.
- **Eligibility gate**: mainnet execution also requires
  `mainnet_attestation.polymarket_eligible = true` with human-filled attestation
  fields. The agent must not infer eligibility or bypass a platform restriction.
- **Order direction**: v1 opens only long BUY positions. SELL orders may reduce or
  close existing positions only; no short exposure.

`routines/50-execute-trade.md` branches on `mode.json.network`. The mainnet branch is
the only file in the repo that may touch private keys or signing operations.

## Consequences

- Safe by default — no real funds at risk until human deliberately flips the flag.
- Hourly cadence is the v1 default and matches Claude routine schedule limits.
- Paper data is realistic (real spreads/orderbook) but cannot capture slippage from
  the agent's own size — acceptable given the small bankroll.
