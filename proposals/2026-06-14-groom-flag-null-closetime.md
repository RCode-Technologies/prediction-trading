---
id: 2026-06-14-groom-flag-null-closetime
title: Make groom flag open forecasts that are silently unresolvable (null close_time)
created: 2026-06-14
lens: synthesis (deep)
status: awaiting_human
bucket: human_application
conviction: high
reversibility: trivial
horizon: now
supersedes: null
---

> **Intent-gate correction (2026-06-14 enact).** This RFC was self-approved as `self_enactable`, but
> `config/autonomy.md` § denylist lists **`skills/groom/`** under "Repo-structure power". The change
> sketch touches `skills/groom/SKILL.md`, so `enact`'s intent gate refused it (`reason: denylist`) and
> wrote no code. Re-bucketed `human_application`, status `awaiting_human`. A human can apply the
> one-bullet edit below directly. The gate did its job — envision mis-bucketed, enact caught it.

## Claim

`skills/groom` should lint `state/forecasts.open.jsonl` for `resolved:false` rows with a null/absent
`close_time` and report them in `findings[]`. Such rows are **silently unresolvable** — `recalibrate`
can never take their `close` CLV snap nor resolve them via Gamma, so they accumulate as dead weight in
the open ledger and quietly waste calibration data (a scarce resource per the AGENTS cost model).

## Evidence

On 2026-06-14 the trade-window emitted **6 forecasts** (`20260614T180311Z-07460a75-fc-1..6`) whose
ledger rows all carry `close_time:null` — despite the forecast events carrying *fully parsed*
`resolution_criteria` naming explicit dates (e.g. "checked Jun 30 2026 12:00 ET"). The 06-13 cohort,
by contrast, had proper `close_time` values. The regression was caught only by manual inspection
during this daily-close; no automated guard flagged it. Groom already lints schema/budget/referential
integrity but has no open-forecast resolvability check.

## Why it might be wrong (steelman)

- The real fix is upstream (populate `close_time` at emission), so a groom flag treats a symptom, not
  the cause. True — but groom is report-only by design; surfacing the symptom weekly is exactly its
  job, and it gives the human/`reflect` the signal to fix the cause. Detection and fix are separable.
- A forecast could legitimately have no close_time (e.g. open-ended market). In practice Polymarket
  binary markets always have an end date; a null is a bug, not a valid state. Even if some are valid,
  a `findings[]` line is non-blocking (report-only) — no false-positive cost beyond one noted line.

## Cheapest falsifying experiment

Run the amended groom on the current `state/forecasts.open.jsonl`: it must list exactly the 6
`fc-1..6` ids from cycle `07460a75` and nothing else. If it lists healthy rows (with valid
close_time) it is over-flagging and should be reverted.

## Impact & cost

- **Learning:** prevents silent loss of calibration data — the highest-value scarce resource after
  capital/correctness. Catches the whole class of "forecast emitted but unresolvable" regressions.
- **Invocation/token cost:** zero new cycles; one extra `jq` pass over a small file inside the
  already-running Sunday groom; ≤ a few lines added to the weekly recap when triggered.
- **Capital effect:** none.
- **Protected core:** none — `skills/groom` is not a protected-core path.

## Change sketch

File: `skills/groom/SKILL.md`. In step 4 ("Lint — report only"), insert a new bullet immediately
after the existing **Schema:** bullet:

```
   - **Open-forecast integrity:** flag any `resolved:false` row in `state/forecasts.open.jsonl` with
     null or absent `close_time` (silently unresolvable — `recalibrate` can never snap its `close`
     window or resolve it via Gamma). List the offending `forecast_id`s in `findings[]`.
```

Additive only; no other lines change. Revert = delete the inserted bullet (`git revert` the commit).
