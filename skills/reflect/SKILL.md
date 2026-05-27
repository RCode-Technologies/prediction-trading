---
name: reflect
description: Daily governance. Reads state/scorecard.json (kept fresh by recalibrate), applies smartness gates, may edit strategy/current.md. Only file it may edit.
inputs: state/scorecard.json, state/calibration.json, strategy/current.md, recent recaps/
outputs: strategy/current.md (if edited) + history snapshot, reflection event
---

# Reflect

Once/UTC date from `daily-close`. Governance, not recomputation — `skills/recalibrate` keeps metrics fresh.

## Hard rules

- Only edits `strategy/current.md`.
- Snapshot on every edit to `strategy/history/YYYY-MM-DD-vN.md`.
- Record uncertainty; never overfit sparse data.

## Steps

1. **Idempotency.** Grep trade-log for `event_type=="reflection" date:<today UTC>` → if found, exit.

2. **Build dataset.** Today's events + trailing-30d unresolved forecasts now resolved or with fresh midpoint. Join by `forecast_id` (fallback: `market_id`/`token_id`/`ts`). Keep all attribution fields incl. `learning_intent`.

3. **Score.** Resolved: Brier `(your_p - outcome)^2`, hit/miss. Unresolved: forecast vs current midpoint / CLV (drift, not truth). Fills: realized P&L if resolved, MTM if open.

4. **Attribute** by `strategy_version`, `thesis_id`, `feature_tags`, `learning_intent`, market class, `source_providers`. Today's `recaps/<date>.md` has most of this; recompute only gaps.

5. **Anti-overfitting gates.** Tighten immediately on severe risk miss / correlation surprise / stale-mark failure / source quality failure. Otherwise need ≥1 of:
   - 5 resolved for same thesis/tag/class,
   - 8 unresolved with consistent adverse drift across ≥2 UTC dates,
   - weekly recap showing same lesson across independent markets.
   
   Weaker → **Pending evidence** only.

6. **Smartness scorecard.** Read from `state/scorecard.json` (preference order):
   1. `state/scorecard.json` if `updated_at >= now - 12h` → use directly.
   2. Today's `recaps/<date>.md` fenced JSON → if scorecard stale.
   3. Recompute from `state/forecasts.resolved.jsonl` (slow path).
   
   **v2 cold-start carve-out:** when `exploit.resolved_n < 5`, regression gate uses `explore.calibration_slope` instead of `exploit.brier_skill`.

7. **Convergent calibration update law.** Per exploit bucket with `resolved_n >= 10`: per `strategy/current.md`. Proposed v(N+1), don't write yet.

8. **Reflection-quality gate.** Simulate v(N+1) on trailing 14d:
   1. Re-derive each `your_p` under proposed calibration + tag + source penalties.
   2. Recompute `brier_skill_after`.
   3. If `brier_skill_after < brier_skill_before - 0.005` AND not a risk-tightening edit → refuse. Emit `reflection edited:false reason:"regression_blocked"`, append to **Pending evidence**, no snapshot, exit.

9. **Auto-revert.** Inspect last 3 `reflection` events. All 3 with `brier_skill < last_good_version.brier_skill` → next edit MUST revert:
   - Copy `last_good_version` snapshot to `current.md`, preserve failed-run as `strategy/history/<date>-v<failed_N>.md`, bump version.
   - Emit `reflection edited:true reason:"auto_revert" reverted_to:"<vN>"`. Skip standard edit.

10. **Exploration retries.** Walk hypothesis registry:
    - `demoted, next_retry_date <= today` → `probation, sizing_mult:0.5`, clear date. Pending: "5 forecasts for promotion".
    - `probation` with ≥5 resolved → batch `brier_skill > 0` → `watch, mult:1.0`; else re-demote `+14d`.

11. **Decide edit.** Edit if: hit-rate/Brier worse than threshold; repeated mispricing pattern; correlation surprise; research method consistently better; new evidence changes thesis status. Don't edit otherwise. Emit `reflection edited:false` to mark today done.

12. **If editing:**
    - Read frontmatter `version: vN` → bump `v(N+1)`.
    - Snapshot: copy to `strategy/history/YYYY-MM-DD-v<old_N>.md`. Conflict → `-v<old_N>a`.
    - Update structured state: decision rules, calibration ledger, hypothesis registry, pending evidence, caveats.
    - Write new `current.md` with `version: v(N+1)`. Append rationale to Changelog.

13. **`reflection` event** via `journal`:
    ```json
    {"event_type":"reflection","date":"<YYYY-MM-DD>","edited":true,"prior_version":"v<old>","new_version":"v<new>","snapshot":"strategy/history/<date>-v<old>.md","reason":"normal|regression_blocked|auto_revert|risk_tighten","reverted_to":null,"metrics":{...},"per_source":[],"per_feature_tag":[],"promoted":[],"demoted":[],"probation_started":[],"probation_resolved":[],"pending":[],"rationale":"<short>"}
    ```

14. **Commit subject:** `feat(strategy): reflect -> v<N+1> [cycle <cid>]` (per `skills/commit`).

15. **Guardrail recommendation.** If `guardrails.md` should change → `risk.surface_recommendation(text)` so daily summary includes it. Never edit guardrails.

## Failure modes

- No activity → `reflection edited:false`.
- No learning fields → score what's possible; add to pending evidence.
- YAML version parse fail → treat as `v0`; write `v1` snapshot.
- Snapshot write fail → do NOT overwrite `current.md`. Log + exit.
- Gate refused → `edited:false reason:"regression_blocked"`, retry next day.
- Auto-revert → normal edit semantics with `reason:"auto_revert"`.
