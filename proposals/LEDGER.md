# Proposal Ledger

Index of every proposal `skills/envision` surfaces, newest first. One row per RFC in this directory.
Maintained by `envision` (daily append + Sunday curation) and `enact` (status on implementation).

**Lifecycle:** `surfaced` → `self_approved` →(enact)→ `enacted` → `live` | `reverted` · or `vetoed`
| `superseded`. `human_application` proposals: `awaiting_human` → `applied` | `declined`.

**Veto (supervisor):** `git revert` the enact commit, set a `status` here to `vetoed`/`declined`, or
direct the agent. No inbound channel exists.

| id | title | lens | bucket | conviction | status | updated | note |
| -- | ----- | ---- | ------ | ---------- | ------ | ------- | ---- |
| 2026-06-12-trim-redundant-heartbeats | Trim the two heartbeat fires that overlap richer routines | efficiency / cost | human_application | medium | surfaced | 2026-06-12 | heartbeat `0 */4` double-fires at 04:00 (overnight-watch) + 12:00 (research-window); move to `0 0,8,16,20` → −2 paid invocations/day, zero liveness loss. Manual-cron UI + AGENTS.md mirror = needs human. |
