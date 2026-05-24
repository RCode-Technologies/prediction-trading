---
name: reflect
description: Daily self-review. Compares recent forecasts to outcomes, decides whether to edit strategy/current.md, snapshots the prior version. May only edit strategy/current.md (ADR 0005).
inputs: last 24h of trade-log, current strategy/current.md, recent recaps/
outputs: strategy/current.md (if edited), strategy/history/YYYY-MM-DD-vN.md snapshot, reflection event
---

# Reflect

Strategy self-improvement loop. Runs once per UTC date from the end-of-day
routine. Snapshot-then-edit (ADR 0007).

## Hard rules

- **May only edit `strategy/current.md`.** Never `config/guardrails.md`,
  never `AGENTS.md`, never routines, never skills (ADR 0005).
- **Snapshot on every edit.** Always copy the prior version to
  `strategy/history/YYYY-MM-DD-vN.md` before overwriting.

## Steps

1. **Idempotency check.** Grep `state/trade-log.jsonl` for
   `event_type=="reflection"` with `date:<today UTC>`. If found, exit.

2. **Pull last 24h of events.** For each `forecast` with a resolved market
   in the window, compute Brier score `(your_p - outcome)^2`. For unresolved
   markets, compare forecast price to current midpoint and flag drift.

3. **Aggregate hit-rate, Brier, realized P&L, MTM P&L, NAV trajectory.**
   The `recap` skill already wrote this to today's `recaps/YYYY-MM-DD.md` —
   read it instead of recomputing where possible.

4. **Decide whether to edit.** Reasons to edit:
   - Hit-rate or Brier worse than the strategy's stated threshold.
   - Repeated mispricing pattern not captured in current strategy.
   - Correlation surprise (two trades turned out related).
   - A research method that consistently produced better forecasts.

   Reasons not to edit: too few data points, no clear lesson. Emit
   `reflection` with `edited: false` either way to mark today done.

5. **If editing:**
   - Read `strategy/current.md` frontmatter, parse `version: vN`,
     increment to `v(N+1)`.
   - **Snapshot:** copy current file to
     `strategy/history/YYYY-MM-DD-v<old_N>.md`. If filename already exists
     today, append a letter suffix (`-v<old_N>a`).
   - Write new `strategy/current.md` with `version: v(N+1)`. Keep the change
     incremental; append rationale to the `# Changelog` section at the bottom.
   - Strategy body owned by the agent: probability calibration methods,
     sizing framework, market selection criteria, correlation rules,
     edge-identification heuristics, minimum-edge floor.

6. **Emit `reflection` event** via `journal`:
   ```json
   {"event_type":"reflection","date":"<YYYY-MM-DD>","edited":true,"prior_version":"v<old_N>","new_version":"v<N+1>","snapshot":"strategy/history/<YYYY-MM-DD>-v<old_N>.md","rationale":"<short>"}
   ```

7. **Conventional commit message** (handled by `persist` skill at end of
   end-of-day routine):
   ```
   feat(strategy): reflect → v<N+1> (snapshot v<old_N>) [cycle <cycle_id>]
   ```

8. **Guardrail recommendation hint.** If reflection thinks
   `config/guardrails.md` should change, call `risk.surface_recommendation(text)`
   so the next daily summary includes it. **Do not edit `guardrails.md`.**

## Failure modes

- **No activity:** acceptable; write `reflection` with `edited: false`.
- **YAML version parse fails:** treat as `v0`; write `v1` snapshot.
- **Snapshot write fails:** do not overwrite `current.md`. Log + exit.
