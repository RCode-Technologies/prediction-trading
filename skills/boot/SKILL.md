---
name: boot
description: Wake-up sequence for every routine — sync main, validate state, acquire lock, check halts, liveness-gap check, emit cycle_start.
inputs: caller routine name, phase tag
outputs: cycle_id, lock acquired, validated state, halt status, liveness gap (if any)
---

# Boot

## Steps

1. **Sync.** `git fetch origin && git checkout main && git pull --rebase origin main`. Agent operates on `main` only. Failure → exit non-zero (no log line possible).

2. **`cycle_id` = `YYYYMMDDTHHMMSSZ-<8-lower-hex>`** UTC (e.g. `20260524T133000Z-3f9c8a21`).

3. **Validate boot files** (`jq empty`):
   - `config/mode.json` — keys: `schema_version`, `network`, `cadence_minutes`, `observation_only`, `observation_started_at`, `observation_hours`, `mainnet_attestation`.
   - `state/{halts,lock,portfolio,cycle-index}.json`.
   - `state/trade-log.jsonl` tail (~50 lines parse).
   - `strategy/current.md`.
   
   Failure → append `preflight_failed` if log appendable, jump to `persist`, exit.

4. **Lock** (`state/lock.json`):
   - `active && now < expires_at` → another cycle in flight, exit clean, no commit. TTL 55 min.
   - `active && now >= expires_at` → stale. Append `stale_lock_recovered` (this + prior cycle_id).
   - Acquire: atomic write `{schema_version:1, active:true, cycle_id, started_at:<now>, expires_at:<now+55m>}`.

5. **Halts.** `halts.json.active==true` → compute `halt_age_days = floor((now − triggered_at)/86400)`,
   then call `notify` kind `halt_active` (suppression-exempt, date-deduped once per UTC date — see
   `skills/notify`) with `{reason, triggered_at, halt_age_days}`. An active halt must re-alert the human
   **every day** until cleared, not only at trip time (the 2026-05-29 → 06-10 nav halt went silent for
   12 days after its single trip alert). Return halt flag. **No capital/phase work** — but read-only
   calibration still runs: each routine's halt branch jumps to its `recalibrate` step (`sweep`/`snap_clv`),
   then `phase_completed` → `persist`. A halt stops capital actions, never the learning loop or the push.

5b. **Protected-core integrity audit (deterministic — no narrative judgement).** Run EXACTLY this
   snippet and act ONLY on its printed verdict. The path list mirrors `config/autonomy.md` § Protected
   core (keep in sync):
   ```bash
   AGENT_ID="${GIT_AUTHOR_EMAIL:-agent@prediction-trading.local}"
   violations=""
   for p in config/autonomy.md config/guardrails.md AGENTS.md \
            skills/boot skills/persist skills/circuit-breaker \
            skills/enact skills/recalibrate skills/risk; do
     a=$(git log -1 --format=%ae -- "$p")   # ONLY the most-recent commit's author
     [ -z "$a" ] && continue                 # no history yet → skip
     [ "$a" = "$AGENT_ID" ] && violations="$violations $p"
   done
   echo "PROTECTED_CORE_VIOLATIONS:[$violations ]"
   ```
   **Halt iff the printed list is non-empty** → `circuit-breaker.halt("protected_core_violation", <paths>)`
   with `offending_commit = git log -1 --format=%h -- <first violating path>`; return halt flag, no phase
   work. **Empty list → 5b PASSES; continue to 5c.**

   **Anti-confabulation rules (HARD — a fabricated halt on 2026-06-10 stopped the system for hours:**
   **the cycle invented a "genesis commit" that was actually an unrelated heartbeat and halted on it):**
   - Only `git log -1` (the *newest* commit) author counts. The genesis/oldest author is IRRELEVANT — the
     repo was scaffolded under the agent identity, so most protected files' *first* commit is agent-authored;
     a single later human commit fully cleanses it. NEVER use `git log … | tail -1` or reason from genesis.
   - The ONLY admissible evidence is the `PROTECTED_CORE_VIOLATIONS` list printed by the snippet **in this
     cycle**. Do not halt from memory, a recalled/guessed hash, a recent edit, or a plausibility argument.
     No paths printed ⇒ no violation, full stop. Never write an `offending_commit` you did not just read
     from `git log`.
   - A protected file last-committed by the human identity (`!= $AGENT_ID`, e.g. `mail@rcode.tech`) is
     expected and clean — that is exactly how rails are maintained.

   This is the backstop behind `enact`'s intent gate and `persist`'s write gate (defense in depth).

5c. **NAV reconciliation invariant (v3, AC #13).** Recompute book NAV from `state/portfolio.json`:
   `book_nav = cash_usdc + Σ(shares × mark_liquidation)`. Reconstruct **expected cash** from trade-log
   history: `starting_capital − Σ(BUY notional_usdc + fee_usdc) + Σ(SELL notional_usdc − fee_usdc)
   + Σ(deposit) − Σ(withdrawal)`. SELL `notional_usdc` is the **full proceeds** (`shares × fill_price`),
   NOT realized P&L — proceeds are what actually lands in cash. (Verified 2026-06-10:
   `10000 − 227.20 − 276.28 + 243.13 = 9739.65 == cash_usdc`.) Two checks, both fail-closed:
   - `|expected_cash − cash_usdc| > 0.01` (absolute, not relative) → `circuit-breaker.halt("nav_reconciliation_failed", expected_cash, cash_usdc, delta)`.
   - A position whose `shares` moved with **no** corresponding `paper_fill`/`mainnet_fill` in the trade-log
     (cross-check current `shares` against Σ of fills for that `token_id`) → same halt.
   On halt: return halt flag, no phase work. **Positions are NEVER scaled to fit a baseline** — capital changes
   are only ever explicit `deposit`/`withdrawal` events (see `skills/journal`); the prior 185× `manual_baseline_reset`
   class of distortion is structurally impossible. Keep it cheap — one pass over the trade-log tail.

6. **Observation transition.** `observation_only==true` and `now >= observation_started_at + observation_hours*3600` → set `observation_only=false`. Don't commit here — `persist` bundles it into the routine's single commit.

7. **Liveness-gap check.** `gap_seconds = now - cycle-index.last_completed_at`. > 32400 (9h, 1.5× the worst expected 6h between cycles) → append:
   ```json
   {"event_type":"liveness_gap","last_completed_at":"<iso>","gap_seconds":<n>,"threshold_seconds":32400,"missed_routines_inferred":[<list>]}
   ```
   `missed_routines_inferred` from cron frontmatter ∩ gap window. Informational only — not a halt.

8. **`cycle_start`** via `journal`:
   ```json
   {"schema_version":1,"event_id":"<cid>-cycle_start-1","cycle_id":"<cid>","event_type":"cycle_start","ts":"<now>","mode":"<network>","phase":"<caller>"}
   ```

8b. **Liveness alert.** If step 7 emitted `liveness_gap`, call `notify` kind `liveness_gap` (suppression-exempt). Continue regardless.

9. **Return** `{cycle_id, halts_active, mode, observation_only, liveness_gap_seconds}`.

## Failure modes

- Pull/rebase fail → state diverged; no trading; next cycle retries.
- JSON corruption → preflight fail; `persist` still attempts lock release.
- Lock write fail → do not trade.
