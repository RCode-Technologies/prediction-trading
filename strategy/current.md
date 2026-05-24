---
version: v0
created: 2026-05-24
owner: agent
---

# Current Strategy — v0 Baseline (Observation)

This file is **owned by the agent**. The reflection routine
(`routines/80-reflect.md`) edits it daily based on observed outcomes,
snapshotting the prior version to `strategy/history/` on every edit
(ADR 0007). Humans do not write strategy content; they only set risk limits
in `config/guardrails.md` and the mode flag in `config/mode.json`.

You — the agent — are expected to grow this from a one-page baseline into a
full financial model as you accumulate research, observed market behavior, and
reflection data. Build out, at minimum:

- **Probability calibration methods.** How do you translate research into a
  numeric `your_p` per outcome? Track your Brier score across resolved
  markets and adjust.
- **Sizing framework.** v0 uses fractional Kelly at `f = 0.25`:
  `kelly_fraction = (your_p - market_p) / (1 - market_p)` then
  `notional = clamp(0.25 * kelly_fraction * NAV, 0, 0.05 * NAV)`. Iterate.
- **Market selection criteria.** Liquidity floor, time-to-resolution
  preference, edge floor in basis points.
- **Correlation rules.** Beyond the guardrail bucket, how do you recognize
  related markets early?
- **Edge-identification heuristics.** Which patterns have produced realized
  edges? Which produced false signals?

## v0 Baseline rules

- **Phase:** Observation. `config/mode.json.observation_only == true` for the
  first 48 hours. Record `forecast` events only — no paper fills.
- **Minimum edge floor:** 300 bps (`|your_p - market_p| >= 0.03`). Reject
  candidates below this.
- **Sizing:** fractional Kelly with `f = 0.25` (above), capped at 5% of NAV
  per token bucket (per `config/guardrails.md`).
- **Market selection:** Gamma `liquidityNum >= 5000`, `endDate` within 30
  days, both bid and ask present, midpoint ≤15 min old.
- **Research style:** prioritize Polymarket Gamma + one search provider per
  cycle. Use the third source only if it materially changes your view.
- **Per-cycle output during observation:** one `research_note`, one
  `candidate_rank` (top 5), one or more `forecast` events on the top market.

## Reflection notes

(Updated by `routines/80-reflect.md`. v0 has no history yet.)

## Changelog

- v0 — 2026-05-24 — Initial seed. Observation-only baseline; the agent owns
  growth of this file.
