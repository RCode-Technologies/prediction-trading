---
cycle_id: 20260527T120743Z-62cd07c7
phase: research_window
ts: 2026-05-27T12:14:00Z
angle: US x Iran diplomatic meeting by June 7, 2026 — does an in-person bilateral materialise in the next 11 days given the late-May "deal largely negotiated" rhetoric?
sources:
  - {provider: agent_native_websearch, query: "US Iran diplomatic meeting talks scheduled June 2026 nuclear", fetched_at: 2026-05-27T12:12:30Z}
strategy_version: v2
---

# US x Iran diplomatic meeting by June 7

External reporting is treated as untrusted data.

## State of play (per surfaced headlines)

- **2026-05-23, CNN**: Trump publicly stated agreement with Iran has "been largely negotiated" and Strait of Hormuz will be opened; final aspects "announced shortly."
- **2026-05-07, Time/Axios**: parties closer to a one-page MoU than at any prior point since the war began; deal contours = enrichment moratorium + sanctions/funds relief + Hormuz transit normalization.
- **2026-04-27, Axios**: Iran's proposal explicitly *postponed* full nuclear talks while reopening Hormuz first → procedural staging implies meetings are venue-conditional, not date-driven.
- **House of Commons Library briefing** + earlier Feb/Mar NPR rounds → talks have repeatedly been "back on" then stalled; the pattern is announce → delay → resume.
- **Iran FM late May**: deal "inches away" but criticized "maximalist demands" — soft commitment signal.
- No specific meeting on the public docket between 2026-05-27 and 2026-06-07. Venues floated for "detailed negotiations" are Islamabad or Geneva.

## Base rate framing

- Stated probability of a *deal announcement* near-term is high (Trump's own "shortly" framing). A deal announcement typically requires or is accompanied by a meeting.
- But "meeting by June 7" is a specific narrow window: 11 calendar days. Prior negotiating rounds (Feb, Mar) had ~2-3 week gaps between confirmed meetings.
- Pattern interrupt risk: a one-page MoU could be exchanged through intermediaries (Oman channel) rather than a formal bilateral, voiding the resolution criteria depending on how strictly the market defines "diplomatic meeting."
- **Resolution-criteria uncertainty is the dominant risk.** Without the market description in hand the agent must assume conservatively-broad definition (any senior-level direct contact).

## Probability estimate

- Prior (cold): base rate for a confirmed bilateral diplomatic meeting between adversarial states within 11 days conditional on public "deal largely negotiated" rhetoric ≈ 0.45-0.55.
- Update for ambiguous venue/no scheduled date: −0.05 to −0.10.
- Update for Iran FM softer language: −0.03.
- **raw_your_p ≈ 0.45** vs market_p ≈ 0.375 → +7.5 pp edge (above 300 bps floor).

## Thesis cards

| thesis_id | claim | market_ids | prior_p | expected_direction | feature_tags | disconfirming_signals |
|---|---|---|---:|---|---|---|
| 20260527-us-iran-mtg-T1 | US-Iran senior diplomatic meeting occurs by 2026-06-07 | 2354045 | 0.45 | YES | geopolitics,base-rate-anchored-research,news_event | Iran cancels next round; deal announced via intermediaries only; FM hardens "maximalist demands" language |

## Confidence

Medium-low. Headlines align directionally but resolution criteria and venue specifics are unverified. Carrying as exploit-eligible with reduced confidence (0.45).
