---
id: 2026-06-16-clv-by-liquidity-bucket
title: Segment CLV by book-liquidity bucket — is our primary learning signal valid, or thin-book noise?
created: 2026-06-16
lens: failure / surprise
status: surfaced
bucket: human_application
conviction: medium
reversibility: easy
horizon: next
supersedes: null
---

## Claim

Our headline learning signal — CLV (`clv_mean`, the fast-learning pulse that drives the scorecard while `resolved_n < 30`) — is reported as a single blended number per intent/`edge_source`, with **no liquidity stratification**. On thin or one-sided books the midpoint is noisy and often untradeable, so a negative CLV there may be **microstructure noise, not prediction error**. Add a CLV slice by book-liquidity bucket (e.g. two-sided depth tiers) so we can tell whether our persistently negative CLV is a real forecasting deficit or an artifact of forecasting markets we can't trade.

## Evidence

- **Today's surprise (Tue failure lens):** of 6 open forecasts due a CLV snap, **2 had empty/one-sided books** (`a744c807-F6` empty; `62cc61a4-F6` a 0.001 longshot with ask-only) — snaps deferred because no midpoint could be formed. We routinely emit forecasts on markets whose books can't even produce a CLV reading.
- The `none` edge_source slice (no thesis) dominates the open ledger (**clv_n 32, clv_mean −0.0201, hit-rate 0.3125**) — the worst slice — and plausibly overlaps the thinnest books, since thesis-free explore probes are assigned regardless of liquidity (`skills/markets` keeps no-thesis candidates; `rank` only weights `liquidity_num` softly, never floors it).
- Every reflection for 2+ weeks has logged "explore CLV mean negative, monitor" (now −0.0020 over 75 snaps) without being able to say **why**. Liquidity stratification is the missing cut that would turn "monitor" into a decision.

## Why it might be wrong (steelman)

- CLV could be uniformly negative across liquidity tiers — i.e. we genuinely forecast slightly worse than the market everywhere — in which case the segmentation adds a column and changes nothing. Sample is still thin (75 explore snaps); slicing by 3–4 liquidity buckets leaves ~15–25 each, near the noise floor.
- `liquidity_num` (Gamma) and live two-sided book depth (CLOB) are different things; the cheap-to-store field may not predict snap-time tradeability well, so the bucket label could be miscalibrated.
- This is measurement, not edge. It tells us whether to trust CLV; it does not by itself improve forecasts.

## Cheapest falsifying experiment

Read-only, zero new sources, zero capital: over the **existing** `clv_snaps` in `state/forecasts.{open,resolved}.jsonl`, attach each forecast's `liquidity_num` (already on the candidate record / universe cache) and compute `clv_mean`/`clv_hit_rate`/`clv_n` split into 2–3 liquidity tiers. **Kill condition:** if thin- and thick-book tiers have CLV within ~1 standard error of each other, the thin-book-noise hypothesis is dead and the single number stands. **Confirm condition:** if the thinnest tier is materially more negative and the liquid tier is ~flat/positive, CLV is partly noise and (a) the scorecard should report the liquid-tier CLV as the honest skill signal and (b) the explore batch should floor on two-sided depth.

## Impact & cost

- **Learning impact:** potentially foundational — validates or discredits the metric the whole cold-start learning loop leans on. Higher leverage than any new edge source while the signal itself is unverified.
- **Invocation/token cost:** none new — rides the existing `daily-close`/`overnight-watch` sweep; pure local aggregation over snaps already stored.
- **Capital effect:** none.
- **Why human_application:** the canonical compute belongs in `skills/recalibrate` (protected-core rail — agent may run, never edit) and the schema in `skills/journal`. Per the autonomy denylist this cannot self-enact. A **read-only `recap`-side mirror** (a derived liquidity×CLV table in the daily smartness scorecard, computed from existing fields) could ship first as a non-protected, reversible preview — same staging pattern the 06-15 longshot-calibration proposal used.

## Change sketch (for the human / staged mirror)

- **Mirror first (non-protected, reversible):** in `skills/recap`, after reading `state/scorecard.json`, compute a `by_liquidity_bucket[]` table from `state/forecasts.{open,resolved}.jsonl` (`liquidity_num` tiers: `<5k`, `5k–25k`, `>25k`) × `{clv_mean, clv_hit_rate, clv_n}`, and embed it in the Smartness-scorecard JSON block of `recaps/<date>.md`. Read-only, no protected file touched.
- **Canonical (human-applied):** promote the same computation into `skills/recalibrate.snap_clv` step 4 so `state/scorecard.json` carries `by_liquidity_bucket[]` natively, and add the field to the `journal` scorecard schema. Both are protected-core / canonical-schema edits → human applies.
- If the liquid tier proves ~flat-or-positive, follow up with a separate proposal to floor the explore batch on two-sided book depth (touches `skills/markets` ranking — its own RFC).
