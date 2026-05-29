---
name: enact
description: Sunday-only bounded self-implementation. Applies ≤1 self_approved, denylist-clean proposal as a single revertible commit; arms + checks auto-rollback. Protected core — the agent executes it but may never edit it.
inputs: proposals/LEDGER.md, the selected proposals/<id>.md RFC, config/autonomy.md, state/scorecard.json, recent trade-log (null_cycle/halt)
outputs: one standalone revertible commit + enactment event + enactment notify; or a refusal (awaiting_human) / enact_failed; auto-rollback revert when a live enactment regresses
---

# Enact

Sundays only, from `daily-close` after the deep `envision` pass. This is where the agent writes its
own code — bounded hard by `config/autonomy.md`. **≤1 enactment per week.**

`enact` is **protected core**: a human authored it, the agent executes it, and the agent can never
edit it (boot integrity audit + persist write gate). That is what makes the intent gate below
trustworthy — the agent cannot remove its own rails.

## Hard rules

- **Self-enactable only.** A proposal whose change-sketch touches any `config/autonomy.md` § denylist
  path, or whose RFC `bucket` is `human_application`, is refused — never written. Protected core ⊆
  denylist, so an enacted commit can never include a protected-core path.
- **One revertible commit.** Exactly the files in the change-sketch, committed standalone (the second
  sanctioned exception to one-commit-per-cycle, alongside mainnet pre-submit). A single
  `git revert <sha>` must fully undo it.
- **Idempotent.** Grep this ISO week for `enactment status:"enacted"` → already enacted this week,
  skip the implement step (auto-rollback still runs). Grep today for an `enactment` event → don't
  repeat on a re-run.
- **Never blocks the cycle.** Any uncertainty → refuse + surface, don't force.

## Steps — auto-rollback check (runs first, every Sunday)

1. **Find the live enactment.** Most recent `enactment status:"enacted"` with no later
   `status:"reverted"` / `status:"live"` for the same `slug`. None → skip to § implement.
2. **Evaluate regression** against the baseline recorded in that event (any one triggers a revert):
   - **Operational:** ≥1 `null_cycle` naming a file the enactment touched, OR ≥2 `null_cycle` in any
     24h since the enactment `sha`.
   - **Rails:** any `protected_core_violation` halt since the enactment. (Capital/market halts are
     *not* attributable — a `self_enactable` change has zero capital effect by construction.)
   - **Forecast quality** (only if a touched file is on the forecasting path — `skills/research`,
     `skills/markets`): trailing `brier_skill` worse than baseline by >0.005 across ≥5 newly-resolved
     forecasts (same threshold as `reflect`).
3. **Revert or graduate.**
   - Regression → `git revert --no-commit <sha>` then commit `revert(agent): auto-rollback <slug> [cycle <cid>]`
     (body: `Reverts <sha>. Reason: <metric>.`) and push it standalone — same push discipline as
     § implement step 8 (bare `git push`; stash-rebase-retry only if rejected). Set LEDGER
     `status: reverted`. Emit `enactment status:"reverted"`. `notify enactment` (suppression-exempt).
   - No regression and the enactment is ≥7 days old → set LEDGER `status: live`, emit
     `enactment status:"live"` (no notify — silence is fine for a graduation).

## Steps — implement (≤1, after auto-rollback)

1. **Cadence gate.** Already an `enactment status:"enacted"` this ISO week → stop (≤1/week).
2. **Select.** The single `self_approved`, non-vetoed proposal in `LEDGER.md` (envision self-approves
   ≤1 on this same cycle). Multiple → highest `conviction`, then `horizon: now > next`. None → stop.
3. **Re-read the RFC** `proposals/<id>.md`. Parse the Change sketch (exact files + edits) and `bucket`.
4. **Intent gate.** Every path the change-sketch would write, checked against `config/autonomy.md`
   § denylist; and `bucket == self_enactable`. Any denylist hit or `human_application` → **refuse**:
   set LEDGER `status: awaiting_human`, emit `enactment status:"refused" reason:"denylist"`,
   `notify enactment`, write **no** code. Stop.
5. **Apply** the change-sketch exactly — additive or localized edits only; no data migration, no
   destructive delete of tracked history.
6. **Validate.** `jq empty` on any touched JSON; `jq -c . <file>.jsonl` on any JSONL; new/edited
   skill + routine files have well-formed frontmatter (`name` + `description`); referenced templates /
   paths exist; markdown parses. Fail → `git checkout HEAD -- <touched paths>` (discard the attempt),
   set LEDGER `status: enact_failed`, emit `enactment status:"failed" reason:"<short>"`,
   `notify enactment`, stop.
7. **Record baseline** for auto-rollback: read `state/scorecard.json` (`brier_skill`, `mean_clv`) +
   current `null_cycle` count. Carried in the enactment event (step 9).
8. **Commit standalone** (the enacted files only — the cycle's other WIP stays uncommitted for
   `persist` at step 12, which is fine: `git push` ignores a dirty tree):
   ```bash
   git add <touched files>            # never -A — scope strictly to the change-sketch
   git commit -m "$(cat <<EOF
   feat(agent): enact <slug> [cycle <cid>]

   Proposal: proposals/<id>.md
   Files: <comma-separated touched paths>
   Veto: git revert this commit, or set proposals/LEDGER.md status to vetoed.
   EOF
   )"
   git push                           # bare ref (global hooks flag "git push origin main")
   # rejected (remote advanced — rare for a single writer)? the enacted files are already
   # committed, so only the cycle WIP is dirty — stash just that, rebase, retry, restore:
   #   git stash push -u && git pull --rebase origin main && git push && git stash pop
   SHA=$(git rev-parse HEAD)          # final, stable sha for the veto recipe + ledger
   ```
   Push still failing → `git revert --no-edit HEAD` (undo the local enact commit), `git stash pop`
   if stashed, emit `enactment status:"failed" reason:"push"`, surface, stop. Else set LEDGER
   `status: enacted`, record `SHA` (the `notify enactment` veto line carries it).
9. **`enactment` event** via `journal` (§ Event). 10. **`notify enactment`** (suppression-exempt —
   the human must always see autonomous code changes + how to veto).

## `enactment` event (via `journal`)

```json
{"event_type":"enactment","date":"<YYYY-MM-DD>","proposal_id":"<id>","slug":"<slug>","status":"enacted|reverted|live|refused|failed","sha":"<commit sha|null>","files":["<path>"],"baseline":{"brier_skill":<n|null>,"mean_clv":<n|null>,"null_cycle_count":<int>},"reason":"<short|null>"}
```

Governance event — does **not** trigger the recalibrate hook.

## Failure modes

- No `self_approved` proposal → silent no-op (a quiet week is fine).
- Denylist hit / `human_application` → refuse, `awaiting_human`, surface. The human applies it.
- Validation fail → discard, `enact_failed`, surface; the proposal stays for a human or a fixed re-draft.
- Push fail → revert local, `failed`, surface; next Sunday retries.
- Notify fail → `notification kind:"enactment_failed"`; never blocks (notify never blocks).
