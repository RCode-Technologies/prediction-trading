---
cycle_id: 20260527T181042Z-83063414
phase: trade_window
ts: 2026-05-27T18:11:30Z
source_ts: 2026-05-27T18:11:00Z
strategy_version: v2
min_edge_bps: 300
universe_size: 38
universe_cached_at: 2026-05-27T12:08:30Z
sources_used_cycle: 0
research_overlap: research_window theses still active (US-Iran exploit, Fed-Sep forecast-only)
---

# Candidates — 2026-05-27 trade window

Watchlist from research/2026-05-27/watchlist.md (12:18 UTC) refreshed with fresh CLOB midpoints at 18:11 UTC. Universe still fresh (cached 12:08 UTC). No new Gamma/WebSearch calls this cycle.

## Fresh marks vs research_window

| market_id | slug | research mid (12:08) | fresh mid (18:11) | Δ | book | status |
|---|---|---:|---:|---:|---|---|
| 2354045 | us-x-iran-diplomatic-meeting | 0.375 | 0.37 | -0.005 | 0.36/0.38 | live, 2-sided |
| 1439549 | fed-rate-cut-by-629 | 0.127 | 0.127 | 0 | 0.123/0.131 | live, 2-sided |
| 907513 | wi-gov-dem-primary | 0.2745 | 0.276 | +0.0015 | 0.263/0.289 | live, 2-sided |
| 2298737 | anthropic-1.5T | 0.075 | 0.075 | 0 | 0.07/0.08 | live, 2-sided |
| 1107307 | us-strike-on-colombia | 0.185 | n/a | n/a | endDate 2026-01-31 (past) | rejected |

## Dedupe state (today's forecasts)

- 2354045 US-Iran: exploit forecast emitted at 12:20 (research_window). Same-day exploit re-emission allowed (within-cycle dedupe only).
- 1439549 Fed Sep: forecast-only emitted at 12:20. Edge_bps -370 (negative), fails ≥300 threshold for exploit slot.
- 907513 WI Gov: explore-rank3 emitted at 12:21. Same-day probe dedupe blocks re-probing.

## Slate (3 mandatory forecasts)

`exploit_eligible = 1` (just Iran). Per `strategy/current.md` § Exploration probe policy slot table → 1 exploit + 2 explore probes.

| slot | path | rank/ε | market_id | event_slug | your_p | market_p | edge_bps | bucket | rationale |
|---:|---|---:|---|---|---:|---:|---:|---|---|
| 1 | exploit | n/a | 2354045 | us-x-iran-diplomatic-meeting-by-329 | 0.45 | 0.37 | +800 | 40-50 | Thesis from research_window (Trump "deal largely negotiated"; FM "inches away"); mid drifted -0.005 in 6h, edge slightly wider. Sizing will compute add to existing 740 shares. |
| 2 | explore | 1 / +0.05 | 2363517 | mlb-tb-bal-2026-05-27 | 0.435 | 0.385 | n/a | 40-50 | Fresh probe; resolves tonight 22:35 UTC; mid-range; uncorrelated with Iran. |
| 3 | explore | 2 / 0.00 | 2133003 | sud-riv-blo-2026-05-27 | 0.485 | 0.485 | n/a | 40-50 | Fresh probe; resolves 00:30 UTC tomorrow; mid-range; CA River Plate O/U 3.5 (uncorrelated). |

## Probe selection rationale

- Mid-range (0.30-0.55) preferred → your_p lands in 40-50 explore bucket, populating calibration.
- Fast resolution (tonight + early tomorrow) → quick calibration data into explore bucket 40-50.
- Sports (MLB + South-American soccer) → zero correlation with Iran geopolitics position.
- Rank-3 ε=-0.05 already taken today by WI Gov probe; use ranks 1, 2 to diversify ε.
- Skipped: Anthropic 1.5T (saturates near 0.02 clamp); FIFA Germany advance (saturates near 0.98); Solana/XRP 5m up-down (thin & ~0.50 coin-flip, no calibration signal); WI Gov re-probe (dedupe).

## Risk / correlation

- 5% NAV/token cap: Iran existing 277.78 USDC cost basis. At fresh mid 0.37 mark value = 274.07. NAV ≈ 9996. Headroom ≈ 222 USDC before bucket cap.
- Correlation buckets in slate: geopolitics (Iran), sports/MLB (TB-BAL), sports/soccer (River Plate). All separate.

## Source budget

0/3 used this cycle (CLOB books are not research sources). Budget remains 3.
