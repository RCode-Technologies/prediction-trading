---
name: persist
description: End-of-cycle bookkeeping. Atomic writes, validation, lock release, one routine commit + pull/rebase + push. **A cycle that does not push is unsuccessful.**
inputs: pending changes in working tree, cycle_id
outputs: HEAD pushed, lock released, cycle_end event
---

# Persist

Push is the **only** success criterion. The agent pushes directly to `main` — no PRs, no feature branches. Verify `HEAD == origin/main`. Scheduled routines produce one pushed Conventional Commit whenever no mainnet pre-submit safety commit is required.

Do **not** create follow-up bookkeeping commits. A commit cannot contain its own final SHA without another commit; clean one-commit routine history is preferred over exact in-repo `last_pushed_commit` tracking.

## Git identity (idempotent — every cycle)

```bash
git config --global user.email "${GIT_AUTHOR_EMAIL:-agent@prediction-trading.local}"
git config --global user.name  "${GIT_AUTHOR_NAME:-Polymarket Trading Agent}"
```

## Push preflight (before first commit)

```bash
git push --dry-run origin main 2>&1 | head -5
```

Auth failure (`Permission denied`, `could not read Username`, `403`, `Repository moved`) → `circuit-breaker.halt("push_permission_missing")`. Fail fast.

## Atomic write rule

JSON: `jq '<expr>' f.json > f.json.tmp && mv f.json.tmp f.json`. JSONL: `>>` only; never edit prior lines.

## End-of-cycle

1. **Validate all state:**
   ```bash
   jq empty config/mode.json state/portfolio.json state/halts.json state/lock.json state/cycle-index.json
   jq -c . state/trade-log.jsonl > /dev/null
   ```
   Fail → `persist_conflict` + notify + exit (no commit).

1b. **Null-cycle audit (v2).** Read this cycle's event types from `trade-log.jsonl` (filter `cycle_id == <cid>`). Compare against the routine's expected floor (defined in `strategy/current.md` § Action commitment per cycle):

   | phase            | required events                                                       |
   | ---------------- | --------------------------------------------------------------------- |
   | research_window  | `research_note >=1`, `candidate_rank >=1`, `forecast >=3`             |
   | trade_window     | `forecast >=3`                                                        |
   | daily_close      | `recap >=1`, `reflection >=1`                                         |
   | overnight_watch  | `nav_snapshot >=1`                                                    |

   Any floor missed → append:
   ```json
   {"event_type":"null_cycle","reason":"floor_missed","required":{"forecast":3,"research_note":1,"candidate_rank":1},"actual":{"forecast":<n>,"research_note":<n>,"candidate_rank":<n>},"phase":"<phase>"}
   ```
   Then call `notify` kind `null_cycle` (paper + mainnet, suppression-exempt).

   This is auditable evidence, NOT a halt. The cycle still commits + pushes so the failure is durable — silent failure is the actual enemy. If the floor was missed because the breaker is active, suppress `null_cycle` (the halt already explains why).

2. **`nav_snapshot`** via `journal`:
   ```json
   {"event_type":"nav_snapshot","nav_usdc":<n>,"cash_usdc":<n>,"positions_value_usdc":<n>}
   ```
   Append `{ts, nav_usdc}` to `cycle-index.json.nav_snapshots` (cap 1000).

3. **`cycle-index.json`:** set `last_cycle_id`, `last_started_at`, `last_completed_at`. Do not mutate `last_pushed_commit` for this cycle; it is deprecated for exact tracking because updating it would require a second commit.

4. **Release lock** (atomic): `{schema_version:1, active:false, cycle_id:null, started_at:null, expires_at:null}`.

5. **`cycle_end`** via `journal`.

6. **Commit once.** Load `skills/commit/SKILL.md` for the canonical message format (types, scopes, subject rules, routine→subject table). Compose subject + body per that contract and run:
   ```bash
   git add -A
   git commit -m "<formatted subject + body per skills/commit>"
   ```
   **A commit message that doesn't pass `skills/commit` is a contract violation.** Do NOT add `--no-verify`; fix the message instead.

7. **Pull/rebase/push:**
   ```bash
   git pull --rebase origin main
   git push
   ```
   Use `git push` (no explicit ref). Direct push to main is the intentional policy for this repo (see `AGENTS.md` § Persistence + push policy); some environments have a global pre-push hook that flags the literal pattern `git push origin main`, so default-upstream form is preferred. Never `--force`, never `--no-verify`. On rejection: retry pull/rebase **once**. Still failing → `persist_conflict` + notify + non-zero exit. Stale lock recovers next cycle.

8. **Verify push:**
   ```bash
   git fetch origin main
   LOCAL=$(git rev-parse HEAD)
   REMOTE=$(git rev-parse origin/main)
   [ "$LOCAL" = "$REMOTE" ] || exit 1
   ```
   Mismatch → `persist_conflict` + notify + non-zero exit.

9. **Stop.** Do not amend or create a follow-up `last_pushed_commit` commit. If an operator needs the pushed SHA, use `git rev-parse origin/main` outside tracked state.

## Mainnet pre-submit push (from `trade`)

This is the safety exception to one-commit routine history. A mainnet order intent must be durable before SDK submission; the routine may therefore have a pre-submit decision commit plus the final persist commit.

```bash
git add state/trade-log.jsonl
git commit -m "feat(decision): pre-submit <idempotency_key> [cycle <cid>]"
git pull --rebase origin main && git push origin main
```

Push fail → `trade` aborts before SDK call (order not submitted).

## Failure modes

- Push unresolvable → unsuccessful cycle. Idempotency keys on pre-submit decisions protect mainnet duplicates.
- State corrupted after a routine write → `git checkout -- <file>` if possible, log, notify, exit.
- Plain force-push attempted by an automated routine → forbidden, abort. Human-directed history consolidation may use `--force-with-lease` per `AGENTS.md`.
