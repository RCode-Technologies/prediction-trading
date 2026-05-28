---
cycle_id: 20260528T181106Z-70f27403
phase: trade_window
ts: 2026-05-28T18:14:00Z
source_ts: 2026-05-28T18:13:00Z
strategy_version: v2
min_edge_bps: 300
universe_size: 34
universe_cached_at: 2026-05-28T18:13:18Z
sources_used_cycle: 1
---

# Candidates — 2026-05-28 (trade window)

Refresh of research-window watchlist (CLOB midpoints re-pulled). Universe cache rebuilt (was 30h stale). Held position 2354045 (US-Iran) mark moved sharply 0.155 → 0.30 in ~6h; thesis your_p=0.18 leaves -1200 bps long-buy edge (no add; v2 has no auto-SELL). Other thesis candidates (Fed-Sep, BTC-82k) remain negative-edge on long-BUY path. Zero exploit-eligible after the move. 3 explore probes fill the mandatory slate.

## Refreshed watchlist marks

| market_id | event_slug | question (truncated) | end | bid/ask | mid (fresh) | mid (research) | Δ mid | liq | thesis your_p | edge_bps | exploit_eligible |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|:---:|
| 2354045 | us-x-iran-diplomatic-meeting-by-329 | US x Iran diplomatic meeting by June 7? | 2026-06-07 | 0.28/0.32 | 0.300 | 0.155 | +0.145 | 25240 | 0.18 | -1200 | NO (exploit-forecasted earlier today; no add) |
| 1439549 | fed-rate-cut-by-629 | Fed rate cut by September? | 2026-06-17 | 0.133/0.141 | 0.137 | 0.127 | +0.010 | 18626 | 0.09 | -470 | NO |
| 2350172 | what-price-will-bitcoin-hit-may-25-31-2026 | Bitcoin reach $82,000 May 25-31? | 2026-06-01 | 0.006/0.011 | 0.0085 | 0.026 | -0.0175 | 22096 | 0.005 | -35 | NO |
| 907513 | wisconsin-governor-democratic-primary-winner | Francesca Hong WI Gov primary? | 2026-08-11 | 0.263/0.299 | 0.281 | 0.2745 | +0.007 | 7700 | null | 0 | NO (same-day probed) |
| 1975536 | which-company-has-the-best-ai-model-end-of-may | OpenAI best AI model May 2026? | 2026-05-31 | 0.004/0.008 | 0.006 | 0.0035 | +0.0025 | 93999 | null | 0 | NO (same-day probed) |
| 2356520 | wta-rakhimo-muchova-2026-05-27 | Roland Garros Rakhimova vs Muchova | 2026-06-03 | -/- | stale | 0.105 | n/a | 55024 | null | n/a | DROP (book empty; same-day probed) |
| 2298737 | will-anthropics-valuation-hit-by-june-30 | Anthropic valuation hit $1.5T by June 30? | 2026-07-01 | 0.07/0.08 | 0.075 | 0.075 | 0 | 10758 | null | 0 | NO (chosen for new probe) |

## Slate composition (trade-window forecasts)

0 exploit fills + 3 explore probes per `strategy/current.md` slot table.

| slot | market_id | path | rank ε | learning_intent | your_p | market_p | notional | rationale |
|---:|---|---|---:|---|---:|---:|---:|---|
| 1 | 2298737 | explore-probe | +0.05 | explore | 0.125 | 0.075 | 0 (probe pinned) | Carried explore-eligible from research-window watchlist; not probed today. Calibration on 10-20 bucket. |
| 2 | 2350172 | explore-probe | 0 | explore | 0.02 (clamped from 0.0085) | 0.0085 | 0 (probe pinned) | Carried BTC-82k thesis market, ε=0 trust-market baseline but clamp to 0.02 floor; 0-10 bucket. |
| 3 | 1439549 | explore-probe | -0.05 | explore | 0.087 | 0.137 | 0 (probe pinned) | Carried Fed-Sep thesis market, ε=-0.05; 0-10 bucket. Probe lands very close to research thesis (0.09). |

## Notes for downstream phases

- **US-Iran mark surge.** YES mid moved 0.155 → 0.225 → 0.30 between 12:00Z research, 16:09Z heartbeat, and 18:13Z trade-window pull. Held position notional value: 303.92 → 405.22. Cost basis 0.373 → unrealized loss now -$98 vs -$200 earlier. Without fresh research budget spent, cannot revise thesis upward; v2 disallows auto-SELL. Flag for `reflect` (daily-close) to evaluate whether news-event tag warrants prior-down-revision discipline rules.
- **Universe refresh.** Prior cache was 30h stale; rebuilt at 18:13Z (top-100 by volume on Gamma). 34 markets survive filter (vs prior 38). None of the prior watchlist markets remain in the top-100 by volume — they have liquidity but lower current volume than today's short-window markets. Acceptable for v2; trade-window slate uses carried watchlist + fresh marks.
- **Probe spread.** 3 categories: tech-valuation (Anthropic), crypto-price (BTC), macro-rate (Fed). No correlation cluster.
- **Source budget**: 1/3 used (universe refresh). 2 remaining held in reserve.
- **Correlation check.** Same-cycle probes touch tech / crypto / macro — three distinct event classes. Held position (geopolitics) is independent. 5% NAV bucket limits unaffected (probes = 0 notional).

## Resolution / source provenance

- Gamma /markets refresh (1 source). 100 returned (limit cap at 100 despite request).
- Fresh CLOB books pulled for prior 7 watchlist markets (NOT research sources).
- Carried thesis cards from `research/2026-05-28/macro-and-iran-update.md` and prior watchlist.
