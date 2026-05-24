# 10 — Load State

**Trigger:** after `00-wake-up.md` has acquired the lock and halts are not active.

**Reads:** `config/mode.json`, `config/guardrails.md`, `state/halts.json`,
`state/lock.json`, `state/portfolio.json`, `state/cycle-index.json`, tail of
`state/trade-log.jsonl`.

**Writes:** nothing. Pure read + validate.

## Steps

1. **Re-read everything from disk** even if you already opened it in `00-wake-up.md`.
   Files may have been touched by the observation-flag commit.

2. **Validate JSON schemas.** Every file below must parse with `jq empty <file>`
   AND contain `schema_version: 1`. If any check fails, append a
   `preflight_failed` event and abort to `60-log-and-persist.md`.
   - `config/mode.json`: required keys `schema_version`, `network`,
     `cadence_minutes`, `observation_only`, `observation_started_at`,
     `observation_hours`, `mainnet_attestation`.
   - `state/portfolio.json`: required keys `schema_version`, `cash_usdc`,
     `starting_capital`, `starting_ts`, `positions`, `open_orders`, `updated_at`.
   - `state/halts.json`: required keys `schema_version`, `active`, `reason`,
     `triggered_at`, `cycle_id`.
   - `state/lock.json`: required keys `schema_version`, `active`, `cycle_id`,
     `started_at`, `expires_at`.
   - `state/cycle-index.json`: required keys `schema_version`, `last_cycle_id`,
     `last_started_at`, `last_completed_at`, `last_pushed_commit`, `nav_snapshots`.

3. **Validate trade-log.** Pipe the last 200 lines through `jq -c .` to confirm
   each parses. Any malformed line aborts the cycle.

4. **Read `config/guardrails.md`** (markdown). Mentally bind 5% per-position and
   10%/24h circuit-breaker limits for later use in `40-decide-and-size.md` and
   `99-circuit-breaker.md`.

5. **Read `strategy/current.md`.** This is your active financial model — keep it
   in mind through research, market selection, and sizing.

6. **Compute NAV** using the formula in `config/guardrails.md`:
   `cash_usdc + sum(position.shares * fresh_mark_price)`. If any open position
   lacks a fresh mark price (≤15 min old), flag NAV as `stale`; new trades are
   forbidden until fresh marks are obtained in `40-decide-and-size.md`.

## Failure modes

- **Missing required key:** treat the file as invalid. Do not patch silently.
  Human must fix.
- **`schema_version` higher than 1:** abort. A future version requires an explicit
  routine update.
- **Empty portfolio with zero `starting_capital`:** abort. The portfolio was never
  seeded.
