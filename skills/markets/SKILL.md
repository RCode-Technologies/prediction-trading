---
name: markets
description: Discover, rank, and snapshot Polymarket candidate markets from Gamma + CLOB. Produces a candidate watchlist with fresh prices; feeds sizing and trade skills.
inputs: research note (optional), source budget remaining
outputs: research/YYYY-MM-DD/candidates.md or watchlist.md, candidate_rank event
caps: each Gamma /markets query consumes one of the shared 3-source budget (ADR 0006)
---

# Markets

Polymarket market discovery + candidate ranking + fresh-price snapshots.

## Endpoints (no auth required)

- Gamma: `https://gamma-api.polymarket.com`
- CLOB read: `https://clob.polymarket.com`
- Data API: `https://data-api.polymarket.com`

See `skills/polymarket/SKILL.md` for full reference (load on demand only).

## Steps

1. **Check remaining source budget** from the calling routine. Each
   `/markets` query is one source. If 0 remain, skip discovery and reuse
   the most recent `candidates.md` if its `source_ts` is within the last
   hour; otherwise return an empty watchlist.

2. **Discover candidates** (one Gamma query):

   ```
   GET https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&order=volume&ascending=false
   ```

   Filter client-side:
   - `endDate` within next 30 days (near-resolution)
   - `liquidityNum >= 5000`
   - both `bestBid` and `bestAsk` present
   - exclude already-closed/resolved markets

3. **Cross-reference research and learning state.** Read today's thesis cards
   plus the active learning state in `strategy/current.md`. For each
   candidate, ask: does a named thesis materially shift `your_p` vs
   market-implied `market_p`, and is this feature tag currently promoted,
   neutral, or demoted by prior evidence? Drop candidates with no
   informational edge.

4. **Rank** by
   `edge_score = |your_p - market_p| * min(1, liquidityNum / 25000)`.
   Apply learned penalties from `strategy/current.md` for demoted feature
   tags, weak source classes, stale theses, and correlation flags. Do not
   promote a candidate solely because the market moved after the thesis was
   written; that is drift evidence for reflection, not a fresh edge by itself.
   Keep top 5.

5. **Fresh-price snapshot per candidate** (optional, one CLOB book call per
   candidate — these do not count as research sources because they are safety
   freshness checks):

   ```
   GET https://clob.polymarket.com/book?token_id=<token_id>
   ```

   Compute `midpoint = (best_bid + best_ask) / 2` if both sides exist and the
   book timestamp is ≤15 min old. If only one side and ≤15 min, use last trade
   price. Else mark `stale: true`.

6. **Build candidate records**, each with:
   `market_id`, `condition_id`, `token_id` (for the outcome you'd BUY),
   `outcome`, `side: "BUY"`, `best_bid`, `best_ask`, `midpoint`,
   `liquidity_num`, `volume_num`, `close_time`, `your_p`, `market_p`,
   `edge_bps`, `source_ts`, `stale`, `thesis_id`, `evidence_refs`,
   `feature_tags`, `source_providers`, `prior_p`, `raw_your_p`, `confidence`,
   `calibration_bucket`, `resolution_criteria`, `disconfirming_signals`.

7. **Write the file** the caller named (`watchlist.md` for pre-market,
   `candidates.md` for market-open). Markdown frontmatter + table.

8. **Emit `candidate_rank`** via the `journal` skill:
   ```json
   {"event_type":"candidate_rank","count":N,"top_market_id":"<id>","path":"research/YYYY-MM-DD/<filename>"}
   ```

## Outputs to caller

`{candidates: [...], path, sources_used}`.

## Failure modes

- **Gamma empty list:** log event with `count:0`, return empty.
- **No candidate beats minimum edge** (from `strategy/current.md`): return
  empty; caller skips sizing/trade.
- **Source budget exhausted:** reuse stale `candidates.md` only if ≤1h old.
