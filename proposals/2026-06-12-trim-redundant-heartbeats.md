---
id: 2026-06-12-trim-redundant-heartbeats
title: Trim the two heartbeat fires that overlap richer routines
created: 2026-06-12
lens: efficiency / cost
status: surfaced
bucket: human_application
conviction: medium
reversibility: trivial
horizon: next
supersedes: null
---

## Claim

The `heartbeat` cron `0 */4` fires at 00/04/08/12/16/20 UTC, but **04:00 collides with
overnight-watch and 12:00 collides with research-window**. Those two routines already emit a
`nav_snapshot` and run `recalibrate`, so the coincident heartbeats add zero liveness signal — they
are pure duplicate paid invocations. Move heartbeat to `0 0,8,16,20` (4/day instead of 6),
eliminating ~2 paid sessions/day (~60/month, ~20% of the daily metabolism) with **no** loss of
liveness coverage.

## Evidence

- 2026-06-12 trade-log shows the double-fire directly: overnight_watch `nav_snapshot` at 04:09 **and**
  a separate heartbeat cycle at 04:11/04:12; research_window `phase_completed` at 12:13 **and** a
  heartbeat at 12:12. Two cron sessions doing the same liveness work in the same minute.
- AGENTS.md § Cost model: "The metered unit is the **scheduled invocation** — each cron fire is one
  paid agent session." Two redundant fires/day is the single cheapest invocation saving available.
- Liveness math: with heartbeat at 0,8,16,20 + routines at 4,12,18,22, every 2–4h window still emits
  a `nav_snapshot`. Max inter-cycle gap = 4h, far under boot's 9h `liveness_gap` threshold. Coverage
  is unchanged; only the duplicates are removed.
- VISION.md open question #2 explicitly asks: "Is 10 invocations/day the right metabolism?" This is a
  concrete, bounded first answer: 8/day with identical coverage.

## Why it might be wrong (steelman)

- If a content routine ever **fails to emit** its `nav_snapshot` (e.g. crashes early), the coincident
  heartbeat is a cheap backstop that today silently covers for it. Removing it could let a single
  routine failure widen a liveness gap by one slot.
- A heartbeat is the lightest cycle; the marginal token cost of the two duplicates is small, so the
  saving is invocation-count, not compute — worth it only if invocations are the binding constraint
  (AGENTS.md says they are).
- Manual cron means a human must make the change and could mis-edit the schedule, briefly creating a
  real gap.

## Cheapest falsifying experiment

Grep the last 30d of trade-log for any `liveness_gap` event whose window would have been covered
**only** by a 04:00 or 12:00 heartbeat (i.e. where the colliding routine did not emit its own
`nav_snapshot` that hour). Zero such cases ⇒ the duplicates have never once been load-bearing ⇒ safe
to drop. One or more ⇒ keep them (the backstop is real). Pure local log read, 0 sources, 0 capital.

## Impact & cost

- **Invocations:** −2/day (−~20% of the 10/day metabolism), recurring. No token or capital effect.
- **Liveness:** unchanged (max gap 4h ≪ 9h threshold).
- **Risk:** the steelman backstop case; mitigated because boot's `liveness_gap` check + the named
  routines' own `nav_snapshot` still cover every window.
- **Capital:** none.

## Change sketch

`human_application` — the schedule lives in the **Claude Code UI manual cron**, not a repo file
(AGENTS.md § Schedule: "manual cron in Claude Code UI"; "Scheduler is manual"). The agent cannot
self-enact a UI cron edit, so this needs a human:

1. In the Claude Code cron UI, change the `heartbeat` timer from `0 */4 * * *` to `0 0,8,16,20 * * *`.
2. Update the doc mirror in `AGENTS.md` § Schedule (the `0 */4` row) and
   `routines/heartbeat.md` frontmatter `cron:` to match — this part is a normal repo edit a human (or
   a future `enact` pass, if it ever covers non-protected doc files) can apply, but it must stay in
   sync with the UI or the docs lie.

Note: `AGENTS.md` is protected core, so even the doc-mirror edit is `human_application`, not
self-enactable. Surfaced for human review, not auto-applied.
