---
name: commit
description: Conventional Commits / commitlint format for every routine commit. Loaded by skills/persist before composing the message.
inputs: routine name, cycle_id, summary
outputs: well-formed subject + body strings
---

# Commit

Canonical commit-message rules. Non-conforming messages corrupt the structured event log.

## Format

```
<type>(<scope>): <subject> [cycle <cycle_id>]

<optional body — wrap at 100 chars>
```

## Types

`feat` (new capability / forecast / trade / routine) · `fix` (bug, halt, null_cycle) · `chore` (no-op cycles, housekeeping) · `docs` · `refactor` · `perf` · `test` · `style` · `build` · `ci` · `revert`.

## Scopes

`cycle` (heartbeat, no-ops, null cycles) · `research` · `trade` · `recap` · `strategy` (reflect edits) · `halt` · `decision` (mainnet pre-submit) · `state` (schema/file) · `agent` (AGENTS.md + self-direction: envision/enact/auto-rollback) · `skill` · `routine` · `repo` (repo-wide hygiene / groom).

Adding a scope is itself an `agent` or `skill` change — document it here in the same commit.

## Subject

- Imperative, lowercase, ≤72 chars **including** `[cycle <cid>]`. No trailing period.
- `[cycle <cycle_id>]` is **required** for routine-emitted commits. Human-directed commits (refactors, docs) may omit it.

## Routine → subject (canonical)

| routine                          | subject                                                       |
| -------------------------------- | ------------------------------------------------------------- |
| overnight-watch (no trade)       | `chore(cycle): overnight_watch [cycle <cid>]`                 |
| overnight-watch (opportunistic)  | `feat(trade): overnight opportunistic <slug> [cycle <cid>]`   |
| research-window (normal)         | `feat(research): window <YYYY-MM-DD> [cycle <cid>]`           |
| research-window (explore-only)   | `feat(research): window explore_only <N>fcsts [cycle <cid>]`  |
| trade-window (paper fill)        | `feat(trade): paper_fill <slug> [cycle <cid>]`                |
| trade-window (mainnet)           | `feat(trade): mainnet_fill <slug> [cycle <cid>]`              |
| trade-window (explore-only)      | `feat(trade): explore_only <N>fcsts [cycle <cid>]`            |
| trade-window (mixed)             | `feat(trade): exploit<N>+explore<M> [cycle <cid>]`            |
| daily-close                      | `feat(recap): daily <YYYY-MM-DD> [cycle <cid>]`               |
| daily-close (Sunday)             | `feat(recap): daily + weekly <YYYY-Www> [cycle <cid>]`        |
| daily-close (strategy edit)      | `feat(strategy): reflect -> v<N+1> [cycle <cid>]`             |
| daily-close (proposal surfaced)  | `feat(agent): envision <slug> [cycle <cid>]`                  |
| daily-close (Sunday vision-only) | `docs(agent): vision weekly <YYYY-Www> [cycle <cid>]`         |
| heartbeat                        | `chore(cycle): heartbeat [cycle <cid>]`                       |
| heartbeat (liveness gap)         | `fix(cycle): heartbeat liveness_gap <N>h [cycle <cid>]`       |
| any — floor missed               | `fix(cycle): null_cycle <reason> [cycle <cid>]`               |
| any — breaker tripped            | `fix(halt): <reason> [cycle <cid>]`                           |
| mainnet pre-submit (rare)        | `feat(decision): pre-submit <idempotency_key> [cycle <cid>]`  |
| enact self-implementation (Sun)  | `feat(agent): enact <slug> [cycle <cid>]`                     |
| enact auto-rollback (Sun)        | `revert(agent): auto-rollback <slug> [cycle <cid>]`           |

`daily-close` is **one commit** but can carry recap + reflect + envision artifacts. Pick the single
headline by first match (most-consequential-wins); the rest go in the body:
1. reflect edited `strategy/current.md` → `feat(strategy): reflect -> v<N+1>`.
2. envision surfaced (daily) or self-approved (Sunday) a proposal → `feat(agent): envision <slug>`.
3. Sunday weekly recap written → `feat(recap): daily + weekly <YYYY-Www>`.
4. plain daily → `feat(recap): daily <YYYY-MM-DD>`.
`docs(agent): vision weekly` is reserved for the rare case where a Sunday `VISION.md` revision is the
*only* new durable artifact (e.g. a re-run where the recap was already deduped). `enact` does **not**
ride here — it pushes its own standalone revertible commit(s) (the `enact` rows above; see `skills/enact`).

## Body

1-3 short lines. WHY when non-obvious. Multi-paragraph allowed for reflect/halt. Never include secrets, wallet addresses, token-bearing URLs.

## Compose pattern

```bash
git commit -m "$(cat <<EOF
<type>(<scope>): <subject> [cycle <cid>]

Phase: <phase>
Details: <context>
EOF
)"
```

Heredoc preserves newlines reliably.

## Enforcement

Non-conforming commit → fix via `fix(agent): <correction>` follow-up or `--amend` before push. Never `--no-verify`. Never plain `--force` on automated pushes; `--force-with-lease` only for human-directed history consolidation.
