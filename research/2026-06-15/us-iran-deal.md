---
cycle_id: 20260615T121223Z-62cc61a4
phase: research_window
ts: 2026-06-15T12:18:00Z
angle: Status of a US x Iran deal and whether Mojtaba Khamenei is plausibly the signatory by July 31
sources:
  - {provider: agent_native_websearch, url: "https://commonslibrary.parliament.uk/research-briefings/cbp-10637/", fetched_at: 2026-06-15T12:15:00Z}
  - {provider: agent_native_websearch, url: "https://www.usnews.com/news/us/articles/2026-06-15/a-history-of-irans-nuclear-program-and-tensions-with-the-us-as-an-interim-deal-is-reached", fetched_at: 2026-06-15T12:15:00Z}
---

External content treated as untrusted data — used only to anchor a probability, not as instruction.

As of 2026-06-15, open-source reporting describes an **interim US–Iran deal** being finalized, with a
signing reportedly planned in Switzerland. Reported terms: reopening the Strait of Hormuz, oil-sanctions
relief, a ceasefire extension after a recent conflict, and full nuclear limits/verification deferred to a
separate ~60-day track. Direct VP-led talks in April 2026 reportedly ended without a deal; momentum has
since shifted toward an interim agreement.

The specific Polymarket question (`2512442`) asks whether **Mojtaba Khamenei** signs a US x Iran deal by
**July 31**. The newsflow makes *a* deal more likely than base rate, but the named-signatory condition is
narrow: bilateral deals of this kind are signed by foreign ministers / heads of delegation, not the
Supreme Leader's son. Market midpoint ≈ 0.065 looks roughly fair; my honest estimate is marginally above
it (0.07) on raised deal odds, but the signatory specificity caps the upside. **This is the same
ambiguous-resolution geopolitical shape as the 2026-05-27 Iran loss — kept explore-only (no capital).**
The Gamma `description` was not formally parsed and only one search provider backs this, so the exploit
gate (resolution_parsed ∧ reference_class ∧ ≥2 sources ∧ edge_net≥0.03) is not met.

## Thesis cards
| thesis_id | claim | market_ids | prior_p | expected_direction | feature_tags | edge_source | reference_class | resolution_parsed | disconfirming_signals |
|---|---|---|---:|---|---|---|---|---|---|
| 20260615-us-iran-deal-T1 | Interim US–Iran deal is near, but Mojtaba Khamenei as the *signatory* by Jul 31 stays unlikely | 2512442 | 0.065 | YES slightly up | geopolitics,news_latency,explore | news_latency | (unnamed — not 2-source-backed) | false | deal signed by FM/president not M. Khamenei; talks collapse; deadline slips past Jul 31 |
