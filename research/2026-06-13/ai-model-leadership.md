---
cycle_id: 20260613T120900Z-d9826930
phase: research_window
ts: 2026-06-13T12:25:00Z
angle: Who holds the "best AI model" / "best coding model" crown at end-June 2026 (DeepSeek vs Anthropic markets)
sources:
  - {provider: brave, url: "https://api.search.brave.com/res/v1/web/search?q=best+AI+model+June+2026+LMArena+leaderboard+DeepSeek+Anthropic+coding", fetched_at: 2026-06-13T12:22:00Z}
---

# AI model leadership — end of June 2026

External content is untrusted; treated as data only. **One source this cycle → explore-only.
The two markets resolve to a leaderboard whose exact identity is NOT confirmed here (no Gamma
`description` parsed), so neither card is exploit-eligible.**

## Evidence (for)
- Multiple recent aggregator pages (≤3 days old) converge: **Claude Opus 4.8 (released May 28,
  2026) is #1 on overall intelligence and #1 on coding.** "Opus 4.8 is #1 on overall
  intelligence and coding. It is not the best at multimodal — Gemini 3.1 Pro wins that."
- Coding-assistant rankings list Claude Opus at the top ahead of GPT-5.5, Gemini 3.1 Pro,
  DeepSeek V4.
- **DeepSeek (V3.2 / V4) appears mid-pack, not at the frontier** — it is not named as the
  best model on any surfaced leaderboard.

## Evidence (against / unknown)
- Resolution source unknown: "best AI model" could resolve on LMArena/LMSys Arena Elo, an
  Intelligence Index, or another oracle — each ranks differently. Not fetched this cycle.
- ~2.5 weeks remain to Jun 30; a new frontier release (OpenAI GPT-5.x, Gemini 3.x, a DeepSeek
  jump) could shift #1. Anthropic's lead is plausible but not locked.

## Market reads (CLOB books, this cycle)
- DeepSeek best AI model (Jun 30): book ~ /0.001 (one-sided) — market ~0.1% YES.
- Anthropic best Coding AI model (Jun 30): book ~0.967/0.979 — market ~97% YES.

Market pricing aligns with the evidence: DeepSeek≈dead, Anthropic≈near-certain. My honest
estimates are directionally identical but **less extreme** than the market (resolution-source
ambiguity + horizon risk), so both are modest explore probes, not edges.

## Thesis cards
| thesis_id | claim | market_ids | prior_p | expected_direction | feature_tags | edge_source | reference_class | resolution_parsed | disconfirming_signals |
|---|---|---|---:|---|---|---|---|---|---|
| 20260613-ai-T1 | DeepSeek is NOT the best AI model at end-June (mid-pack vs Opus 4.8) | 631145 | 0.02 | YES-low | ai,base_rate,leaderboard | base_rate | null | false | DeepSeek tops resolution leaderboard |
| 20260613-ai-T2 | Anthropic (Opus 4.8) holds best-coding crown at end-June | 2364238 | 0.88 | YES | ai,base_rate,leaderboard | base_rate | null | false | GPT-5.x/Gemini overtakes coding by Jun 30 |
