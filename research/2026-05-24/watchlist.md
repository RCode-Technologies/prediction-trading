---
cycle_id: 20260524T220555Z-a6554a6a
phase: research_window
ts: 2026-05-24T22:14:00Z
source_ts: 2026-05-24T22:13:30Z
gamma_query: "active=true&closed=false&limit=100&order=volume&ascending=false"
filter: "endDate<=30d, liquidityNum>=5000, two-sided book"
candidates_after_filter: 15
sources_used_this_routine: 3
budget_remaining_after: 0
research_overlap: none — Gabbard/Iran/Machado theses did not surface in top-100-by-volume markets within 30d end-date filter
mode: paper (observation_only=true)
---

# Watchlist — 2026-05-24

## Coverage gap

Today's `overnight-shifts` research surfaced three theses (Gabbard DNI resignation, Trump Iran "no rush", Machado Venezuela return). **None of them map to markets in today's top-volume Gamma slice within the 30d end-date filter.** Source budget for this routine is now exhausted (1 Brave + 1 WebFetch + 1 Gamma = 3/3); a targeted "Gabbard" / "DNI" / "Venezuela election" Gamma search must wait for the next routine. Logged this gap explicitly so trade-window can decide whether to spend its budget chasing these.

## Top 5 (liquidity-ranked, observation-phase forecasts only)

| rank | market_id | question | side | best_bid | best_ask | midpoint | liq_num | vol_num | close | your_p | market_p | edge_bps | stale | thesis_id | feature_tags |
|---:|---|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---|---|---|
| 1 | 566136 | PSG win 2025–26 Champions League | BUY YES | 0.57 | 0.58 | 0.575 | 827219 | 9878809 | 2026-05-31 | 0.575 | 0.575 | 0 | false | null | sports_final, deep_book |
| 2 | 2343383 | Valorant: Leviatán vs G2 — Map 2 winner (Leviatán) | BUY YES | 0.39 | 0.44 | 0.415 | 36128 | 9932 | 2026-05-25T01:00Z | 0.415 | 0.415 | 0 | false | null | esports, thin_book_drift, wide_spread_5pp |
| 3 | 1012319 | Royal Challengers Bengaluru win 2026 IPL | BUY YES | 0.37 | 0.38 | 0.375 | 18201 | 98812 | 2026-05-31 | 0.375 | 0.375 | 0 | false | null | sports_final, cricket |
| 4 | 1439549 | Fed rate cut by September 2026 meeting | BUY YES | 0.143 | 0.159 | 0.151 | 17184 | 99261 | 2026-06-17 | 0.151 | 0.151 | 0 | false | null | macro, fed_path, base_rate |
| 5 | 1492419 | Richard Tabor = NJ Republican Senate nominee | BUY YES | 0.43 | 0.44 | 0.435 | 5760 | 9942 | 2026-06-02 | 0.435 | 0.435 | 0 | false | null | midterm_primary, political |

`your_p` = `market_p` for every row because no research thesis from this routine materially shifts any of them and observation-phase strategy says "rely on edge floor" when calibration buckets have `resolved_n < 10`. Edge floor is 300 bps per `strategy/current.md`; all five rows are 0 bps. **No candidate passes min-edge → no fills today even after observation window ends.**

## Per-candidate detail

### 1. PSG — Champions League (566136)
- `condition_id`: 0x6e9f90a6f471b52d03499a81586ca478519474eb152f1327c8c767f020d62529
- `token_id` (YES): 104259436423064082971150541232006260758664018969024622611484550356541952860834
- CLOB book ts: 2026-05-24T22:10:00Z, best_bid 0.57 (size 522k), best_ask 0.58 (size 862k). Deepest book in the universe.
- Final on/before 2026-05-31. Two-leg knockout — single-game outcome. No proprietary football model on hand; 0 edge.
- `prior_p` 0.575, `raw_your_p` 0.575, `confidence` low.
- `resolution_criteria`: PSG hoist the trophy in the 2025–26 UCL final (per Polymarket market description, to be cross-checked at trade time).
- `disconfirming_signals`: late-week injury news on key PSG player; opposing-side momentum from semis.

### 2. Valorant — Leviatán vs G2 Map 2 (2343383)
- `condition_id`: 0x2689999091fda61a6efe42d4646b9199ca485a578afba3c30c9296c3893d11ff
- `token_id` (Leviatán): 13862527119781720335658555469197872973969182208760780924816101348645923630577
- CLOB book ts: 2026-05-24T22:10:22Z, best_bid 0.39 (size 839), best_ask 0.44 (size 308). **5pp spread** = ~10% effective edge tax round-trip. Hypothesis registry already flags `thin-book-drift` as `caution`.
- Demoted by spread alone; included on watchlist for monitoring, not for sizing.

### 3. RCB — IPL 2026 (1012319)
- `condition_id`: 0xf9dd88d2f2b61574da0f0d338e2456d5ff50c9debabfc6c1df85ce19b50282e3
- `token_id` (YES): 78489029628428171560629478176830507283782902711569001590212217854909060316276
- CLOB book ts: 2026-05-24T22:09:59Z, best_bid 0.37 (size 4378), best_ask 0.38 (size 178). Tight 1pp spread.
- Cricket — no model. 0 edge.

### 4. Fed cut by Sept 2026 meeting (1439549)
- `condition_id`: 0xb4022c0b2718eca7ad27195f2d48f06527fa000269d188e1d3001ff8bbc16956
- `token_id` (YES): 3080129411996805379742751525600597838226998464163037042731747436895624822756
- CLOB book ts: 2026-05-24T22:10:22Z, best_bid 0.143 (size 5), best_ask 0.159 (size 13.45). **Books are tiny in $-terms** (~$2 of size on each side); liq_num counts deeper book away from top.
- Macro market — needs Fed-funds-futures cross-reference before any thesis. No research this routine. 0 edge.

### 5. NJ Senate GOP nominee — Tabor (1492419)
- `condition_id`: 0x55728e5c560c8cdccb726ccb501494097ef1b48b86d951cc4f01e4fd827eaf57
- `token_id` (YES): 54786372405419103069241280242567192305848379313144139944913472740721831144877
- CLOB book ts: 2026-05-24T22:10:12Z, best_bid 0.43 (size 372), best_ask 0.44 (size 198). Primary 9 days out.
- Closest to our research bucket (AP overnight: "Dems poised to finish several seats behind Republicans in 2026"). But no NJ-specific polling pulled this routine. 0 actionable edge.

## Candidates considered and dropped

- BTC>$70k by 5/25 (mid 0.997), ETH<$1800 by 5/24 (mid 0.0015), Hyperliquid<$24 May (mid 0.0015), Roland Garros completed match (mid 0.9995): degenerate / resolved-in-all-but-name; no edge possible.
- Various tennis handicap markets (Popyrin, Cilic): all `thin-book-drift` caution; preferred NJ Senate for the 5th slot for feature-tag diversity even though raw liquidity is lower.
- KOR LCK CL game handicap (8627 liq): same caution as Valorant.
- Elon tweet count 65-89 May 25-27 (8121 liq): novelty market, no model.

## Next-routine carry

- Trade-window: if budget permits, run targeted Gamma queries for "Gabbard" / "Tulsi" / "Director of National Intelligence" / "Venezuela election" / "Iran nuclear deal" — these are the actionable themes from research that weren't captured by the volume-ranked top-100.
- Daily-close: log that the research↔markets coverage gap happened today; reflection may want to flag the routine ordering (research before markets discovery) as a process risk when the research angle is news-driven and the news doesn't touch top-volume markets.
