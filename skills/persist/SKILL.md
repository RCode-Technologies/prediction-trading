---
name: persist
description: End-of-cycle bookkeeping. Atomic writes, validation, null-cycle audit, lock release, one routine commit + pull/rebase + push.
inputs: pending changes in working tree, cycle_id
outputs: HEAD == origin/main, lock released, cycle_end + (maybe) null_cycle event
---

# Persist

Push is the only success criterion. Direct push to `main`, no PRs. One Conventional Commit per cycle (mainnet pre-submit and Sunday `enact` self-implementation are the sanctioned exceptions). No follow-up bookkeeping commits.

## Git identity (idempotent)

```bash
git config --global user.email "${GIT_AUTHOR_EMAIL:-agent@prediction-trading.local}"
git config --global user.name  "${GIT_AUTHOR_NAME:-Polymarket Trading Agent}"
```

## Push preflight (before first commit)

```bash
git push --dry-run 2>&1 | head -5   # bare — NEVER name the ref; global hooks block any "git push…main" pattern
```

Auth failure → `circuit-breaker.halt("push_permission_missing")`. Fail fast. A hook block
(`BLOCKED: …feature branches…`) is NOT an auth failure — re-run bare, never add the ref.

## Atomic write rule

JSON: `jq '<expr>' f.json > f.json.tmp && mv f.json.tmp f.json`. JSONL: `>>` only; never edit prior lines.

## Steps

1. **Validate state:**
   ```bash
   jq empty config/mode.json state/portfolio.json state/halts.json state/lock.json state/cycle-index.json
   jq -c . state/trade-log.jsonl > /dev/null
   ```
   Fail → `persist_conflict` + notify + exit (no commit).

1b. **Protected-core write gate.** `persist` always commits under the agent identity, so every commit
   is agent-authored. Check the working tree for changes to any `config/autonomy.md` § Protected core
   path (`git status --porcelain -- <path>…`). Any match → the agent is attempting to alter its own
   rails: reset those paths to HEAD (`git checkout HEAD -- <paths>`, discarding the illegitimate edit —
   the agent always boots from clean `main`, so a dirty protected file can only be this cycle's own
   write; the intent is preserved in the proposal RFC + `enactment` event), then
   `circuit-breaker.halt("protected_core_violation", paths)`. The cycle then persists the halt normally
   (`fix(halt): protected_core_violation`) — the discarded paths are not in the commit.

2. **Null-cycle audit.** Count event types this cycle (`cycle_id == <cid>`) vs floor in `strategy/current.md` § Decision rules (also mirrored in AGENTS.md). Floor missed → append `null_cycle` + notify (suppression-exempt). Still commits + pushes — silent failure is the enemy. If the floor was missed **because a halt blocked phase work** (`halts.active` this cycle), append the event with `reason:"halted"` instead of `"floor_missed"` and **skip its notify only** (boot's daily `halt_active` alert already covers the human) — the miss stays auditable in the log instead of vanishing.
   ```json
   {"event_type":"null_cycle","reason":"floor_missed|halted","required":{...},"actual":{...},"phase":"<phase>"}
   ```

3. **`nav_snapshot`** via `journal`. Append `{ts, nav_usdc}` to `cycle-index.json.nav_snapshots` (cap 1000).

4. **`cycle-index.json`:** set `last_cycle_id`, `last_started_at`, `last_completed_at`. `last_pushed_commit` deprecated (would require a 2nd commit).

5. **Release lock** atomically: `{active:false, cycle_id:null, started_at:null, expires_at:null}`.

6. **`cycle_end`** via `journal`. While `halts.json.active`, it MUST carry `halted:true, halt_reason:"<reason>"`
   (uniform — every halted cycle greps identically), and the commit subject appends ` halted`
   (`skills/commit` § Routine-mapped subjects).

7. **Commit once.** Load `skills/commit/SKILL.md` for format. Compose + run:
   ```bash
   git add -A
   git commit -m "<formatted per skills/commit>"
   ```
   A non-conforming message is a contract violation. Never `--no-verify`.

8. **Pull/rebase/push:**
   ```bash
   git pull --rebase origin main
   git push   # no explicit ref — global hooks flag the literal "git push origin main" pattern
   ```
   Never `--force`. On rejection: retry pull/rebase once. Still failing → `persist_conflict` + notify + non-zero exit. Stale lock recovers next cycle.

9. **Verify push:**
   ```bash
   git fetch origin main
   [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] || exit 1
   ```
   Mismatch → `persist_conflict` + notify + non-zero exit.

## Mainnet pre-submit push (from `trade`)

Only exception to one-commit-per-routine. Mainnet order intent must be durable before SDK submission:

```bash
git add state/trade-log.jsonl
git commit -m "feat(decision): pre-submit <idempotency_key> [cycle <cid>]"
git pull --rebase origin main && git push
```

Push fail → `trade` aborts before SDK call.

## Failure modes

- Push unresolvable → unsuccessful cycle. Idempotency keys on pre-submit decisions protect mainnet duplicates.
- State corrupted after a routine write → `git checkout -- <file>` if possible, log, notify, exit.
- Force-push by automated routine → forbidden, abort. `--force-with-lease` only via human direction.
