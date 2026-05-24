---
name: circuit-breaker
cron: null
cron_tz: null
phase: circuit_breaker
expected_frequency: reactive — invoked from other routines via skills/risk; not its own scheduled cloud routine
---

# Circuit Breaker — reactive

**Not on a schedule.** This routine documents the halt protocol that
`skills/risk` enforces on demand. Other routines call into `skills/risk`
which uses these rules; this file is the canonical reference humans read
to understand what triggers a halt and how to recover.

## When this fires

- **24h loss** ≥ 10% of baseline NAV (formula in `config/guardrails.md`).
  Evaluated by `skills/risk` in `trade-window`, `daily-close`, and
  `overnight-watch` (after their `nav_snapshot`).
- **Mainnet cancel failure** on a partial fill (set by `skills/trade`).
- **Post-submit push failure** for mainnet (set by `skills/trade`).
- **No baseline NAV available** and `starting_capital` missing
  (`reason: "no_baseline_nav"`).

## What happens when it fires

1. `skills/risk` writes `state/halts.json`:
   ```json
   {"schema_version":1,"active":true,"reason":"<reason>","triggered_at":"<now>","cycle_id":"<cycle_id>"}
   ```
2. `skills/journal` appends a `halt` event with `baseline_nav`,
   `current_nav`, `pnl_usdc`, `pnl_pct`, `reason`.
3. `skills/notify` sends `circuit_breaker` payload (paper AND mainnet per
   ADR 0008).
4. `skills/persist` commits + pushes the halt with message:
   `fix(halt): <reason> [cycle <cycle_id>]`.
5. Cycle exits before any further sizing/trade activity. Already-executed
   trades in the same cycle remain logged (breaker stops *future* cycles).

## What happens on the next scheduled cycle

`skills/boot` reads `halts.active == true` and returns the halt flag to
the calling routine. The calling routine **skips its phase work** and:

- Calls `skills/notify` so daily-summary (if due) surfaces the active halt.
- Calls `skills/persist` to release the lock and update `cycle-index.json`.
- Exits.

## Recovery (human-only)

The agent **never** clears the halt. A human edits `state/halts.json`:

```bash
jq '.active=false | .reason=null | .triggered_at=null | .cycle_id=null' \
   state/halts.json > state/halts.json.tmp && mv state/halts.json.tmp state/halts.json
git add state/halts.json
git commit -m "chore(halt): cleared by <handle> after review"
git push
```

The next scheduled routine reads `active: false` and proceeds normally.

## Edge cases

- **Stale marks on >50% of positions:** breaker is **not** fired. Instead
  `skills/risk` emits `preflight_failed` with
  `reason: "stale_marks_skip_breaker"`; the next cycle re-evaluates with
  fresh data.
- **Breaker fires in `overnight-watch` while US is asleep:** Telegram
  notification still goes out; trading stays halted until human ack
  (daily-close at 22:00 UTC will resend the status in the daily summary).
