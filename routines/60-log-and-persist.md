# 60 — Log and Persist

**Trigger:** end of every cycle. Reached from any prior routine (including
early aborts).

**Reads:** all of `state/`, `config/`, recent writes from `research/` and
`strategy/`.

**Writes:** `state/cycle-index.json`, `state/lock.json` (release),
`state/trade-log.jsonl` (`nav_snapshot`, `cycle_end`), git commit + push on
the memory branch.

## Steps

1. **Validate everything.**
   - `jq empty config/mode.json state/portfolio.json state/halts.json
     state/lock.json state/cycle-index.json` must succeed.
   - Every line of `state/trade-log.jsonl` must parse: `jq -c . state/trade-log.jsonl
     > /dev/null`. If any check fails, the cycle is not persistable as-is —
     write a `persist_conflict` event in memory only (do not write more JSONL
     lines), Telegram-notify if possible, and stop without commit.

2. **Append a `nav_snapshot`** event:
   ```json
   {"schema_version":1,"event_id":"<cycle_id>-nav_snapshot-1","cycle_id":"<cycle_id>","event_type":"nav_snapshot","ts":"<now>","mode":"<network>","nav_usdc":<nav>,"cash_usdc":<cash>,"positions_value_usdc":<v>}
   ```
   Also append `{ts, nav_usdc}` to `state/cycle-index.json.nav_snapshots`
   (cap the array at the most recent 1000 entries).

3. **Update `state/cycle-index.json`:**
   - `last_cycle_id = <this cycle_id>`
   - `last_started_at = <cycle_start ts>`
   - `last_completed_at = <now>`
   - `last_pushed_commit` left as the prior value until step 7 succeeds.

4. **Release the lock.** Set `state/lock.json`:
   ```json
   {"schema_version":1,"active":false,"cycle_id":null,"started_at":null,"expires_at":null}
   ```

5. **Append `cycle_end`** event:
   ```json
   {"schema_version":1,"event_id":"<cycle_id>-cycle_end-1","cycle_id":"<cycle_id>","event_type":"cycle_end","ts":"<now>","mode":"<network>"}
   ```

6. **Atomic file writes.** Every JSON write goes via temp file + `mv`:
   `jq '...' state/portfolio.json > state/portfolio.json.tmp && mv
   state/portfolio.json.tmp state/portfolio.json`. JSONL appends use `>>` only.

7. **Commit and push.**
   - `git add -A`
   - `git commit -m "cycle <cycle_id>"` (or include short context, e.g.
     `cycle <cycle_id>: observation forecast`, `cycle <cycle_id>: paper fill <market>`).
   - `git pull --rebase` (the start-of-cycle pull may be stale by an hour).
   - `git push`. Never `--force`, never `--no-verify`.
   - On rejection: retry pull/rebase once. If still conflicting, append a
     `persist_conflict` event to the local file, attempt one more commit + push;
     if that fails, Telegram-notify and stop with non-zero exit.

8. **Confirm push success.** Read the local HEAD SHA after push and write it
   into `cycle-index.json.last_pushed_commit`. Commit and push that
   single-line update too (a small follow-up commit is acceptable).

## Failure modes

- **Push rejection unresolvable:** the cycle is not successful. Idempotency keys
  on any pre-submit decision events that did push protect against duplicate
  mainnet orders next cycle. Lock release also did not push — next cycle will
  see a stale lock and recover.
- **JSON validation fails after writes:** do not push corrupted state. Roll
  back the offending file via `git checkout -- <file>` if possible, log the
  incident in a final event line, and notify.
- **Force-push attempted:** forbidden — abort.
