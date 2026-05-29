---
cycle_id: 20260527T120743Z-62cd07c7
phase: research_window
ts: 2026-05-27T12:18:00Z
source_ts: 2026-05-27T12:08:30Z
research_overlap: 2/5 (US-Iran + Fed-Sep theses match top-2)
strategy_version: v2
min_edge_bps: 300
candidates_passing_min_edge: 2
universe_size: 38
universe_cached_at: 2026-05-27T12:08:30Z
sources_used_cycle: 3
---

# Watchlist — 2026-05-27 (research window)

Universe-first v2: 38 markets satisfied `liquidityNum >= 2000`, `endDate <= 2026-08-25`, two-sided book, orderbook enabled. Two surfaced research theses (US-Iran meeting, Fed Sep cut) attach to the slate. Three explore-probe-eligible top candidates listed for slate slot allocation per `strategy/current.md § Exploration probe policy`.

## Top 5 ranked candidates

| rank | market_id | event_slug | question (truncated) | end | bid/ask | mid | liq_num | your_p | market_p | edge_bps | edge_score | thesis_id | feature_tags | exploit_eligible |
|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|:---:|
| 1 | 2354045 | us-x-iran-diplomatic-meeting-by-june-7-2026 | US x Iran diplomatic meeting by June 7? | 2026-06-07 | 0.37/0.38 | 0.375 | 25240 | 0.45 | 0.375 | +750 | 0.0750 | 20260527-us-iran-mtg-T1 | geopolitics,base-rate-anchored-research,news_event | YES |
| 2 | 1439549 | fed-rate-cut-by-629 | Fed rate cut by September 2026 meeting? | 2026-06-17 | 0.123/0.131 | 0.127 | 18626 | 0.09 | 0.127 | -370 | 0.0276 | 20260527-fed-sep-cut-T1 | macro,base-rate-anchored-research,fed | YES (forecast-only; market overpriced) |
| 3 | 907513 | wisconsin-governor-democratic-primary-winner | Francesca Hong wins WI Gov Dem primary? | 2026-08-11 | 0.262/0.287 | 0.2745 | 7700 | null | 0.2745 | 0 | 0 | null | politics,primary,explore-candidate | NO |
| 4 | 2298737 | will-anthropics-valuation-hit-by-june-30 | Anthropic valuation hit $1.5T by June 30? | 2026-07-01 | 0.07/0.08 | 0.075 | 10758 | null | 0.075 | 0 | 0 | null | tech,valuation,explore-candidate | NO |
| 5 | 1107307 | us-strike-on-colombia-by-january-31 | US strike on Colombia by December 31? (endDate 2026-01-31 — Polymarket-tagged active despite past end) | 2026-01-31 | 0.18/0.19 | 0.185 | 12298 | null | 0.185 | 0 | 0 | null | geopolitics,explore-candidate | NO |

## Slate composition (research-window forecasts)

Two exploit_eligible → 2 exploit forecasts + 1 explore probe (per `strategy/current.md` slot table for exploit_eligible=2).

| slot | market_id | path | rank ε | learning_intent | your_p | market_p | notional | rationale |
|---:|---|---|---:|---|---:|---:|---:|---|
| 1 | 2354045 | exploit | n/a | exploit | 0.45 | 0.375 | ≤2.7 USDC (5% NAV cap), Kelly = 0.12, fractional Kelly target ≈ 1.62 USDC | Trump "deal largely negotiated"; Iran FM "inches away"; window narrow but signal strong |
| 2 | 1439549 | exploit | n/a | exploit | 0.09 | 0.127 | 0 (Kelly negative, forecast-only) | FedWatch hold-through-year; CPI 3.8%; energy shock; ~70% no-change Dec |
| 3 | 907513 | explore-probe | -0.05 | explore | 0.2245 | 0.2745 | 0 (probe pinned) | Mid-range no-thesis market with future close (2026-08-11); ε=-0.05 (rank-3 by slot). Anthropic-1.5T saturates near 0.02 clamp; Colombia endDate already past — rejected as probe targets. |

## Notes for downstream phases

- **Research overlap improved vs 2026-05-26.** Yesterday's watchlist had 0 thesis-bearing candidates; today's universe surfaces 2 thesis-aligned markets (US-Iran by direct news match, Fed Sep cut by macro re-pricing). v2 universe-first design is now producing exploit candidates.
- **US-Iran caveat.** Resolution criteria uncertain — assumed broad ("any senior-level direct contact"). If criteria require named-principal in-person meeting (e.g., Secretary of State ↔ FM), agent should mark down ~0.05 before next cycle when more information surfaces. Disconfirming signal: announcement-via-intermediaries-only.
- **Fed forecast-only.** No NO-leg buy path; forecast feeds calibration bucket 0-10 / 10-20 only. Reflect should evaluate whether the macro-base-rate thesis-tag beats market_p Brier when this resolves at the June 17 next-FOMC mark (market end date).
- **Explore probe choice (907513 WI Gov Dem primary — Hong).** Picked because midpoint 0.2745 is comfortably away from the clamps and the market has a clean future close (2026-08-11). Anthropic-1.5T saturates near 0.02 clamp under ε=-0.05; Colombia-strike's Gamma endDate of 2026-01-31 is already past (Polymarket-flagged active but resolution risk uncertain). ε-probe carries more signal when neither saturated nor in a stale-resolution window.
- **Source budget**: 3/3 (1 Gamma `/markets` + 2 native WebSearch). Trade-window has fresh 3-source budget at 18:00 UTC and may re-research US-Iran headlines, especially if the deal-announcement timing changes.
- **No correlation cluster** within slate: geopolitics (Iran), macro (Fed), geopolitics-different-region (Colombia). 5% NAV bucket safe.

## Resolution / source provenance

- Gamma `/markets?active=true&closed=false&limit=500&order=volume&ascending=false` at 2026-05-27T12:08:30Z (1 source).
- Native WebSearch "US Iran diplomatic meeting talks scheduled June 2026 nuclear" (1 source).
- Native WebSearch "Federal Reserve September 2026 FOMC rate cut probability CME FedWatch" (1 source).
- Thesis cards in `research/2026-05-27/{us-iran-meeting-by-jun7,fed-cut-by-september}.md`.
