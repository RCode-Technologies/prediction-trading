---
name: markets
description: Polymarket discovery + ranking + fresh-price snapshots. Universe-first; v2 attaches research signals to a stable universe rather than dropping markets that lack a thesis.
inputs: research notes (optional), source budget remaining, candidate count target
outputs: state/universe.jsonl (24h cache), research/YYYY-MM-DD/{candidates,watchlist}.md, candidate_rank event
caps: each Gamma /markets query = 1 of 3 shared source budget
---

# Markets

## Endpoints

- Gamma: `https://gamma-api.polymarket.com`
- CLOB read: `https://clob.polymarket.com`
- Data: `https://data-api.polymarket.com`

Full ref: `skills/polymarket/SKILL.md` (on demand).

## v2 design

Universe-first: build a stable liquid universe once/24h, then attach research overlays. Markets without thesis match are **kept** and become exploration probes (see `skills/sizing` explore path).

## Helpers

### `universe()` — daily liquid universe cache → `state/universe.jsonl`

```
GET /markets?active=true&closed=false&limit=500&order=volume&ascending=false
```

Filter: `endDate <= 90d`, `liquidityNum >= 2000`, two-sided book, not closed. JSONL row per surviving market: `market_id`, `condition_id`, `token_id_yes`, `token_id_no`, `market_question`, `event_slug`, `liquidity_num`, `volume_num`, `close_time`, `category`, `cached_at`.

Costs 1 Gamma source. Skip if `cached_at >= now - 24h`.

### `book(token_id)` — fresh CLOB snapshot

```
GET /book?token_id=<token_id>
```

Both sides + ≤15min → return `best_bid`, `best_ask`, `spread = best_ask - best_bid`, `executable_price` (= `best_ask` for a BUY, `best_bid` for a SELL), and `midpoint = (best_bid + best_ask)/2` (**reference only — never the trade price**). One side + ≤15min → last trade. Else `stale:true`. CLOB calls are NOT research sources.

**Cost-honest (v3):** you buy at the ask, sell at the bid. `executable_price`/`best_ask`/`best_bid` drive fills (`skills/trade`), marks (`skills/risk`), and `edge_net` (`strategy/current.md`); `midpoint` is for display + Kelly payout odds only.

### `attach_signals(universe, research_notes)`

For each market: look up matching thesis in today's `research/YYYY-MM-DD/*.md` by `market_ids` field or keyword vs `market_question`. Populate thesis fields or `null`. Carry the v3 gate fields from the matched thesis card forward: `resolution_criteria`, `resolution_parsed`, `reference_class`, `edge_source`, `source_providers`. No match → `thesis_id:null`, `reference_class:null`, `resolution_parsed:false`, `edge_source:"none"` (the candidate is explore-only; the binding gate is in `skills/sizing`).

### `rank(candidates, top_n=5)`

```
edge_score = |your_p - market_p| * min(1, liquidity_num / 25000)
exploit_eligible = (thesis_id != null) AND (|your_p - market_p| >= 0.03)
```

Sort: `exploit_eligible desc`, `edge_score desc`, `liquidity_num desc`. Apply learned penalties (demoted tags, weak sources, stale theses, correlation). Keep top_n.

**Do not drop** candidates without thesis match — slate carries them with `thesis_id:null`; `trade-window` step 6 assigns `learning_intent`.

## Steps (main `markets` invocation from a routine)

1. **Budget check.** 0 remain → load cached `state/universe.jsonl`; no Gamma calls.
2. **Universe freshness.** Missing or `cached_at < now - 24h` → run `universe()` (1 source). Else load cache.
3. **Attach signals.** Read today's research thesis cards. Match by `market_ids` or keyword. Populate or leave `null`.
4. **Fresh-price snapshot per candidate.** `book()` on each BUY-side `token_id`. Markets with stale books flagged `stale:true` but kept.
5. **Rank** via `rank()`.
6. **Candidate record fields:** `market_id`, `condition_id`, `token_id`, `outcome`, `market_question`, `event_slug`, `side:"BUY"`, `best_bid`, `best_ask`, `spread`, `executable_price` (= `best_ask` for BUY), `midpoint` (reference only), `liquidity_num`, `volume_num`, `close_time`, `your_p`, `market_p`, `edge_bps`, `source_ts`, `stale`, `thesis_id` (may be null), `evidence_refs`, `feature_tags`, `source_providers`, `prior_p`, `raw_your_p`, `confidence`, `calibration_bucket`, `resolution_criteria`, `resolution_parsed`, `reference_class` (may be null), `edge_source`, `disconfirming_signals`, `learning_intent` (left null; assigned by trade-window step 6). The gate fields (`resolution_parsed`, `reference_class`, `source_providers`) are carried for the binding `skills/sizing` edge gate.
7. **Write file** caller-named (`watchlist.md` pre-market, `candidates.md` market-open). Frontmatter + table.
8. **`candidate_rank`** via `journal`:
   ```json
   {"event_type":"candidate_rank","count":N,"top_market_id":"<id>","path":"...","exploit_eligible":<n>,"explore_eligible":<n>,"universe_size":<n>,"universe_cached_at":"<iso>"}
   ```

## Failure modes

- Gamma empty/errored → use stale cache, flag `degraded:true`. Else `count:0`.
- All candidates stale → still return — explore path tolerates stale; exploit rejects.
- Budget exhausted on non-universe call → reuse `candidates.md` if ≤1h old; else empty.
- No candidate beats min-edge → fine in v2; `trade-window` fills with explore probes.
