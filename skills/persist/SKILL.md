---
name: persist
description: End-of-cycle bookkeeping. Atomic writes, validation, lock release, git commit + pull/rebase + push. **A cycle that does not push is unsuccessful.**
inputs: pending changes in working tree, cycle_id
outputs: HEAD SHA pushed, lock released, cycle_end event
---

# Persist

Push is the **only** success criterion. The agent pushes directly to `main` — no PRs, no feature branches. Verify `HEAD == origin/main` and write SHA to `cycle-index.json.last_pushed_commit`.

## Git identity (idempotent — every cycle)

```bash
git config --global user.email "${GIT_AUTHOR_EMAIL:-agent@prediction-trading.local}"
git config --global user.name  "${GIT_AUTHOR_NAME:-Polymarket Trading Agent}"
```

## Push preflight (before first commit)

```bash
git push --dry-run origin main 2>&1 | head -5
```

Auth failure (`Permission denied`, `could not read Username`, `403`, `Repository moved`) → `circuit-breaker.halt("push_permission_missing")`. Fail fast.

## Atomic write rule

JSON: `jq '<expr>' f.json > f.json.tmp && mv f.json.tmp f.json`. JSONL: `>>` only; never edit prior lines.

## End-of-cycle

1. **Validate all state:**
   ```bash
   jq empty config/mode.json state/portfolio.json state/halts.json state/lock.json state/cycle-index.json
   jq -c . state/trade-log.jsonl > /dev/null
   ```
   Fail → `persist_conflict` + notify + exit (no commit).

2. **`nav_snapshot`** via `journal`:
   ```json
   {"event_type":"nav_snapshot","nav_usdc":<n>,"cash_usdc":<n>,"positions_value_usdc":<n>}
   ```
   Append `{ts, nav_usdc}` to `cycle-index.json.nav_snapshots` (cap 1000).

3. **`cycle-index.json`:** set `last_cycle_id`, `last_started_at`, `last_completed_at`. Leave `last_pushed_commit` for step 7.

4. **Release lock** (atomic): `{schema_version:1, active:false, cycle_id:null, started_at:null, expires_at:null}`.

5. **`cycle_end`** via `journal`.

6. **Commit** (Conventional Commits):
   ```bash
   git add -A
   git commit -m "<type>(<scope>): <subject> [cycle <cid>]"
   ```

7. **Pull/rebase/push:**
   ```bash
   git pull --rebase origin main
   git push origin main
   ```
   Never `--force`, never `--no-verify`. On rejection: retry pull/rebase **once**. Still failing → `persist_conflict` + notify + non-zero exit. Stale lock recovers next cycle.

8. **Verify push:**
   ```bash
   git fetch origin main
   LOCAL=$(git rev-parse HEAD)
   REMOTE=$(git rev-parse origin/main)
   [ "$LOCAL" = "$REMOTE" ] || exit 1
   ```
   Mismatch → `persist_conflict` + notify + non-zero exit.

9. **Write SHA** to `cycle-index.json.last_pushed_commit`. Follow-up commit OK: `chore(cycle): record last_pushed_commit [cycle <cid>]`.

## Mainnet pre-submit push (from `trade`)

```bash
git add state/trade-log.jsonl
git commit -m "feat(decision): pre-submit <idempotency_key> [cycle <cid>]"
git pull --rebase origin main && git push origin main
```

Push fail → `trade` aborts before SDK call (order not submitted).

## Failure modes

- Push unresolvable → unsuccessful cycle. Idempotency keys on pre-submit decisions protect mainnet duplicates.
- State corrupted after a routine write → `git checkout -- <file>` if possible, log, notify, exit.
- Force-push attempted → forbidden, abort.
