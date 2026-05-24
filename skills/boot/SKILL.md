---
name: boot
description: Wake-up sequence for every routine — sync main, validate state, acquire lock, check halts. Failure here = no other skill runs.
inputs: caller routine name, phase tag
outputs: cycle_id, lock acquired, validated state, halt status
---

# Boot

## Steps

1. **Sync.** `git fetch origin && git checkout main && git pull --rebase origin main`. The agent operates on `main` only — no feature branches, no PRs. Failure → exit non-zero (no log line possible).

2. **`cycle_id`** = `YYYYMMDDTHHMMSSZ-<8 lower-hex>` UTC. E.g. `20260524T133000Z-3f9c8a21`.

3. **Validate boot files** (`jq empty` on every JSON):
   - `config/mode.json` — required keys: `schema_version`, `network`, `cadence_minutes`, `observation_only`, `observation_started_at`, `observation_hours`, `mainnet_attestation`.
   - `state/halts.json`, `state/lock.json`, `state/portfolio.json`, `state/cycle-index.json`.
   - `state/trade-log.jsonl` tail (~50 lines; each parses).
   - `strategy/current.md`.
   
   Any failure → append `preflight_failed` if log is appendable, jump to `persist`, exit.

4. **Lock.** Read `state/lock.json`.
   - `active && now < expires_at` → another cycle in flight, exit clean, no commit. TTL 55 min.
   - `active && now >= expires_at` → stale. Append `stale_lock_recovered` (this `cycle_id` + prior).
   - Acquire: atomic write `{schema_version:1, active:true, cycle_id, started_at:<now>, expires_at:<now+55m>}`.

5. **Halts.** `halts.json.active==true` → return halt flag to caller; no phase work.

6. **Observation transition.** If `mode.observation_only==true` and `now >= observation_started_at + observation_hours * 3600` → set `observation_only=false`. Do **not** commit here; `persist` includes this state change in the routine's single end-of-cycle commit.

7. **Append `cycle_start`:**
   ```json
   {"schema_version":1,"event_id":"<cid>-cycle_start-1","cycle_id":"<cid>","event_type":"cycle_start","ts":"<now>","mode":"<network>","phase":"<caller>"}
   ```

8. **Return** `{cycle_id, halts_active, mode, observation_only}` to caller.

## Failure modes

- Pull/rebase fail → state diverged; no trading; next cycle retries.
- JSON corruption → preflight fail; `persist` still attempts lock release.
- Lock write fail → system failure; do not trade.
