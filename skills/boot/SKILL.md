---
name: boot
description: Mandatory wake-up sequence for any routine — sync memory branch, validate state JSON, acquire repo-backed lock, check halts, dispatch back to caller. Every routine invokes this skill first.
inputs: caller routine name, intended phase tag
outputs: cycle_id, lock acquired, validated state in memory, halt status
---

# Boot

The first thing every routine does. Stateless run start: pull memory branch,
validate everything, acquire the lock, prepare a `cycle_id`. If anything here
fails, **no other skill runs**.

## Steps

1. **Sync the memory branch.**
   - `git fetch origin`
   - `git checkout <default-branch>`
   - `git pull --rebase`
   - If any step fails: emit no log line (commit impossible), exit non-zero.

2. **Generate `cycle_id`:** `YYYYMMDDTHHMMSSZ-<8 lower-hex>` in UTC. Example
   `20260524T133000Z-3f9c8a21`.

3. **Read & validate the 7 boot files** in this order, with `jq empty <file>`
   on every JSON:
   - `config/mode.json` (required keys: `schema_version`, `network`,
     `cadence_minutes`, `observation_only`, `observation_started_at`,
     `observation_hours`, `mainnet_attestation`)
   - `state/halts.json`
   - `state/lock.json`
   - `state/portfolio.json`
   - `state/cycle-index.json`
   - tail of `state/trade-log.jsonl` (last ~50 lines; every line parses)
   - `strategy/current.md`

   If any file is missing or invalid: append a `preflight_failed` event if the
   trade-log itself is appendable, then jump to the persist skill to commit
   whatever can be committed, and exit.

4. **Lock protocol.** Read `state/lock.json`.
   - `active && now < expires_at`: another cycle is in flight. Exit cleanly,
     no commit. Lock TTL is 55 minutes (under the hourly schedule floor).
   - `active && now >= expires_at`: stale. Append a `stale_lock_recovered`
     event with this `cycle_id` and the prior `cycle_id`. Continue.
   - Acquire: write `{schema_version:1, active:true, cycle_id, started_at:<now>,
     expires_at:<now + 55m>}` atomically (temp file + `mv`).

5. **Halts check.** If `state/halts.json.active == true`: only the
   `circuit-breaker` routine + `notify` skill (for status) may run. Return the
   halt flag to the caller; do not proceed to phase work.

6. **Observation transition.** If `mode.observation_only == true` and
   `now >= observation_started_at + observation_hours * 3600`:
   set `observation_only = false`. Commit just that file with
   `chore(mode): observation window ended` and continue.

7. **Append `cycle_start`:**
   ```json
   {"schema_version":1,"event_id":"<cycle_id>-cycle_start-1","cycle_id":"<cycle_id>","event_type":"cycle_start","ts":"<now>","mode":"<network>","phase":"<caller>"}
   ```

8. **Return** `{cycle_id, halts_active, mode, observation_only}` to the calling
   routine. Caller decides which phase skills to invoke next.

## Failure modes

- **Pull/rebase fails:** state may have diverged. No trading. Exit; next
  scheduled invocation retries.
- **JSON corruption:** preflight fail. Skip phase work. Persist skill still
  attempts to release the lock and push a diagnostic event.
- **Lock write fails:** system failure. Do not trade.

## Cross-references

- `skills/persist/SKILL.md` for lock release at cycle end.
- `skills/risk/SKILL.md` for circuit-breaker evaluation.
- ADR 0009/0010 for memory-branch contract.
