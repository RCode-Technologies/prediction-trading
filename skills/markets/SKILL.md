---
name: markets
description: Polymarket market discovery + ranking + fresh-price snapshots. Universe-first; v2 attaches research signals to a stable universe rather than dropping markets that lack a thesis.
inputs: research notes (optional), source budget remaining, candidate count target
outputs: state/universe.jsonl (cached 24h), research/YYYY-MM-DD/{candidates,watchlist}.md, candidate_rank event
caps: each Gamma /markets query = 1 of the shared 3-source budget
---

# Markets

## Endpoints (no auth)

- Gamma: `https://gamma-api.polymarket.com`
- CLOB read: `https://clob.polymarket.com`
- Data API: `https://data-api.polymarket.com`

Full ref: `skills/polymarket/SKILL.md` (on demand only).

## v2 design

Discovery is **universe-first**: build a stable liquid universe once/24h, then attach research-derived `your_p` overlays. Markets without an attached thesis are NOT dropped — they become exploration probes downstream (see `skills/sizing` explore path). This is the structural fix for the v1 failure mode where research surfaced theses that didn't intersect with the top-volume slice.

## Helpers

### `universe()` — daily liquid universe cache

Refreshed at most once/24h. Persists to `state/universe.jsonl`. Caller checks staleness before invoking.

```
GET https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=500&order=volume&ascending=false
```

Filter client-side (v2, relaxed): `endDate <= 90d`, `liquidityNum >= 2000`, both `bestBid`+`bestAsk`, not closed/resolved. Append each surviving market as a JSONL row with: `market_id`, `condition_id`, `token_id_yes`, `token_id_no`, `market_question`, `event_slug`, `liquidity_num`, `volume_num`, `close_time`, `category` (election/sports/macro/crypto/other inferred from market metadata), `cached_at`.

Costs 1 Gamma source. If `state/universe.jsonl` exists with `cached_at >= now - 24h`, skip the call.

### `book(token_id)` — fresh CLOB snapshot

```
GET https://clob.polymarket.com/book?token_id=<token_id>
```

Both sides + ≤15 min → `midpoint = (best_bid + best_ask) / 2`. One side + ≤15 min → last trade price. Else `stale:true`. CLOB calls are NOT research sources (they're safety).

### `attach_signals(universe, research_notes)` — fold theses into universe

For each market in the universe, look up any matching thesis in today's `research/YYYY-MM-DD/*.md` notes by `market_ids` field or by keyword match against `market_question`. Output a candidate record with thesis fields populated (or `null` if no match).

### `rank(candidates, top_n)` — ordered slate

```
edge_score = |your_p - market_p| * min(1, liquidity_num / 25000)
exploit_eligible = (thesis_id != null) and (|your_p - market_p| >= 0.03)
```

Sort by: `exploit_eligible desc`, then `edge_score desc`, then `liquidity_num desc`. Apply learned penalties (demoted tags, weak sources, stale theses, correlation flags). Keep top `top_n` (default 5).

**Crucially:** do NOT drop candidates without thesis match. The slate carries them through with `thesis_id:null`; `routines/trade-window` step 6 assigns `learning_intent` per slot.

## Steps (for the main `markets` invocation called from a routine)

1. **Check source budget.** 0 remain → fall back to whatever cached `state/universe.jsonl` exists; no Gamma calls.

2. **Universe freshness.** If `state/universe.jsonl` missing OR `cached_at < now - 24h` → run `universe()` (costs 1 Gamma source). Else load from cache.

3. **Attach signals.** Read today's `research/YYYY-MM-DD/*.md` thesis cards. Match against universe by `market_ids` or question-keyword. Populate `thesis_id`, `evidence_refs`, `feature_tags`, `source_providers`, `prior_p`, `raw_your_p`, `disconfirming_signals` per candidate. Unmatched candidates keep these fields as `null`.

4. **Fresh-price snapshot per candidate.** Use `book()` on each candidate's BUY-side `token_id`. CLOB calls don't count toward research budget. Markets with stale books are flagged `stale:true` but kept (sizing/recalibrate handle staleness).

5. **Rank.** Use `rank(candidates, top_n=5)`. Returns slate with both exploit-eligible and exploration-fallback candidates.

6. **Candidate record fields** (per row):
   `market_id`, `condition_id`, `token_id` (BUY outcome), `outcome`, `market_question`, `event_slug`, `side:"BUY"`, `best_bid`, `best_ask`, `midpoint`, `liquidity_num`, `volume_num`, `close_time`, `your_p`, `market_p`, `edge_bps`, `source_ts`, `stale`, `thesis_id` (may be null), `evidence_refs`, `feature_tags`, `source_providers`, `prior_p`, `raw_your_p`, `confidence`, `calibration_bucket`, `resolution_criteria`, `disconfirming_signals`, `learning_intent` (left null by markets; assigned by `trade-window` step 6).

7. **Write file** caller-named (`watchlist.md` pre-market, `candidates.md` market-open). Frontmatter + table including a `thesis?` and `learning_intent` column (or "tbd" if unassigned).

8. **`candidate_rank`** via `journal`:
   ```json
   {"event_type":"candidate_rank","count":N,"top_market_id":"<id>","path":"research/YYYY-MM-DD/<filename>","exploit_eligible":<n>,"explore_eligible":<n>,"universe_size":<n>,"universe_cached_at":"<iso>"}
   ```

## Failure modes

- Gamma empty / errored → use stale cache if any, flag `degraded:true`; if neither, log `count:0`, return empty.
- All candidates flagged stale → still return them — sizing's explore path tolerates stale marks; exploit path rejects.
- Budget exhausted on a non-universe call → reuse latest `candidates.md` if ≤1h old; else empty.
- **No candidate beats min-edge:** acceptable in v2 — trade-window fills the slate with exploration probes from the universe.
