# 00 — Wake Up

**Trigger:** every scheduled run. Mandatory first routine. No other routine may
run before this one.

**Reads:** `config/mode.json`, `state/halts.json`, `state/lock.json`,
`state/portfolio.json`, `state/cycle-index.json`, tail of `state/trade-log.jsonl`.

**Writes:** `state/lock.json`, `state/cycle-index.json`, `config/mode.json`
(only to flip `observation_only` after 48h), `state/trade-log.jsonl`
(`cycle_start`, possibly `stale_lock_recovered`).

## Steps

1. **Sync memory branch.**
   - `git fetch origin`
   - `git checkout <memory-branch>` (default branch).
   - `git pull --rebase`.
   - If any step fails, log nothing (no commit possible) and exit non-zero.

2. **Generate `cycle_id`.**
   - Format: `YYYYMMDDTHHMMSSZ-<8 lowercase hex>`, UTC.
   - Example: `20260524T140000Z-3f9c8a21`.

3. **Run the boot sequence.** Read in this order:
   `config/mode.json` → `state/halts.json` → `state/lock.json` →
   `state/portfolio.json` → `state/cycle-index.json` → last ~50 lines of
   `state/trade-log.jsonl`. Validate each JSON file with `jq empty <file>`. If any
   is invalid, jump to step 8 and exit without trading.

4. **Lock check.**
   - If `lock.json.active == true` and `now < expires_at`: another cycle is in
     flight. Exit cleanly — no commit, no log line (the cycle that owns the lock
     will write its own events).
   - If `lock.json.active == true` and `now >= expires_at`: stale lock.
     Append a `stale_lock_recovered` event with this cycle's `cycle_id` and the
     prior `cycle_id`. Continue.
   - Acquire: set `lock.json = { schema_version: 1, active: true, cycle_id,
     started_at: <now>, expires_at: <now + 55m> }`. Write atomically (temp file +
     `mv`).

5. **Halts check.**
   - If `halts.json.active == true`: skip all routines except possibly
     `99-circuit-breaker.md` for status assessment. Jump to step 8.

6. **Observation transition.**
   - If `mode.json.observation_only == true` and
     `now >= observation_started_at + observation_hours * 3600`:
     set `observation_only = false` and commit only this change with message
     `cycle <cycle_id>: observation window ended`. Continue.

7. **Append `cycle_start` event** to `state/trade-log.jsonl`:
   ```json
   {"schema_version":1,"event_id":"<cycle_id>-cycle_start-1","cycle_id":"<cycle_id>","event_type":"cycle_start","ts":"<now>","mode":"<network>"}
   ```

8. **Dispatch.**
   - If halts active → `routines/70-notify-telegram.md` for daily summary if not
     sent today, then `routines/60-log-and-persist.md`, release lock, exit.
   - Otherwise → `routines/10-load-state.md` → `20-research.md` →
     `30-analyze-markets.md` → `40-decide-and-size.md` → `50-execute-trade.md` →
     `60-log-and-persist.md` → `70-notify-telegram.md` → (daily, once per UTC
     date) `80-reflect.md` → `99-circuit-breaker.md` evaluation → release lock,
     `cycle_end`, commit, push.

## Failure modes

- **`git pull --rebase` fails:** state may have diverged. Do not trade. Exit and
  let the next scheduled run try again.
- **JSON corruption:** any invalid file → no trading this cycle. If `trade-log.jsonl`
  is appendable, write a diagnostic `preflight_failed` event. Release lock anyway.
- **Lock write fails:** treat as system failure; do not trade.

## Notes

- Lock TTL is 55 minutes, slightly under the hourly cadence so a hung cycle does
  not block the next scheduled run forever.
- Lock release is part of `60-log-and-persist.md`; if the cycle aborts mid-way,
  always set `lock.active = false` before exiting.
