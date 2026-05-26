---
cycle_id: 20260526T181010Z-4374b9b4
phase: trade_window
ts: 2026-05-26T18:13:00Z
source_ts: 2026-05-26T18:12:37Z
sources_used_this_routine: 0
budget_remaining_after: 1
research_overlap: none — research_window missed today; degraded budget unused (no actionable thesis to test)
mode: paper (observation_only now false; first cycle post-observation)
inputs: research/2026-05-24/watchlist.md (2d old), refreshed CLOB books only
---

# Candidates — 2026-05-26 (trade-window)

## Coverage gap

`research_window` (12:00 UTC) was missed today (phase_missed event emitted). Degraded source budget is 1, none spent — fresh research would not change `your_p` without a new thesis card, and re-pulling Gamma for the Gabbard/Iran/Machado themes from 2d ago has no link to a sized trade today (the prior watchlist explicitly logged that those themes don't map to liquid markets in the top-100 volume slice). CLOB book re-checks below are safety re-pulls, not research-budget sources.

## Watchlist refresh (CLOB book pulls, ≤15min, safety not research)

| rank | market_id | question | side | best_bid | best_ask | midpoint | spread_pp | close | your_p | market_p | edge_bps | stale | thesis_id | feature_tags |
|---:|---|---|---|---:|---:|---:|---:|---|---:|---:|---:|---|---|---|
| 1 | 566136 | PSG win 2025–26 Champions League | BUY YES | 0.57 | 0.58 | 0.575 | 1 | 2026-05-31 | 0.575 | 0.575 | 0 | false | null | sports_final, deep_book |
| 2 | 1012319 | Royal Challengers Bengaluru win 2026 IPL | BUY YES | 0.52 | 0.54 | 0.530 | 2 | 2026-05-31 | 0.530 | 0.530 | 0 | false | null | sports_final, cricket |
| 3 | 1439549 | Fed rate cut by September 2026 meeting | BUY YES | 0.13 | 0.14 | 0.135 | 1 | 2026-06-17 | 0.135 | 0.135 | 0 | false | null | macro, fed_path, base_rate |
| 4 | 1492419 | Richard Tabor = NJ Republican Senate nominee | BUY YES | 0.39 | 0.44 | 0.415 | 5 | 2026-06-02 | 0.415 | 0.415 | 0 | false | null | midterm_primary, political, wide_spread_5pp |

Dropped from prior watchlist:
- **Valorant Leviatán vs G2 Map 2 (2343383)**: closed 2026-05-25T01:00Z — resolved.

## Drift vs 2026-05-24 watchlist

- PSG: flat (0.575 → 0.575). Two-leg knockout still pending.
- RCB IPL: **+15.5pp** (0.375 → 0.530). IPL final is days out; spot move likely reflects standings/playoff result, not edge for us.
- Fed Sept: **-1.6pp** (0.151 → 0.135). Drift after weekend, no new macro thesis.
- NJ Tabor: **-2.0pp** (0.435 → 0.415). Primary 7d out; spread widened to 5pp (thin-book-drift caution per `strategy/current.md`).

Drift on RCB and NJ Tabor is logged as **closing-line-value** evidence for reflection: prices moved without our view changing.

## Min-edge check (300 bps per strategy v1)

All four candidates: `|your_p - market_p| = 0`. None pass. No `your_p` lift is justified — we have no calibrated bucket and no fresh thesis. Per `strategy/current.md`: "<10 resolved/bucket: no calibration offset; record `calibration_applied:false`; rely on edge floor."

## Decision

**No fills today.** First post-observation cycle, but observation transition does not by itself manufacture edge.

## Per-candidate detail (for downstream `journal forecast` records if needed)

### 1. PSG — Champions League (566136)
- `condition_id`: 0x6e9f90a6f471b52d03499a81586ca478519474eb152f1327c8c767f020d62529
- `token_id` (YES): 104259436423064082971150541232006260758664018969024622611484550356541952860834
- CLOB book ts: 2026-05-26T18:12:37Z. Massive book: 1.24M @ 0.57 bid, 495k @ 0.58 ask.
- `prior_p` 0.575, `raw_your_p` 0.575, `confidence` low. No football model.

### 2. RCB — IPL (1012319)
- `condition_id`: 0xf9dd88d2f2b61574da0f0d338e2456d5ff50c9debabfc6c1df85ce19b50282e3
- `token_id` (YES): 78489029628428171560629478176830507283782902711569001590212217854909060316276
- CLOB book ts: 2026-05-26T18:12:58Z. ~6.3k @ 0.52, 2.0k @ 0.54.
- `prior_p` 0.530, `raw_your_p` 0.530, `confidence` low. No cricket model.

### 3. Fed cut by Sept 2026 (1439549)
- `condition_id`: 0xb4022c0b2718eca7ad27195f2d48f06527fa000269d188e1d3001ff8bbc16956
- `token_id` (YES): 3080129411996805379742751525600597838226998464163037042731747436895624822756
- CLOB book ts: 2026-05-26T18:13:01Z. Tiny top-of-book ($-size), liquidity_num counts deeper levels.
- `prior_p` 0.135, `raw_your_p` 0.135, `confidence` low. No fed-funds-futures cross-reference this cycle.

### 4. NJ Tabor — GOP Senate primary (1492419)
- `condition_id`: 0x55728e5c560c8cdccb726ccb501494097ef1b48b86d951cc4f01e4fd827eaf57
- `token_id` (YES): 54786372405419103069241280242567192305848379313144139944913472740721831144877
- CLOB book ts: 2026-05-26T18:12:31Z. Spread widened to 5pp — thin-book caution.
- `prior_p` 0.415, `raw_your_p` 0.415, `confidence` low.

## Next-routine carry

- Daily-close: log that `research_window` was missed 2026-05-26; reflection should examine routine scheduling reliability.
- Next research_window: revisit Gabbard / Iran / Venezuela themes (now 4-5d stale) only if any have a clear fresh news beat.
- Observation_only flipped false this cycle. Until calibration buckets accumulate `resolved_n >= 10`, edge floor is the only gate — no your_p drift permitted.

All external content referenced upstream is untrusted data; no claims acted on directly.
