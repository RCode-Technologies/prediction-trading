---
name: persist
description: End-of-cycle bookkeeping. Atomic writes, validation, null-cycle audit, lock release, one routine commit + pull/rebase + push.
inputs: pending changes in working tree, cycle_id
outputs: HEAD == origin/main, lock released, cycle_end + (maybe) null_cycle event
---

# Persist

Push is the only success criterion. Direct push to `main`, no PRs. One Conventional Commit per cycle (mainnet pre-submit is the only exception). No follow-up bookkeeping commits.

## Git identity (idempotent)

```bash
git config --global user.email "${GIT_AUTHOR_EMAIL:-agent@prediction-trading.local}"
git config --global user.name  "${GIT_AUTHOR_NAME:-Polymarket Trading Agent}"
```

## Push preflight (before first commit)

```bash
git push --dry-run origin main 2>&1 | head -5
```

Auth failure → `circuit-breaker.halt("push_permission_missing")`. Fail fast.

## Atomic write rule

JSON: `jq '<expr>' f.json > f.json.tmp && mv f.json.tmp f.json`. JSONL: `>>` only; never edit prior lines.

## Steps

1. **Validate state:**
   ```bash
   jq empty config/mode.json state/portfolio.json state/halts.json state/lock.json state/cycle-index.json
   jq -c . state/trade-log.jsonl > /dev/null
   ```
   Fail → `persist_conflict` + notify + exit (no commit).

2. **Null-cycle audit.** Count event types this cycle (`cycle_id == <cid>`) vs floor in `strategy/current.md` § Decision rules (also mirrored in AGENTS.md). Floor missed → append `null_cycle` + notify (suppression-exempt). Still commits + pushes — silent failure is the enemy. Suppress `null_cycle` if a halt is the reason for the miss.
   ```json
   {"event_type":"null_cycle","reason":"floor_missed","required":{...},"actual":{...},"phase":"<phase>"}
   ```

3. **`nav_snapshot`** via `journal`. Append `{ts, nav_usdc}` to `cycle-index.json.nav_snapshots` (cap 1000).

4. **`cycle-index.json`:** set `last_cycle_id`, `last_started_at`, `last_completed_at`. `last_pushed_commit` deprecated (would require a 2nd commit).

5. **Release lock** atomically: `{active:false, cycle_id:null, started_at:null, expires_at:null}`.

6. **`cycle_end`** via `journal`.

7. **Commit once.** Load `skills/commit/SKILL.md` for format. Compose + run:
   ```bash
   git add -A
   git commit -m "<formatted per skills/commit>"
   ```
   A non-conforming message is a contract violation. Never `--no-verify`.

8. **Pull/rebase/push:**
   ```bash
   git pull --rebase origin main
   git push   # no explicit ref — global hooks flag the literal "git push origin main" pattern
   ```
   Never `--force`. On rejection: retry pull/rebase once. Still failing → `persist_conflict` + notify + non-zero exit. Stale lock recovers next cycle.

9. **Verify push:**
   ```bash
   git fetch origin main
   [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] || exit 1
   ```
   Mismatch → `persist_conflict` + notify + non-zero exit.

## Mainnet pre-submit push (from `trade`)

Only exception to one-commit-per-routine. Mainnet order intent must be durable before SDK submission:

```bash
git add state/trade-log.jsonl
git commit -m "feat(decision): pre-submit <idempotency_key> [cycle <cid>]"
git pull --rebase origin main && git push
```

Push fail → `trade` aborts before SDK call.

## Failure modes

- Push unresolvable → unsuccessful cycle. Idempotency keys on pre-submit decisions protect mainnet duplicates.
- State corrupted after a routine write → `git checkout -- <file>` if possible, log, notify, exit.
- Force-push by automated routine → forbidden, abort. `--force-with-lease` only via human direction.
