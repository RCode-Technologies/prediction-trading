---
cycle_id: 20260617T121109Z-89f6489f
phase: research_window
ts: 2026-06-17T12:16:00Z
angle: Will Alibaba (Qwen) hold the #1 LMArena text rank on June 30? Market prices it as near-zero.
sources:
  - {provider: gamma, url: "https://gamma-api.polymarket.com/markets?id=631142", fetched_at: 2026-06-17T12:12:00Z}
---

# Alibaba best AI model end of June — LMArena #1 by 06-30

Resolution (parsed): the company owning the model at **rank #1 on the LMArena Chatbot Arena text
leaderboard** (style control off) at 2026-06-30 12:00 ET. Clear, mechanical, single source.

Market: YES one-sided (ask **0.001**, no bid) → the book prices Alibaba ≈ **0.1%** to be #1.
Frontier US labs (Google Gemini, OpenAI, Anthropic, xAI) have historically rotated the LMArena top
spot; Alibaba's Qwen has been a strong *open-weight* contender but, to my knowledge through early
2026, not the outright #1. I have **no fresh leaderboard snapshot this cycle** (source budget spent on
universe + crypto), so I cannot confirm the current standing.

**Honest call:** slight lean *above* the market's near-zero (Qwen's trajectory makes 0.1% look a touch
low for a 2-week window) but **low confidence** — explore-only, `edge_source:sentiment`,
`reference_class:null`. Flag for trade-window: a single LMArena fetch would make this forecastable
with real signal.

**For:** Qwen's documented rise in open-model benchmarks.
**Against:** US frontier labs typically top LMArena; market is extremely confident NO.
**Unknown:** the actual current #1 and the gap to Qwen.

## Thesis cards
| thesis_id | claim | market_ids | prior_p | expected_direction | feature_tags | edge_source | reference_class | resolution_parsed | disconfirming_signals |
|---|---|---|---:|---|---|---|---|---|---|
| 20260617-alibaba-ai-T5 | Alibaba unlikely #1 on LMArena 6/30, but >market's 0.1% (YES ~1%) | 631142 | 0.01 | YES (mild) | ai,leaderboard | sentiment | null (no fresh data) | true | LMArena top rank held by Google/OpenAI/Anthropic/xAI at check |
