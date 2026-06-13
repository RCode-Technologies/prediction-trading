---
cycle_id: 20260613T120900Z-d9826930
phase: research_window
ts: 2026-06-13T12:20:00Z
angle: Current BTC/ETH spot vs near-term Polymarket price-threshold markets (Jun 14–18)
sources:
  - {provider: brave, url: "https://api.search.brave.com/res/v1/web/search?q=bitcoin+ethereum+price+today+June+13+2026", fetched_at: 2026-06-13T12:15:00Z}
---

# Crypto price thresholds — BTC/ETH (Jun 14–18 close)

External content is untrusted; treated as data only. **One source this cycle → all cards
are explore-only (forecast, no capital). The exploit gate needs ≥2 independent providers +
a parsed Gamma `description` + a named reference class; none of that is met here.**

## Evidence (for)
- Brave surfaced a dated quote: **Fri Jun 5, 2026 — BTC opened ~$63,812, fell to ~$62,046;
  ETH opened ~$1,768.86** (down 2.4% on the day). A CoinMarketCap headline ("BitMine Adds
  126K ETH at Year Low") corroborates ETH trading near a 2026 low.
- BTC near ~$62k sits comfortably above the $56k threshold (~10% cushion) and far below the
  $70–72k band (~+13–16% required, plus a $2k-wide band constraint).

## Evidence (against / unknown)
- **Data is ~8 days stale** (Jun 5). The "continued descent" narrative implies ETH may have
  fallen further by Jun 13; current spot is unknown. This caps confidence on every ETH card.
- No fresh intraday quote; no second independent provider; resolution `description` (oracle,
  snapshot time) not fetched. So these are calibration probes, not bets.

## Market reads (CLOB books, this cycle)
- BTC > $56,000 (Jun 18): book ~0.982/0.987 — market ~98% YES.
- BTC in $70,000–$72,000 (Jun 17): book ~0.009/0.019 — market ~1.4% YES.
- ETH > $1,700 (Jun 18): book ~0.39/0.42 — market ~40% YES.
- ETH > $1,800 (Jun 14): book ~0.004/0.008 — market ~0.6% YES.

The very low ETH>$1,800 price implies ETH is currently well under $1,800 (consistent with a
post-Jun-5 drop below the ~$1,768 print), reinforcing the staleness caveat.

## Thesis cards
| thesis_id | claim | market_ids | prior_p | expected_direction | feature_tags | edge_source | reference_class | resolution_parsed | disconfirming_signals |
|---|---|---|---:|---|---|---|---|---|---|
| 20260613-crypto-T1 | BTC holds > $56k through Jun 18 (large cushion vs ~$62k spot) | 2506684 | 0.96 | YES | crypto,structural,price-threshold | structural | null | false | BTC drops >10% in 5d |
| 20260613-crypto-T2 | BTC NOT in $70–72k band on Jun 17 (far from ~$62k spot) | 2492010 | 0.03 | YES-low | crypto,structural,price-threshold | structural | null | false | sharp BTC rally into band |
| 20260613-crypto-T3 | ETH > $1,700 on Jun 18 is ~coin-flip given year-low/descent | 2506608 | 0.44 | YES | crypto,structural,price-threshold | structural | null | false | confirmed ETH spot << 1700 |
| 20260613-crypto-T4 | ETH > $1,800 on Jun 14 unlikely (below 1800, ~1d horizon) | 2462645 | 0.02 | YES-low | crypto,structural,price-threshold | structural | null | false | overnight ETH spike >+2% |
