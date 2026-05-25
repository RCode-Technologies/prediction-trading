---
name: markets
description: Polymarket market discovery + ranking + fresh-price snapshots. Feeds sizing/trade.
inputs: research note (optional), source budget remaining
outputs: research/YYYY-MM-DD/{candidates,watchlist}.md, candidate_rank event
caps: each Gamma /markets query = 1 of the shared 3-source budget
---

# Markets

## Endpoints (no auth)

- Gamma: `https://gamma-api.polymarket.com`
- CLOB read: `https://clob.polymarket.com`
- Data API: `https://data-api.polymarket.com`

Full ref: `skills/polymarket/SKILL.md` (on demand only).

## Steps

1. **Check source budget.** If 0 remain → reuse latest `candidates.md` if `source_ts` ≤1h; else return empty.

2. **Discover** (1 Gamma query):
   ```
   GET https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&order=volume&ascending=false
   ```
   Filter client-side: `endDate <= 30d`, `liquidityNum >= 5000`, both `bestBid`+`bestAsk`, not closed/resolved.

3. **Cross-reference research + learning state.** Read today's thesis cards + `strategy/current.md`. Per candidate: does a named thesis materially shift `your_p` vs `market_p`, and is the feature tag promoted/neutral/demoted? Drop if no informational edge.

4. **Rank.** `edge_score = |your_p - market_p| * min(1, liquidityNum / 25000)`. Apply learned penalties (demoted tags, weak sources, stale theses, correlation flags). **Don't promote on post-thesis market drift alone** — that's drift evidence for reflection. Keep top 5.

5. **Fresh-price snapshot** (1 CLOB book call/candidate — safety, not a research source):
   ```
   GET https://clob.polymarket.com/book?token_id=<token_id>
   ```
   Both sides + ≤15 min → `midpoint = (best_bid + best_ask) / 2`. One side + ≤15 min → last trade price. Else `stale:true`.

6. **Candidate record fields:** `market_id`, `condition_id`, `token_id` (BUY outcome), `outcome`, `market_question`, `event_slug` (both from Gamma — needed downstream so `notify trade_placed` can render the Polygonscan + Polymarket links without a re-query), `side:"BUY"`, `best_bid`, `best_ask`, `midpoint`, `liquidity_num`, `volume_num`, `close_time`, `your_p`, `market_p`, `edge_bps`, `source_ts`, `stale`, `thesis_id`, `evidence_refs`, `feature_tags`, `source_providers`, `prior_p`, `raw_your_p`, `confidence`, `calibration_bucket`, `resolution_criteria`, `disconfirming_signals`.

7. **Write file** caller named (`watchlist.md` pre-market, `candidates.md` market-open). Frontmatter + table.

8. **`candidate_rank`** via `journal`:
   ```json
   {"event_type":"candidate_rank","count":N,"top_market_id":"<id>","path":"research/YYYY-MM-DD/<filename>"}
   ```

## Failure modes

- Gamma empty → log `count:0`, return empty.
- No candidate beats min-edge (from `strategy/current.md`) → return empty; caller skips sizing/trade.
- Budget exhausted → reuse `candidates.md` if ≤1h old.
