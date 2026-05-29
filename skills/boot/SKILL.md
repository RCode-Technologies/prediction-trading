---
name: boot
description: Wake-up sequence for every routine — sync main, validate state, acquire lock, check halts, liveness-gap check, emit cycle_start.
inputs: caller routine name, phase tag
outputs: cycle_id, lock acquired, validated state, halt status, liveness gap (if any)
---

# Boot

## Steps

1. **Sync.** `git fetch origin && git checkout main && git pull --rebase origin main`. Agent operates on `main` only. Failure → exit non-zero (no log line possible).

2. **`cycle_id` = `YYYYMMDDTHHMMSSZ-<8-lower-hex>`** UTC (e.g. `20260524T133000Z-3f9c8a21`).

3. **Validate boot files** (`jq empty`):
   - `config/mode.json` — keys: `schema_version`, `network`, `cadence_minutes`, `observation_only`, `observation_started_at`, `observation_hours`, `mainnet_attestation`.
   - `state/{halts,lock,portfolio,cycle-index}.json`.
   - `state/trade-log.jsonl` tail (~50 lines parse).
   - `strategy/current.md`.
   
   Failure → append `preflight_failed` if log appendable, jump to `persist`, exit.

4. **Lock** (`state/lock.json`):
   - `active && now < expires_at` → another cycle in flight, exit clean, no commit. TTL 55 min.
   - `active && now >= expires_at` → stale. Append `stale_lock_recovered` (this + prior cycle_id).
   - Acquire: atomic write `{schema_version:1, active:true, cycle_id, started_at:<now>, expires_at:<now+55m>}`.

5. **Halts.** `halts.json.active==true` → return halt flag; no phase work.

5b. **Protected-core integrity audit.** For each path in `config/autonomy.md` § Protected core:
   `git log -1 --format=%ae -- <path>`. Empty (no history yet) → skip. Author email ==
   `${GIT_AUTHOR_EMAIL:-agent@prediction-trading.local}` → the agent modified its own rails →
   `circuit-breaker.halt("protected_core_violation", path)`, return halt flag, no phase work. Cheap —
   one `git log` per manifest entry, and the manifest is short. This is the backstop behind `enact`'s
   intent gate and `persist`'s write gate (defense in depth).

6. **Observation transition.** `observation_only==true` and `now >= observation_started_at + observation_hours*3600` → set `observation_only=false`. Don't commit here — `persist` bundles it into the routine's single commit.

7. **Liveness-gap check.** `gap_seconds = now - cycle-index.last_completed_at`. > 32400 (9h, 1.5× the worst expected 6h between cycles) → append:
   ```json
   {"event_type":"liveness_gap","last_completed_at":"<iso>","gap_seconds":<n>,"threshold_seconds":32400,"missed_routines_inferred":[<list>]}
   ```
   `missed_routines_inferred` from cron frontmatter ∩ gap window. Informational only — not a halt.

8. **`cycle_start`** via `journal`:
   ```json
   {"schema_version":1,"event_id":"<cid>-cycle_start-1","cycle_id":"<cid>","event_type":"cycle_start","ts":"<now>","mode":"<network>","phase":"<caller>"}
   ```

8b. **Liveness alert.** If step 7 emitted `liveness_gap`, call `notify` kind `liveness_gap` (suppression-exempt). Continue regardless.

9. **Return** `{cycle_id, halts_active, mode, observation_only, liveness_gap_seconds}`.

## Failure modes

- Pull/rebase fail → state diverged; no trading; next cycle retries.
- JSON corruption → preflight fail; `persist` still attempts lock release.
- Lock write fail → do not trade.
