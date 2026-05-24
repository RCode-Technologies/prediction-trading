# 0011 — Skills vs Routines split

- **Status:** Accepted
- **Date:** 2026-05-24
- **Related:** PRD v1-instruction-pack, ADR 0010

## Context

The original v1 layout put everything under `routines/00`…`99`. Those files
mixed two concerns:

1. **Scheduling** — what runs at hourly cadence.
2. **Capabilities** — how to fetch from Brave, how to write JSONL events,
   how to sign a Polymarket order.

This conflation made files long, schedule changes touched capability code,
and the boot prompt had to explain both axes. The Polymarket reference
submodule already showed a cleaner pattern: a `SKILL.md` per noun-shaped
capability that the agent loads progressively.

## Decision

Split the repo's instruction files into two distinct kinds:

- **Routines** (`routines/*.md`) — scheduled triggers. Each file:
  - Declares its cron at the top in YAML frontmatter
    (`cron:`, `cron_tz:`, `local_time:`, `phase:`).
  - Reads as a step-by-step playbook that **invokes skills in order**.
  - Stays short (~50–80 lines). Contains no API mechanics; only
    orchestration.
- **Skills** (`skills/<name>/SKILL.md`) — reusable noun-shaped capabilities.
  Each file:
  - Has the same SKILL.md frontmatter pattern as the upstream
    `skills/polymarket/SKILL.md` submodule (`name`, `description`,
    `inputs`, `outputs`).
  - Describes a single capability in detail (API mechanics, formulas, error
    cases).
  - Is loaded **on demand only** by the routine that needs it. Never
    auto-loaded at boot.

v1.1 ships these skills:

| Skill | Role |
|---|---|
| `boot` | Sync repo, validate state, acquire lock, halts check |
| `research` | Brave/Tavily/Serper queries + research-note generation |
| `markets` | Polymarket Gamma/CLOB discovery + candidate ranking |
| `sizing` | Kelly, fractional Kelly, 5% cap, correlation guard |
| `trade` | Paper synthetic fills OR mainnet via py-clob-client (only skill that reads `WALLET_SEED`) |
| `journal` | Canonical writer for `state/trade-log.jsonl` and research notes |
| `persist` | Atomic JSON writes, git pull/commit/push, lock release |
| `notify` | Telegram Bot API + per-mode suppression |
| `risk` | Circuit-breaker formula and halt management |
| `recap` | Daily + weekly benchmark report generation |
| `reflect` | Strategy edit with mandatory snapshot |

Plus `skills/polymarket/` as the existing git submodule.

## Consequences

- Routine files become trivial to read at a glance — they're a list of
  skill invocations with branch conditions.
- Adding a new capability = new `skills/<name>/SKILL.md`; no routine
  rewrite unless schedule wiring changes.
- Adding a new schedule = new `routines/<name>.md`; no skill rewrite.
- `AGENTS.md` explicitly explains the split so the agent knows when to
  load a skill vs follow a routine.
- Token efficiency: a routine that doesn't need `trade` never loads
  `skills/trade/SKILL.md` (which is the largest file because of mainnet
  preconditions). Boot context stays small.
- The wallet-secret constraint is now expressed as "only `skills/trade`
  reads `WALLET_SEED`" — a sharper boundary than "only the mainnet branch
  of `50-execute-trade.md`".
