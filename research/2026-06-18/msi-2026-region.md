---
cycle_id: 20260618T120718Z-7a51ba91
phase: research_window
ts: 2026-06-18T12:15:00Z
angle: Will an LPL (China) team win MSI 2026? Base-rate (region title history) vs current form + sharp consensus.
sources:
  - {provider: brave, url: "https://en.wikipedia.org/wiki/2026_Mid-Season_Invitational", fetched_at: 2026-06-18T12:12:00Z}
  - {provider: agent_native_websearch, url: "https://www.oneesports.gg/league-of-legends/all-lol-msi-winners/", fetched_at: 2026-06-18T12:14:00Z}
---

# MSI 2026 — winning region (LPL/China)

**Question (Polymarket 1494696):** "Will a team from LPL (China) win MSI 2026?" Resolves to the
region of the 1st-place team at MSI 2026 (Daejeon, South Korea; June 28 – July 12). Resolution
source: lolesports.com / Liquipedia. Eleven teams: two each from LCK, LPL, LEC, LCS, LCP + one
CBLOL. **`resolution_parsed: true`** (Gamma description parsed).

**Market:** YES (LPL) best_bid 0.32 / best_ask 0.33, mid 0.325, spread 0.01, liquidity ~$48k.

## Reference class (base rate)

Named class: **MSI champion region distribution, 2015–2025 (10 editions).**
- LPL: 5 titles (EDG 2015, RNG 2018/2021/2022, JDG 2023) → all-time LPL share ≈ 0.50.
- LCK: 4 (SKT 2016/2017, Gen.G 2024/2025).
- LEC: 1 (G2 2019).

All-time region base rate alone would put LPL ≈ 0.50 — i.e. *above* the market.

## Evidence against the naive base rate (why I do NOT bet)

- **Recent form is all LCK.** Gen.G won 2024 and went **undefeated** to win 2025; LCK holds the last
  two titles.
- **Host advantage:** MSI 2026 is in Daejeon, South Korea (LCK home region).
- **Seeding:** LCK sends #1-seed Hanwha Life Esports (HLE) and T1; LPL sends Bilibili Gaming and Top
  Esports. BLG won First Stand in March (beat G2 3–1) — LPL is strong but not the favorite.
- **Sharp consensus already agrees with the market:** independent prediction markets price the
  *winning region* at **LCK ≈ 66% / LPL ≈ 33%** — essentially identical to Polymarket's 32.5%.

## Verdict

Honest `your_p(LPL) ≈ 0.35` — a mild lean above market for LPL's deep historical strength, but I will
**not** override a liquid, sharp consensus with a stale all-time base rate (the 2026-05-27 Iran lesson:
do not manufacture edge). `edge_net = 0.35 − 0.33 = 0.02 < 0.03` net floor → **forecast-only (explore)**,
gate-miss reason `edge_below_net_threshold`. Disconfirming signal: any pre-MSI bracket/roster news
swinging the LCK↔LPL line by >5pp.

## Thesis cards

| thesis_id | claim | market_ids | prior_p | expected_direction | feature_tags | edge_source | reference_class | resolution_parsed | disconfirming_signals |
|---|---|---|---:|---|---|---|---|---|---|
| 20260618-msi-lpl-T1 | An LPL team wins MSI 2026 | 1494696 | 0.35 | YES slightly up vs 0.325 | esports,base_rate | base_rate | MSI champion region distribution 2015-2025 (10 editions) | true | LCK host+#1 seed; consensus 33%; roster/bracket swing >5pp |
