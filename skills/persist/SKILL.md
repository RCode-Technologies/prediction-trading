---
name: persist
description: Atomic JSON writes, JSON/JSONL validation, lock release, git commit + pull/rebase + push. Single canonical writer for state transitions and the only path to the memory branch.
inputs: pending changes in working tree, cycle_id
outputs: HEAD SHA pushed to memory branch, lock released, cycle_end event
---

# Persist

End-of-cycle bookkeeping. Validates state, releases the lock, commits and
pushes the memory branch. Also invoked mid-cycle by the `trade` skill for
the mainnet pre-submit push.

## Atomic write rule

Every JSON write goes through temp + `mv`:

```bash
jq '<expr>' state/portfolio.json > state/portfolio.json.tmp \
  && mv state/portfolio.json.tmp state/portfolio.json
```

JSONL appends only via `>>`. Never edit prior JSONL lines.

## End-of-cycle flow

1. **Validate all state files:**
   ```bash
   jq empty config/mode.json state/portfolio.json state/halts.json \
            state/lock.json state/cycle-index.json
   jq -c . state/trade-log.jsonl > /dev/null
   ```
   Any failure → emit `persist_conflict`, call `notify` if possible, exit
   without commit.

2. **Append `nav_snapshot`** via `journal`:
   ```json
   {"event_type":"nav_snapshot","nav_usdc":<n>,"cash_usdc":<n>,"positions_value_usdc":<n>}
   ```
   Also append `{ts, nav_usdc}` to `state/cycle-index.json.nav_snapshots`
   (cap array at 1000 most recent).

3. **Update `state/cycle-index.json`:**
   - `last_cycle_id = <this>`, `last_started_at = <cycle_start ts>`,
     `last_completed_at = <now>`.
   - `last_pushed_commit` left alone until step 7.

4. **Release the lock.** Atomic write:
   ```json
   {"schema_version":1,"active":false,"cycle_id":null,"started_at":null,"expires_at":null}
   ```

5. **Append `cycle_end`** via `journal`.

6. **Commit:**
   ```bash
   git add -A
   git commit -m "<conventional commit message including cycle_id and phase>"
   ```
   Use Conventional Commits, e.g.:
   - `feat(trade): paper_fill <market_slug> [cycle <cycle_id>]`
   - `chore(cycle): pre_market complete [cycle <cycle_id>]`
   - `fix(halt): circuit breaker tripped [cycle <cycle_id>]`

7. **Pull / rebase / push:**
   ```bash
   git pull --rebase
   git push
   ```
   Never `--force`. Never `--no-verify`.

   On rejection: retry pull/rebase **once**. Still conflicting?
   - Append a local `persist_conflict` event.
   - Call `notify` if possible.
   - Exit non-zero. The lock release did not push — next cycle sees stale
     lock and recovers.

8. **Write HEAD SHA.** After successful push, read local HEAD SHA, set
   `cycle-index.json.last_pushed_commit`. A small follow-up commit + push for
   this one-line update is acceptable.

## Mainnet pre-submit push (called from `trade` skill)

```bash
git add state/trade-log.jsonl
git commit -m "feat(decision): pre-submit <idempotency_key> [cycle <cycle_id>]"
git pull --rebase
git push
```

Push failure here → `trade` skill must abort before any SDK call (the order
has not been submitted).

## Failure modes

- **Push unresolvable:** cycle is unsuccessful. Idempotency keys on any
  already-pushed pre-submit decisions protect mainnet duplicates.
- **State corrupted after a routine write:** `git checkout -- <file>` to
  roll back if possible, log incident, notify, exit.
- **Force-push attempted:** forbidden. Abort.
