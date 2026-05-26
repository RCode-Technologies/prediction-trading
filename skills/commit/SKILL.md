---
name: commit
description: Conventional Commits / commitlint format for every routine commit. Loaded by skills/persist before composing the cycle's commit message.
inputs: routine name, cycle_id, summary of artifacts/decisions
outputs: well-formed Conventional Commit subject + body strings
---

# Commit

Canonical commit-message rules for this repo. Hard contract — non-conforming messages corrupt the structured event log that the agent reads as its brain.

## Format

```
<type>(<scope>): <subject> [cycle <cycle_id>]

<optional body — wrap at 100 chars>

<optional footer>
```

## Allowed `<type>`

| type       | when                                                       |
| ---------- | ---------------------------------------------------------- |
| `feat`     | new capability, new forecast/decision/trade, new routine/skill |
| `fix`      | bug fix, halt, null_cycle, error correction                |
| `chore`    | no-op cycles, housekeeping, dependency bumps               |
| `docs`     | documentation only                                         |
| `refactor` | structural change without behavior change                  |
| `perf`     | performance improvement                                    |
| `test`     | test scaffolding                                           |
| `style`    | formatting only (no logic)                                 |
| `build`    | build / tooling                                            |
| `ci`       | CI config (reserved)                                       |
| `revert`   | explicit revert commits                                    |

## Allowed `<scope>`

| scope      | meaning                                                |
| ---------- | ------------------------------------------------------ |
| `cycle`    | generic cycle commit (heartbeat, no-ops, null cycles)  |
| `research` | research-window outputs                                |
| `trade`    | trade-window outputs, paper/mainnet fills              |
| `recap`    | daily/weekly recap                                     |
| `strategy` | `strategy/current.md` reflect-driven edits             |
| `halt`     | circuit-breaker activations                            |
| `decision` | mainnet pre-submit safety commits                      |
| `state`    | schema/state-file changes                              |
| `agent`    | AGENTS.md and the contract                             |
| `skill`    | `skills/<name>/SKILL.md` changes                       |
| `routine`  | `routines/<name>.md` changes                           |

Extending this list is itself an `agent`-scope or `skill`-scope change — document the new scope here in the same commit.

## Subject rules

- Imperative mood, lowercase.
- ≤72 chars **including** `[cycle <cid>]`.
- The `[cycle <cycle_id>]` suffix is **required** on every routine-emitted commit. Human-directed commits (refactors, docs) may omit it.
- No trailing period.

## Routine-mapped subjects (canonical, copy these)

| routine           | typical subject                                                |
| ----------------- | -------------------------------------------------------------- |
| `overnight-watch` (no trade) | `chore(cycle): overnight_watch [cycle <cid>]`        |
| `overnight-watch` (opportunistic fill) | `feat(trade): overnight opportunistic <slug> [cycle <cid>]` |
| `research-window` (normal)   | `feat(research): window <YYYY-MM-DD> [cycle <cid>]`  |
| `research-window` (explore-only) | `feat(research): window explore_only <N>fcsts [cycle <cid>]` |
| `trade-window` (paper fill) | `feat(trade): paper_fill <slug> [cycle <cid>]`        |
| `trade-window` (mainnet)    | `feat(trade): mainnet_fill <slug> [cycle <cid>]`      |
| `trade-window` (explore only) | `feat(trade): explore_only <N>fcsts [cycle <cid>]`  |
| `trade-window` (mixed)      | `feat(trade): exploit<N>+explore<M> [cycle <cid>]`    |
| `daily-close`               | `feat(recap): daily <YYYY-MM-DD> [cycle <cid>]`       |
| `daily-close` (Sunday)      | `feat(recap): daily + weekly <YYYY-Www> [cycle <cid>]`|
| `daily-close` (strategy edit) | `feat(strategy): reflect -> v<N+1> [cycle <cid>]`   |
| `heartbeat` (normal)        | `chore(cycle): heartbeat [cycle <cid>]`               |
| `heartbeat` (liveness gap)  | `fix(cycle): heartbeat liveness_gap <N>h [cycle <cid>]` |
| **any** floor missed        | `fix(cycle): null_cycle <reason> [cycle <cid>]`       |
| **any** breaker tripped     | `fix(halt): <reason> [cycle <cid>]`                   |
| mainnet pre-submit (rare)   | `feat(decision): pre-submit <idempotency_key> [cycle <cid>]` |

## Body rules

- 1-3 short lines. Convey the WHY when non-obvious, not a restating of the diff.
- Multi-paragraph bodies allowed for reflect's strategy edits or halt explanations.
- Never include secrets, wallet addresses, token-bearing URLs, attestation strings.

## Composing via heredoc (recommended pattern)

```bash
git commit -m "$(cat <<EOF
<type>(<scope>): <subject> [cycle <cid>]

Phase: <phase>
Details: <one or two sentences of context>
EOF
)"
```

The heredoc preserves newlines reliably across shells.

## Enforcement

- A commit that doesn't match this contract is a contract violation. Fix in a `fix(agent): <correction>` follow-up, or `--amend` before push.
- Never use `--no-verify` to bypass a future commitlint hook; fix the message instead.
- Never use plain `--force` on automated routine pushes. Human-directed history consolidation may use `--force-with-lease` only after verifying clean worktree and unchanged remote lease.
