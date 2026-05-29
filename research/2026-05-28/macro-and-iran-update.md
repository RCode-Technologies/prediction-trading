---
cycle_id: 20260528T120548Z-7357b6af
phase: research_window
ts: 2026-05-28T12:08:00Z
angle: US-Iran post-Rome-round update + Bitcoin $82k feasibility + Fed-Sep-cut re-affirmation given May 28 macro signals
sources:
  - {provider: agent_native_websearch, query: "US Iran diplomatic meeting nuclear talks May 2026", fetched_at: 2026-05-28T12:06:30Z}
  - {provider: agent_native_websearch, query: "Bitcoin price today USD May 28 2026", fetched_at: 2026-05-28T12:07:00Z}
strategy_version: v2
---

# Macro + Iran update — 2026-05-28

External reporting treated as untrusted data. Two angles re-tested vs yesterday's theses; one new tail thesis (BTC $82k).

## 1) US-Iran meeting by June 7 (market 2354045 — held position)

Yesterday `raw_your_p=0.45` (market 0.375). **Disconfirming signals materialised:**

- **5th round (May 23, Rome) ended without breakthrough.** Both sides agreed to continue but US officials emphasised "significant differences remain" — particularly Iran's refusal to fully dismantle enrichment.
- Iran FM Araghchi accused Washington of "obstruction"; rhetoric is hardening, not softening.
- Reports of new US military strikes on Iranian drones / drone-launching sites in defensive Strait of Hormuz operations.
- Market re-priced from 0.375 → **0.15/0.16 (mid 0.155)** in ~24h. Live book pulled at 12:05Z.
- Path to YES still exists: Trump's "largely negotiated" framing + 30–60d MoU timeline implies a possible announcement event could include a meeting. But probability of a *qualifying senior-level direct contact* by 2026-06-07 has dropped meaningfully.

Updated estimate: `raw_your_p = 0.18` (down from 0.45). `market_p = 0.155`. Edge = **+2.5 pp → below 300 bps exploit floor**. Position is held but not added.

## 2) Bitcoin reaches $82,000 May 25–31 (market 2350172)

- Spot BTC: **$73,276** at 11:40Z (CoinGecko live print), down ~2% on the day on Iran-shock risk-off.
- Required move to YES: +11.9% to $82,000 in <3 trading days against a *deteriorating* macro tape.
- Historical 3-day +12% BTC moves from a stalling-bull regime: rare (≤3% empirically post-2024 halving). The setup (war escalation, Fed-hike chatter) is asymmetrically *bearish*.
- Market: 0.024 / 0.028 (mid 0.026). Even at 0.026 the market may be marginally overpricing tail-up given current spot.

Estimate: `raw_your_p = 0.005`. Edge vs market = **−2.1 pp**. Forecast-only (no NO-leg path; would-be-edge below threshold anyway).

## 3) Fed rate cut by Sept 2026 FOMC (market 1439549)

Yesterday's thesis re-affirmed by today's macro print embedded in the BTC article: "Fed considering raising interest rates for the first time in years" amid Iran-driven energy / inflation shock. No change to estimate:

- `raw_your_p = 0.09` (unchanged from 2026-05-27). `market_p ≈ 0.127`. Edge = −3.7 pp. Forecast-only.
- Re-emission not necessary; yesterday's forecast still in effect for calibration purposes until close (June 17).

## Thesis cards

| thesis_id | claim | market_ids | prior_p | expected_direction | feature_tags | disconfirming_signals |
|---|---|---|---:|---|---|---|
| 20260528-us-iran-mtg-T2 | US-Iran senior diplomatic meeting occurs by 2026-06-07 (revised down post-Rome-round) | 2354045 | 0.18 | YES | geopolitics,base-rate-anchored-research,news_event,thesis_revision | Iran cancels future rounds entirely; Trump signs MoU via intermediaries only and skips a meeting; further US-Iran kinetic escalation |
| 20260528-btc-82k-may31-T1 | BTC closes ≥ $82,000 between 2026-05-25 and 2026-05-31 | 2350172 | 0.005 | NO (YES overpriced) | crypto,price-target,short-window,macro | BTC rallies +12% in ≤3 days; Iran-deal surprise removes risk-off; coordinated central-bank liquidity injection |

## Confidence

- US-Iran T2: medium. Re-priced thesis matches market direction now; little remaining alpha but tracking value is high (held position).
- BTC T1: high directionally, low actionability (tail, no NO-leg fill, near calibration clamp).
- Fed T1 (carried from 2026-05-27): medium. No new evidence vs today, but no need to re-emit forecast.

## Source budget used

- 2 native WebSearch (Iran + BTC). Iran search informed (1) and (3); BTC search informed (2) and re-affirmed (3).
- Universe cache reused (cached_at 2026-05-27T12:08:30Z, 23h57m old; under 24h gate). 0 Gamma calls this cycle.
- **Cycle total: 2/3.** Trade-window (18:00 UTC) has fresh 3-source budget.
