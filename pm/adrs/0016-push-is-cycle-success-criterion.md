# 0016 — A cycle is successful only if `git push` lands

- **Status:** Accepted
- **Date:** 2026-05-24
- **Related:** ADR 0009/0010 (memory branch contract), ADR 0011 (skills split)

## Context

In Claude Code cloud routines, "the run finished" and "the run persisted"
are different things. A green routine status only proves the cloud session
completed — it does not prove that any local commits made it to the
memory branch. ADR 0009 already required pull/rebase + push at end of
cycle, but did not explicitly state push success as the success criterion,
did not require post-push verification, and did not address the failure
modes that block pushes (no git identity, missing credentials, branch
protection).

## Decision

A cycle is **successful if and only if** `skills/persist` has pushed all
changes to the memory branch and the local HEAD matches the remote HEAD.

To make this concrete, `skills/persist` is required to:

1. **Set git identity idempotently** at the start of every persist call
   so a missing `GIT_AUTHOR_*` env never blocks commits:
   ```bash
   git config --global user.email "${GIT_AUTHOR_EMAIL:-agent@prediction-trading.local}"
   git config --global user.name  "${GIT_AUTHOR_NAME:-Polymarket Trading Agent}"
   ```

2. **Run `git push --dry-run` before the first commit.** If output
   indicates auth failure or repo moved, call
   `skills/circuit-breaker.halt("push_permission_missing")` and exit
   before doing work that will be lost.

3. **Verify after push:**
   ```bash
   git fetch origin
   LOCAL=$(git rev-parse HEAD)
   REMOTE=$(git rev-parse "origin/$(git rev-parse --abbrev-ref HEAD)")
   [ "$LOCAL" = "$REMOTE" ] || exit 1
   ```

4. **Write `cycle-index.json.last_pushed_commit = $LOCAL`** and commit +
   push that one-line update (`chore(cycle): record last_pushed_commit`).

The Claude cloud routine prompt is updated to make the criterion explicit
to the agent:

> The cycle is only successful when `skills/persist` has committed and
> pushed all changes to the memory branch. Do not exit until push has
> landed (verified by `cycle-index.json.last_pushed_commit`).

## Consequences

- Push failure modes (auth, branch protection, network) are detected
  early via `--dry-run` rather than after the agent has done expensive
  research.
- Silent push failures (e.g. branch protection that returns success but
  rejects the ref) are caught by the local-vs-remote SHA verification.
- The `last_pushed_commit` field on `state/cycle-index.json` is the
  canonical record of which commit each cycle landed; humans can correlate
  it with `cycle_id` in the trade log.
- `GIT_AUTHOR_NAME` and `GIT_AUTHOR_EMAIL` become optional but documented
  env vars; defaults keep things working in under-configured environments.
- Pushes still go through Claude Code's GitHub integration (when running
  in a cloud routine) or the operator's local credentials (manual dry
  runs); this ADR does not change the auth model, only the verification.
