# 30 — Analyze Markets

**Trigger:** after `20-research.md`. Skipped if halts active.

**Reads:** Polymarket Gamma `/markets` and `/events`, Polymarket Data API,
today's `research/YYYY-MM-DD/<slug>.md`, `strategy/current.md`.

**Writes:** `research/YYYY-MM-DD/candidates.md`, `state/trade-log.jsonl`
(`candidate_rank` event).

## Steps

1. **Check remaining source budget** from `20-research.md`. Each Gamma `/markets`
   query consumes one of the 3 sources for the cycle. If 0 remain, you must
   work from research notes only and skip Gamma here.

2. **Query Gamma `/markets`** (one query — counts as a source):
   - `GET https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&order=volume&ascending=false`
   - Filter client-side for:
     - `endDate` within the next 30 days (near-resolution preferred)
     - `liquidityNum >= 5000`
     - both `bestBid` and `bestAsk` present
     - excludes already-closed or resolved markets

3. **Cross-reference research.** For each candidate, ask: does today's research
   note materially shift my probability vs the market's implied probability?
   Discard markets where you have no informational edge.

4. **Rank candidates.** Sort by `edge_score = |your_p - market_p| * liquidity_factor`
   where `liquidity_factor = min(1, liquidityNum / 25000)`. Keep top 5.

5. **Build candidate records.** Each must include:
   - `market_id`, `condition_id`, `token_id` (for the outcome you would buy),
     `outcome` label, `side` (always `BUY` in v1),
     `best_bid`, `best_ask`, `midpoint`, `liquidity_num`, `volume_num`,
     `close_time`, `your_p`, `market_p`, `edge_bps`, `source_ts`.

6. **Write `research/YYYY-MM-DD/candidates.md`** — markdown with frontmatter
   `cycle_id` and a table of the records above.

7. **Append `candidate_rank` event** to `state/trade-log.jsonl`:
   ```json
   {"schema_version":1,"event_id":"<cycle_id>-candidate_rank-1","cycle_id":"<cycle_id>","event_type":"candidate_rank","ts":"<now>","mode":"<network>","count":N,"top_market_id":"<id>","path":"research/YYYY-MM-DD/candidates.md"}
   ```

## Failure modes

- **Gamma returns empty list:** log the event, skip directly to
  `60-log-and-persist.md`. No trade this cycle.
- **No candidate beats your minimum edge** (a strategy-defined floor): skip to
  `60-log-and-persist.md`.
- **Source budget exhausted before Gamma call:** use the most recent prior
  `candidates.md` from `research/` only if its `source_ts` is within the last
  hour; otherwise skip trading.
