# PRD — v1 Instruction Pack

- **Status:** Approved (planning)
- **Date:** 2026-05-24
- **Owner:** Theo
- **Related plan:** [../plans/v1-instruction-pack.md](../plans/v1-instruction-pack.md)

## Problem

An autonomous Polymarket trading agent must operate in stateless, ephemeral scheduled
agent environments, with v1 deployed as a Claude Code cloud routine. Each run wakes
up fresh — no in-memory state, no `.env` file, no persistent process. The only
durable substrate is the GitHub repository branch the routine can write to. The agent
must research markets, strategize, execute trades, learn from outcomes, and respect
hard risk limits — all without ever exceeding a tight token budget per cycle.

## Goals

1. **Persistent memory via repo** — every decision, trade, research note, state
   update, and strategy revision is committed and pushed to the configured memory
   branch before the cycle ends.
2. **Minimal boot context** — the agent loads <600 lines / ~15k tokens before it can
   decide what to do next. `CLAUDE.md` is a one-line compatibility shim that tells
   Claude Code to read `AGENTS.md`; `AGENTS.md` is the model-agnostic boot prompt.
   The rest of the knowledge base (skills, routines, history) is loaded only on demand.
3. **Hard risk guardrails** — per-position cap (5% of portfolio), rolling 24h loss
   circuit-breaker (-10%) that halts trading and notifies via Telegram.
4. **Safe-by-default rollout** — paper-trade phase first with real Polymarket market
   data and synthetic fills; mainnet enabled only via explicit flag flip.
5. **Self-improvement loop** — a daily reflection routine reads recent outcomes and edits
   the active strategy file, snapshotting the previous version into history.
6. **Operator visibility** — Telegram alerts for trades placed (mainnet), daily summary,
   and circuit-breaker. Repo is the source of truth for full detail.
7. **Autonomous financial strategy modeling** — the agent acts as a capable wealth
   manager: it designs, formalizes, and iterates financial strategies from first
   principles (probability calibration, Kelly sizing, market microstructure, correlation
   management). Strategy depth is not fixed at boot — it grows as the agent accumulates
   research, observed market behavior, and reflection-driven revisions. The human sets
   risk limits and mode; all strategy content is agent-owned.

## Non-Goals (v1)

- GitHub Actions cron wiring, Dockerfiles, CI pipelines.
- Backtesting harness, web dashboards.
- Multi-account / multi-wallet support.
- Mainnet trading turned on by default.
- Application code in any language — v1 is a **markdown instruction pack only**.

## Users

- **Primary user:** the agent itself, invoked hourly by a Claude Code cloud routine
  for v1. Claude Code sees `CLAUDE.md`, which tells it to read `AGENTS.md`; other
  agents can read `AGENTS.md` directly. The agent follows routines and — crucially —
  acts as the financial mind of the system. It is expected to reason like a
  quant/wealth manager: model probability distributions, manage position correlation,
  apply sizing frameworks (Kelly, fractional Kelly), recognize mispriced markets, and
  continuously refine these models through research and outcome analysis. It is not a
  rules-executor; it is a financial reasoner that operates within guardrails.
- **Supervisor:** the human (Theo). Provides wallet credentials and API keys, flips
  paper→mainnet, configures the Claude cloud routine environment and branch-push
  permission, sets guardrails, reviews logs, receives Telegram alerts, pauses via
  `state/halts.json`. Does not write strategy content — that belongs to the agent.

## Acceptance Criteria

1. Repo skeleton exists with `CLAUDE.md`, `AGENTS.md`, `routines/`, `config/`,
   `state/`, `strategy/`, `research/`, and `skills/polymarket/` (git submodule of
   `Polymarket/agent-skills`).
2. `CLAUDE.md` contains exactly one concise instruction to read `AGENTS.md`.
   Cold-launching any compatible coding agent at the repo root with no extra prompt
   produces a coherent "what am I, what do I do next" answer from `AGENTS.md`.
3. The Claude cloud routine setup is documented in `README.md`: schedule is hourly,
   the selected repo has unrestricted branch pushes enabled for the memory branch,
   required/optional environment variables are configured in the cloud environment,
   allowed network domains are listed, and unnecessary connectors are excluded.
4. A paper-mode dry-run cycle (no API keys, fake portfolio) produces: a research note,
   a candidate-market ranking, prediction log entries during the first 48h observation
   window, paper-fill log entries only after observation ends, a stubbed Telegram
   payload, and a clean git commit + push. It performs zero non-git network writes.
5. Seeding 5 fake paper trades and triggering `routines/80-reflect.md` modifies
   `strategy/current.md` and writes a snapshot into `strategy/history/`.
6. `grep -E "5%|10%"` finds each guardrail in ≥2 places (`AGENTS.md`,
   `config/guardrails.md`, relevant routines).
7. `grep -ri "private_key|signer|createAndPostOrder" routines/` returns hits only
   inside `50-execute-trade.md`'s mainnet branch.
8. `wc -l AGENTS.md` < 200; total always-loaded boot context < ~600 lines.
9. `README.md` enumerates every env var the human must configure in the Claude cloud
   environment for routines, or `export` locally for manual dry runs — split by mode:
   - **Paper** (optional): `BRAVE_API_KEY`, `TAVILY_API_KEY`, `SERPER_API_KEY`.
     `PERPLEXITY_API_KEY` and `X_BEARER_TOKEN` are deferred for v1 due to
     cost/access constraints.
   - **Mainnet** (required): `WALLET_SEED` (BIP-39 mnemonic) plus
     `POLYMARKET_FUNDER_ADDRESS`.
   - **Notifications** (both modes): `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
10. State files use explicit schemas for `portfolio.json`, `halts.json`,
    `cycle-index.json`, `lock.json`, and every `trade-log.jsonl` event type. Every
    routine validates JSON before committing.
11. Every cycle uses a unique `cycle_id`, acquires a repo-backed lock before trading,
    skips or recovers stale locks deterministically, and uses idempotency keys so a
    retried routine cannot place the same mainnet order twice.
12. Mainnet order placement is fail-closed unless all preflights pass: mode is
    `mainnet`, observation is off, human Polymarket eligibility attestation is true,
    `WALLET_SEED` and `POLYMARKET_FUNDER_ADDRESS` are present, Telegram notification
    credentials are present, wallet/API/allowance checks pass, market prices are fresh,
    and all guardrail formulas pass.

## Out-of-Scope / Deferred

- Automatic strategy promotion (mainnet flip stays human-driven for v1).
- Multi-market portfolio optimization (v1 treats each candidate independently).
- Reflection editing guardrails (locked to strategy-only by `adrs/0005`).

## Success Signal

After 48h of paper-mode running hourly, the trade-log contains predictions on
≥10 distinct markets, the strategy file has at least one reflection-driven revision,
and no guardrail violations are logged.
