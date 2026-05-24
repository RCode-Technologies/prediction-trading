# 0013 — Conventional Commits for all agent commits

- **Status:** Accepted
- **Date:** 2026-05-24
- **Related:** PRD v1-instruction-pack, ADR 0009, ADR 0010

## Context

ADR 0009 specified a fixed commit message format `cycle <cycle_id>` for
every end-of-cycle commit. With v1.1's wider variety of cycle outcomes
(research-only cycles, mainnet fills, recaps, reflections, halts), a
single template was both noisy and ambiguous — every commit looked the
same in `git log`, making history hard to scan.

The user also requested commit messages conform to the commitlint /
Conventional Commits standard so downstream tooling (changelog generators,
release notes) can parse them.

## Decision

All agent-authored commits follow Conventional Commits format:

```
<type>(<scope>): <short subject> [cycle <cycle_id>]
```

Common types and scopes used by this agent:

| Commit | Source |
|---|---|
| `feat(research): window <YYYY-MM-DD>` | `routines/research-window` cycle |
| `feat(trade): paper_fill <market_slug>` | paper branch of `skills/trade` |
| `feat(trade): mainnet_fill <market_slug>` | mainnet branch of `skills/trade` |
| `feat(decision): pre-submit <idempotency_key>` | mainnet pre-submit push from `skills/trade` |
| `feat(strategy): reflect → v<N+1> (snapshot v<old_N>)` | `skills/reflect` edit |
| `feat(recap): daily <YYYY-MM-DD>` | `routines/daily-close` |
| `feat(recap): daily + weekly <YYYY-Www>` | Sunday `daily-close` |
| `fix(halt): <reason>` | `skills/risk` halt commit |
| `chore(cycle): <routine> <no-op|complete>` | low-information cycles |
| `chore(mode): observation window ended` | `skills/boot` auto-flip |
| `chore(halt): cleared by <handle>` | human halt clear (documented for humans, not agent-authored) |

Every agent commit ends with ` [cycle <cycle_id>]` so machine-readable
correlation back to a `cycle_start` event is one regex away. Human commits
omit the suffix.

Hard rules carried over from ADR 0009:

- Never `--force` push, never `--no-verify`.
- Always `git pull --rebase` between commit and push.

## Consequences

- `git log --oneline` is now a useful timeline rather than 100 identical
  cycle lines.
- Changelog tooling can group commits by `feat`/`fix`/`chore` automatically.
- New commit categories require an ADR amendment (or a low-risk addition
  to this table) to stay consistent.
- The `cycle_id` suffix is mandatory for agent commits; a missing one
  signals a non-agent (human) commit.
