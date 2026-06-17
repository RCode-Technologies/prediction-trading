---
cycle_id: 20260617T121109Z-89f6489f
phase: research_window
ts: 2026-06-17T12:15:00Z
angle: Near-dated Polymarket crypto strike markets vs current spot — are the deep-OTM lottery tickets fairly priced?
sources:
  - {provider: coingecko, url: "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,ripple&vs_currencies=usd", fetched_at: 2026-06-17T12:13:00Z}
  - {provider: gamma, url: "https://gamma-api.polymarket.com/markets?id=...", fetched_at: 2026-06-17T12:12:00Z}
---

# Crypto price-strike screen — 2026-06-17

Spot (CoinGecko, ~12:13Z): **BTC $64,788 · ETH $1,762.45 · SOL $72.15 · XRP $1.19**.

All four candidates resolve off a **Binance 1m candle** (close at noon ET for the daily strikes;
intra-month low for the BTC barrier) — resolution is mechanical and fully parsed. Each is a
deep-out-of-the-money lottery ticket; I size the YES leg with a lognormal/​barrier-touch model
(daily vol ≈ 3% BTC, 4% ETH, 5–6% SOL/XRP) as a *single-source structural reference*, **not** a
2-source base-rate class — so all four stay **explore-only** (no exploit eligibility).

- **BTC dip to $47,500 in June** [2410579, close 07-01 04:00Z]: −26.7% from $64.8k with ~13 days
  left. Barrier-touch ≈ 2·N(−0.267/(0.03·√13)) ≈ **1.4%**. Market mid 0.0105. ~Fair; tiny fat-tail lean.
- **ETH > $2,000 on Jun 18** [2506625, close 06-18 16:00Z]: +13.5% in ~1.3 days. z≈2.96 → close-above ≈ **0.15%**. Market mid 0.006 — slightly rich but de-minimis.
- **SOL > $110 on Jun 17** [2492166, close today 16:00Z]: +52% in ~4h → ≈ **0**. One-sided book (ask 0.001, no bid). Essentially settled NO.
- **XRP in $0.90–$1.00 on Jun 18** [2506791, close 06-18 16:00Z]: needs −16% to −24% into the band; P(in band) ≈ **0.3%**. Market mid 0.0015. ~Fair.

**For:** spot far from every strike; short horizons; mechanical Binance resolution.
**Against / unknown:** crypto fat tails (a single macro shock could move ETH/XRP fast); my vol inputs are point estimates, not a sourced realized-vol series.

## Thesis cards
| thesis_id | claim | market_ids | prior_p | expected_direction | feature_tags | edge_source | reference_class | resolution_parsed | disconfirming_signals |
|---|---|---|---:|---|---|---|---|---|---|
| 20260617-btc-47500-T1 | BTC will not dip to $47,500 in June (YES ~2%) | 2410579 | 0.02 | NO | crypto,barrier | structural | crypto-intramonth-drawdown-barrier (1 src) | true | BTC breaks <$55k with crash momentum; risk-off cascade |
| 20260617-eth-2000-T2 | ETH not above $2,000 by noon ET 6/18 (YES ~1%) | 2506625 | 0.01 | NO | crypto,daily-strike | structural | crypto-1d-+13pct-move (1 src) | true | ETH rallies >10% on ETF/macro catalyst before noon ET |
| 20260617-sol-110-T3 | SOL not above $110 by noon ET 6/17 (YES ~0.2%) | 2492166 | 0.002 | NO | crypto,daily-strike | structural | crypto-4h-+52pct-move (1 src) | true | implausible 4h melt-up |
| 20260617-xrp-90-100-T4 | XRP not in $0.90–$1.00 by noon ET 6/18 (YES ~0.4%) | 2506791 | 0.004 | NO | crypto,range-strike | structural | crypto-1d-band-landing (1 src) | true | sharp XRP selloff into the band |
