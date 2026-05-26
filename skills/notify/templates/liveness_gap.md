# `liveness_gap`

Sent at most once per cycle that detected a scheduler gap. Suppression-exempt (paper AND mainnet).

```
💤 *Scheduler gap detected* · `<mode>`

Last completed
  <last_completed_at>
Gap
  <gap_hours>h (threshold 9h)
Inferred missed
  <missed_routines>
This cycle
  *<phase>* · `<cycle_id>`
```

Notes:
- A `liveness_gap` means the cron timer in Claude Code UI did not fire (or the agent could not run) for one or more scheduled routines.
- The current cycle continues; this is a backward-looking alert about prior silence.
- If gaps recur, check the cron timer configuration in the Claude Code UI.
