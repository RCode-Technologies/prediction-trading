# 80 — Reflect

**Trigger:** once per UTC date, after `60-log-and-persist.md`. Dispatched from
`00-wake-up.md` only when no prior `reflection` event exists for the current
UTC date.

**Reads:** last 24h of `state/trade-log.jsonl`, current `strategy/current.md`,
recent `research/YYYY-MM-DD/` notes.

**Writes:** `strategy/current.md`, `strategy/history/YYYY-MM-DD-vN.md`,
`state/trade-log.jsonl` (`reflection` event).

## Hard rules (per ADRs 0005, 0007)

- **May only edit `strategy/current.md`.** Never touch `config/guardrails.md`,
  never touch `AGENTS.md`, never touch routines.
- **Snapshot on every edit.** Before writing the new file, copy the current
  version to `strategy/history/YYYY-MM-DD-vN.md` where `N` increments per UTC
  date (start at `v1`; `v2`, `v3` if multiple reflections somehow occur on the
  same day — though the dispatch rule should prevent that).

## Steps

1. **Idempotency check.** Search the trade-log for an event matching
   `event_type == "reflection"` and `date == <today UTC>`. If found, exit
   without changes.

2. **Aggregate last 24h.**
   - Pull all events with `ts >= now - 24h`.
   - Compute: forecasts made, paper fills, mainnet fills, hit rate
     (forecasts where the realized resolution matched the agent's higher-
     probability outcome), realized P&L, current open-position MTM P&L, NAV
     trajectory.

3. **Compare forecasts to outcomes.** For each resolved market in the window,
   compute Brier score `(your_p - outcome)^2`. For unresolved markets, compare
   forecast price to current midpoint and flag drift.

4. **Decide whether to edit.** Reasons to edit:
   - Hit rate or Brier score worse than threshold defined in the current
     strategy file.
   - A repeated mispricing pattern that the strategy does not yet capture.
   - A correlation surprise (two trades that turned out related).
   - A new research method that consistently produced better forecasts.

   Reasons not to edit: too few data points, or no clear lesson. In that case
   still write a `reflection` event with `edited: false` so the daily run is
   marked done.

5. **If editing:**
   - Read the current `strategy/current.md` into memory.
   - Read or compute the next version: parse YAML frontmatter `version: vN`,
     increment to `v(N+1)`.
   - Snapshot: copy current file to
     `strategy/history/<YYYY-MM-DD>-v<old_N>.md`. If that filename already
     exists today, increment the suffix (`-v<old_N>a`, etc.) — but typically
     we expect at most one reflection per day so this is a safety net.
   - Write the new `strategy/current.md` with `version: v(N+1)` and a brief
     `# Changelog` section at the bottom listing the date and rationale for
     this edit. Keep changes incremental; do not rewrite from scratch unless
     genuinely warranted.
   - Body content owned by the agent: probability calibration methods, sizing
     framework (fractional Kelly factor, etc.), market selection criteria,
     correlation rules, edge-identification heuristics, minimum-edge floor.

6. **Append a `reflection` event:**
   ```json
   {"schema_version":1,"event_id":"<cycle_id>-reflection-1","cycle_id":"<cycle_id>","event_type":"reflection","ts":"<now>","mode":"<network>","date":"<YYYY-MM-DD>","edited":true,"prior_version":"v<old_N>","new_version":"v<N+1>","snapshot":"strategy/history/<YYYY-MM-DD>-v<old_N>.md","rationale":"<short>"}
   ```

7. **Commit message** for the strategy edit should reference the snapshot
   path: `cycle <cycle_id>: reflect → strategy v<N+1> (snapshot
   strategy/history/<YYYY-MM-DD>-v<old_N>.md)`.

8. **Surface guardrail recommendations.** If your analysis suggests
   `config/guardrails.md` should change, do **not** edit it. Instead, include
   a "Guardrail recommendation for human review" line in the next daily
   summary Telegram message (composed in `70-notify-telegram.md`).

## Failure modes

- **No trade-log activity in 24h:** acceptable; write `reflection` with
  `edited: false`.
- **YAML version parse fails:** treat as `v0`; write `v1` snapshot to history.
- **Snapshot write fails:** do not overwrite `current.md`. Log failure and exit.
