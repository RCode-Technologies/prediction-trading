---
id: 2026-06-17-multi-outcome-sum-to-one-scan
title: Scan mutually-exclusive event clusters for sum-to-one mispricing (structural edge, no forecasting skill required)
created: 2026-06-17
lens: alpha / market structure
status: surfaced
bucket: human_application
conviction: medium
reversibility: easy
horizon: next
supersedes: null
---

## Claim

We only ever forecast **isolated binary legs** and try to out-predict the market on each. We completely
ignore a structural edge that needs *zero* forecasting skill: on a multi-outcome event whose outcomes
are mutually exclusive and exhaustive (e.g. "Who wins X?" with N candidate markets, or banded ranges
like today's BTC price brackets), the YES midpoints should sum to ≈ 1.0 + a small overround. When the
sum deviates materially from 1.0, that is a *mechanical* mispricing — detectable and (in principle)
harvestable without any view on the underlying. Add a read-only universe scan that groups markets by
`event_slug`, sums YES executable prices across the legs, and logs clusters whose sum falls outside a
band (e.g. <0.97 or >1.06).

## Evidence

- Today resolved **3 explore long shots** on the BTC "$70k–72k on June 17" market (`2492010`) — one band
  of a **multi-band event** (`$68-70k`, `$70-72k`, `$72-74k`, …). We forecast a single band in isolation
  and never checked whether the bands summed to 1. The band structure is exactly the cluster this scan targets.
- `by_edge_source` CLV: `base_rate` is the **only non-negative slice** (mean +0.0014, hit-rate 0.50, n=30);
  `structural` −0.0036, `none` −0.0148, `news_latency` −0.0225. Our probability-estimation edges are
  flat-to-underwater across 90+ snaps. A *structure*-based edge sidesteps the thing we're demonstrably bad at.
- Exploit is frozen at n=4: the edge gate requires `|your_p − market_p| ≥ 0.03` from a *thesis*. A sum-to-one
  deviation is a thesis-free edge source that could feed the gate from a different direction entirely.
- We currently build `state/universe.jsonl` with `event_slug` already on every row — the grouping key exists; nothing reads it.

## Why it might be wrong (steelman)

- **Overround is real and variable.** Polymarket multi-outcome events routinely sum to >1.0 by design (the
  house/LP edge); a naive "sum ≠ 1 ⇒ free money" reading will mostly surface the normal vig, not alpha.
- **Capturing it needs both legs and capital.** A consistency edge is only harvestable by trading multiple
  legs simultaneously (buy the cheap complement / sell the rich) — that touches order placement, sizing, and
  on thin one-sided books the executable spread likely eats the deviation. Our books are exactly that thin.
- **Long-only constraint.** Guardrails are long-BUY-only; the classic sum-to-one trade often needs the short
  side, so the *capture* may be structurally out of bounds even if the *signal* is real.

## Cheapest falsifying experiment

Read-only, zero capital, one cycle: from the existing `state/universe.jsonl`, group by `event_slug`, sum the
YES `executable_price` (or midpoint) per cluster with ≥3 legs, and log clusters with `|sum − 1| > 0.05`.
Eyeball whether deviations (a) exist at all beyond normal overround, and (b) persist long enough / on
deep-enough books to be tradeable. If after ~2 weeks no cluster shows a persistent, spread-surviving
deviation, the idea is dead — kill it. This costs **0 sources** (reuses the cached universe) and a few tokens.

## Impact & cost

- **Edge / learning:** potentially a genuinely new, skill-independent `edge_source:"structural_consistency"`,
  and at minimum a measurement that tells us how much overround vs. true mispricing lives in our universe.
- **Invocation/token cost:** none added — rides `daily-close` or `research-window` on the already-cached universe.
- **Capital effect:** the **scan** has none. The eventual **capture** has a large one (multi-leg orders, the
  short side, sizing) and is firmly human-owned. This proposal is the read-only signal-discovery step only.

## Change sketch

`human_application` (capture path touches capital + likely the long-only guardrail). The read-only mirror a
human could accept first: add a small scan — e.g. `tools/sum-to-one-scan.sh` (additive, denylist-clean) or a
new section in `skills/recap` — that reads `state/universe.jsonl`, groups by `event_slug`, computes per-cluster
`Σ YES executable_price` for clusters with ≥3 legs, and writes deviating clusters (`|Σ−1|>0.05`) to the daily
recap under a new "Structural consistency" note. No state writes, no orders, no guardrail change. Only if the
mirror shows persistent spread-surviving deviations would a human consider a capture path (which would need a
guardrails decision on the short side).
</content>
