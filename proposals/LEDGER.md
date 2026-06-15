# Proposal Ledger

Index of every proposal `skills/envision` surfaces, newest first. One row per RFC in this directory.
Maintained by `envision` (daily append + Sunday curation) and `enact` (status on implementation).

**Lifecycle:** `surfaced` → `self_approved` →(enact)→ `enacted` → `live` | `reverted` · or `vetoed`
| `superseded`. `human_application` proposals: `awaiting_human` → `applied` | `declined`.

**Veto (supervisor):** `git revert` the enact commit, set a `status` here to `vetoed`/`declined`, or
direct the agent. No inbound channel exists.

| id | title | lens | bucket | conviction | status | updated | note |
| -- | ----- | ---- | ------ | ---------- | ------ | ------- | ---- |
| 2026-06-15-longshot-calibration-metric | Add a longshot-regime calibration metric; the linear slope is blind where we trade | measurement | human_application | medium | surfaced | 2026-06-15 | Scorecard `calibration_slope` is a degenerate 0.0 because ~all forecasts sit at p<0.10 (10/12 today); propose a log-odds reliability table + longshot-bias scalar. Canonical compute lives in protected-core `recalibrate` → human applies (a read-only `recap` mirror could ship first). |
| 2026-06-14-groom-flag-null-closetime | Make groom flag open forecasts that are silently unresolvable (null close_time) | synthesis (deep) | human_application | high | awaiting_human | 2026-06-14 | Today's 6 trade-window forecasts emitted with `close_time:null` despite fully parsed resolution_criteria — silently unresolvable, caught only by hand. Self-approved, but enact intent gate refused (`denylist`): `skills/groom/` is on the autonomy denylist (repo-structure power). Re-bucketed human_application; one-bullet edit awaits a human. |
| 2026-06-13-maker-vs-taker-paper-probe | Probe liquidity provision (maker) vs crossing the spread (taker) | moonshot / wildcard | human_application | low | surfaced | 2026-06-13 | Challenge the long-only-taker stance: spread is our biggest recurring cost; on thin/one-sided books (e.g. 631145 today) a resting bid may capture it. Paper-only probe first (zero capital); live deployment would touch the human-owned guardrail + capital → human. |
| 2026-06-12-trim-redundant-heartbeats | Trim the two heartbeat fires that overlap richer routines | efficiency / cost | human_application | medium | surfaced | 2026-06-12 | heartbeat `0 */4` double-fires at 04:00 (overnight-watch) + 12:00 (research-window); move to `0 0,8,16,20` → −2 paid invocations/day, zero liveness loss. Manual-cron UI + AGENTS.md mirror = needs human. |
