---
cycle_id: 20260528T120548Z-7357b6af
phase: research_window
ts: 2026-05-28T12:09:30Z
source_ts: 2026-05-27T12:08:30Z
research_overlap: 3/5 (US-Iran T2 + BTC-82k T1 + carried Fed-Sep T1 attach to slate)
strategy_version: v2
min_edge_bps: 300
candidates_passing_min_edge: 0 (US-Iran 2.5pp, Bitcoin 2.1pp, Fed -3.7pp on YES no NO-leg path)
universe_size: 38
universe_cached_at: 2026-05-27T12:08:30Z
sources_used_cycle: 2
---

# Watchlist — 2026-05-28 (research window)

Universe-first v2. 38-market universe cache reused (23h57m old; under 24h gate). Three theses overlap top candidates: US-Iran revised down, BTC tail (new), Fed Sep cut carried. Zero candidates clear the 300 bps exploit-fill floor on a long-BUY path → slate is forecast-only on theses + 3 explore probes.

## Top 7 ranked candidates

| rank | market_id | event_slug | question (truncated) | end | bid/ask | mid | liq_num | your_p | market_p | edge_bps | edge_score | thesis_id | feature_tags | exploit_eligible |
|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|:---:|
| 1 | 2354045 | us-x-iran-diplomatic-meeting-by-329 | US x Iran diplomatic meeting by June 7? | 2026-06-07 | 0.15/0.16 | 0.155 | 25240 | 0.18 | 0.155 | +250 | 0.0250 | 20260528-us-iran-mtg-T2 | geopolitics,base-rate-anchored-research,news_event,thesis_revision | NO (below 300bps) |
| 2 | 1439549 | fed-rate-cut-by-629 | Fed rate cut by September 2026 meeting? | 2026-06-17 | 0.123/0.131 | 0.127 | 18626 | 0.09 | 0.127 | -370 | 0.0276 | 20260527-fed-sep-cut-T1 | macro,base-rate-anchored-research,fed | YES (forecast-only; market overpriced, no NO-leg path) |
| 3 | 2350172 | bitcoin-reach-82000-may-25-31 | Bitcoin reach $82,000 May 25–31? | 2026-06-01 | 0.024/0.028 | 0.026 | 22096 | 0.005 | 0.026 | -210 | 0.0186 | 20260528-btc-82k-may31-T1 | crypto,price-target,short-window | NO (below 300bps and negative) |
| 4 | 907513 | wisconsin-governor-democratic-primary-winner | Francesca Hong WI Gov Dem primary? | 2026-08-11 | 0.262/0.287 | 0.2745 | 7700 | null | 0.2745 | 0 | 0 | null | politics,primary,explore-candidate | NO |
| 5 | 1975536 | which-company-has-the-best-ai-model-end-of-may | OpenAI best AI model end of May 2026? | 2026-05-31 | 0.003/0.004 | 0.0035 | 93999 | null | 0.0035 | 0 | 0 | null | tech,ai,short-window,explore-candidate | NO |
| 6 | 2356520 | wta-rakhimo-muchova-2026-05-27 | Roland Garros WTA: Rakhimova vs Muchova | 2026-06-03 | 0.10/0.11 | 0.105 | 55024 | null | 0.105 | 0 | 0 | null | sports,tennis,explore-candidate | NO |
| 7 | 2298737 | will-anthropics-valuation-hit-by-june-30 | Anthropic valuation hit $1.5T by June 30? | 2026-07-01 | 0.07/0.08 | 0.075 | 10758 | null | 0.075 | 0 | 0 | null | tech,valuation,explore-candidate | NO |

## Slate composition (research-window forecasts)

0 exploit fills + 3 explore probes per `strategy/current.md` slot table (exploit_eligible=0 path). Plus 1 thesis-driven tracking forecast for the held position (US-Iran).

| slot | market_id | path | rank ε | learning_intent | your_p | market_p | notional | rationale |
|---:|---|---|---:|---|---:|---:|---:|---|
| extra | 2354045 | exploit (forecast-only) | n/a | exploit | 0.18 | 0.155 | 0 (edge 2.5pp < 300 bps floor; sizing/decision skipped per `Min edge (exploit fills): 300 bps`) | Re-emit revised thesis on held position; feeds calibration on exploit slice + tracks held-position view. No add to position. |
| 1 | 907513 | explore-probe | +0.05 | explore | 0.3245 | 0.2745 | 0 (probe pinned) | Mid-tail political primary (close 2026-08-11). ε=+0.05 lands `your_p` in defined explore bucket 30-40, populating sliced calibration ledger. |
| 2 | 1975536 | explore-probe | 0 | explore | 0.0035 | 0.0035 | 0 (probe pinned) | Top-volume liquid universe market with no thesis match; deep-tail YES, ε=0 trust-market baseline at near-zero (calibration on low-prob slice). |
| 3 | 2356520 | explore-probe | -0.05 | explore | 0.055 | 0.105 | 0 (probe pinned) | Sports market (close 2026-06-03); ε=-0.05 with clamp protecting above 0.02 floor. Diversifies from same-day macro/political theses. |

## Slate composition (top-line)

- **Forecasts to emit this cycle: 4** (1 thesis-driven extra + 3 mandatory probes).
- **0 fills.** Held position retained; no adds (edge below floor); no SELL path under v2.

## Notes for downstream phases

- **US-Iran thesis revised.** Yesterday's `raw_your_p=0.45` was disconfirmed by 5th-round (Rome) stall + market re-pricing from 0.375 → 0.155. New estimate 0.18 leaves only 2.5pp edge; insufficient for an add. Hold position; do not auto-SELL (v2 design). Reflection should evaluate at resolution whether the news-event tag warrants demotion.
- **Fed Sep cut not re-emitted** (still in effect, close June 17, no new evidence vs yesterday). Carried as exploit-eligible-but-forecast-only.
- **BTC $82k thesis fresh.** Spot $73,276 at 11:40Z; +12% in 3 days against bear macro is a hard tail. No NO-leg buy path; forecast-only and would not exceed 300 bps anyway.
- **Probes spread across categories** (tech-AI, tennis, tech-valuation). No two probes cluster on the same event class.
- **Correlation check.** US-Iran (geopolitics) does NOT correlate with Fed-Sep cut (macro) for portfolio-bucket purposes; energy-driven inflation is an indirect link, not a same-resolution-event link. BTC and US-Iran share Iran-shock direction but resolve via different criteria. Slate within 5% NAV bucket limits.
- **Source budget**: 2/3 used (Iran + BTC searches). Trade-window has fresh 3-source budget at 18:00 UTC.

## Resolution / source provenance

- Universe cache reused (cached at 2026-05-27T12:08:30Z, 0 Gamma calls this cycle).
- Native WebSearch "US Iran diplomatic meeting nuclear talks May 2026" (1 source).
- Native WebSearch "Bitcoin price today USD May 28 2026" (1 source).
- Fresh CLOB book pulled for held position 2354045 (token_id YES) — NOT a research source.
- Thesis cards in `research/2026-05-28/macro-and-iran-update.md`.
