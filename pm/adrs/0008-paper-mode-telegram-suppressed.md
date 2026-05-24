# 0008 — Paper mode suppresses per-trade Telegram alerts

- **Status:** Accepted
- **Date:** 2026-05-24
- **Related:** PRD v1-instruction-pack, routine 70-notify-telegram

## Context

Paper-mode trades can fire frequently (hourly schedule × multiple candidates).
Sending Telegram on each would create alert fatigue and obscure mainnet alerts
later.

## Decision

`routines/70-notify-telegram.md` checks `config/mode.json.network`:

- **Paper**: send only **daily summary** and **circuit-breaker** events. Per-trade
  notifications are skipped. The trade is still logged to `state/trade-log.jsonl`
  and committed to git.
- **Mainnet**: send **all three** event types — trade placed, daily summary,
  circuit-breaker.

## Consequences

- Telegram remains useful as a signal even during high-frequency paper runs.
- Repo (trade-log + commits) is the source of truth for full paper-mode activity.
- Switching to mainnet automatically restores per-trade alerts — no separate config.
