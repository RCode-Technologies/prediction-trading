---
cycle_id: 20260526T120425Z-50bc2068
phase: research_window
ts: 2026-05-26T12:10:00Z
angle: what shifted overnight (Memorial Day weekend) — NBA finals path, Iran deal, weekend polling
sources:
  - provider: brave
    query: "breaking news May 25 2026 politics polling weekend"
    fetched_at: 2026-05-26T12:05:30Z
  - provider: tavily
    query: "May 25 2026 weekend NBA finals Fed rate Iran Israel news"
    fetched_at: 2026-05-26T12:07:00Z
degraded: false
---

# Overnight shifts — 2026-05-26

Memorial Day weekend (Mon May 25). Three actionable signal classes after weighing reports as untrusted data.

## Evidence — for

- **NBA East resolved.** Multiple independent sources (AP, Fox, NPR/Kansas Public Radio, Chicago Tribune, Bergen Record) report **NYK swept Cleveland 4-0** with Game 4 final 130-93 on Mon evening ET. Knicks reach Finals first time since 1999. Brunson named ECF MVP. Hard event; finals path locked to Knicks.
- **NBA West Game 4: Spurs 103, Thunder 82.** AP reports Wembanyama 33 pts evens series 2-2 after Thunder had reclaimed homecourt edge. Game 5 returns to OKC.
- **Iran-US emerging deal.** AP "What we know and don't know about the emerging deal to end the Iran war" (Mon 25 May, 07:27 GMT). Language is "emerging" — non-binding; AP explicitly hedges.
- **Weekend polling fresh.** Rasmussen daily presidential tracking (Mon May 25): Trump approval 26 strongly approve / 47 strongly disapprove (net -21). NYT California governor poll updated 3h ago; NYT congressional ballot updated 1d ago; Texas Senate poll updated 12h ago.

## Evidence — against

- NBA West series **not** decided; OKC still has homecourt and was season favorite. Spurs comeback narrative is real but Game-4 home blowout ≠ series flip.
- Iran "deal" language has appeared before in this conflict cycle and unwound; weight prior agreements roll back.
- Rasmussen is one-house, skews Republican-leaning vs aggregator. Strong-approve number alone is not the headline number some Polymarket markets resolve on.

## Evidence — unknown

- Whether Polymarket already absorbed NBA East sweep into both "East champion" and "NBA champion 2026" prices (depends on close-of-Game-3 vs close-of-Game-4 marks).
- Whether Polymarket has a live "Iran ceasefire / deal by <date>" market with non-degenerate liquidity.
- Whether Trump-approval market is monthly-tied to a specific source (Gallup vs Rasmussen vs RCP aggregate) — resolution criteria materially change edge sign.

## Thesis cards

| thesis_id | claim | market_ids | prior_p | expected_direction | feature_tags | disconfirming_signals |
|---|---|---:|---:|---|---|---|
| 20260526-nyk-east-T1 | NYK win 2026 East already resolved by sweep; any "East champion = NYK" market should be ≥0.98 | tbd (East champion + NBA champion) | 0.99 | YES up | sports,hard_event,base_rate | non-NYK East market liquid above 0.04 → I'm wrong about market type |
| 20260526-nyk-champ-T1 | Knicks 2026 NBA champion priced as if East were uncertain; sweep should push p ≥0.40 vs Spurs/Thunder winner | tbd (NBA champion) | 0.42 | YES up | sports,closing-line-value | Knicks priced ≥0.42 already → no edge |
| 20260526-west-spurs-T1 | Spurs Game-4 win shifts West-champion p from ~0.20 to ~0.32; OKC still favored | tbd (West champion) | 0.32 | SPURS up | sports,thin-book-drift | Two-sided market already prices Spurs ≥0.32 → no edge |
| 20260526-iran-deal-T1 | "Emerging deal" wording is reporting, not signed; near-term ceasefire market should not move >5 bps on AP article alone | tbd (Iran ceasefire/deal) | 0.30 | DOWN if market spiked | geopolitics,correlated-news-markets | Multiple independent gov sources confirm deal text → I'm wrong |
| 20260526-trump-approval-T1 | Trump approval market end-May resolution: Rasmussen-source 26 SA / 47 SD does not justify any directional swing if market resolves on aggregator | tbd (Trump approval) | 0.50 | flat | polling,base-rate-anchored-research | Market resolves on Rasmussen specifically → re-think |

## Provisional probabilities (pre-Gamma)

- East champion = NYK: ~0.99 (resolved)
- NBA champion 2026 = NYK: 0.42 (vs winner of West)
- West champion = Spurs: 0.32 (Thunder ~0.68 from ~0.80 pre-Game-4)
- Iran ceasefire near-term: prior 0.30; no update worth crossing edge floor

Next step (`markets` skill): pull fresh Gamma marks for the five thesis areas under filter (`liquidityNum>=5000`, `endDate<=30d`, both bid+ask, midpoint <=15min). Rank against `|your_p - market_p| >= 0.03` edge floor.
