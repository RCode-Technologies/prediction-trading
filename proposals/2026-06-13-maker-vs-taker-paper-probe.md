---
id: 2026-06-13-maker-vs-taker-paper-probe
title: Probe liquidity provision (maker) vs always crossing the spread (taker)
created: 2026-06-13
lens: moonshot / wildcard
status: surfaced
bucket: human_application
conviction: low
reversibility: hard
horizon: moonshot
supersedes: null
---

## Claim

The agent is structurally a **long-only price-taker**: it only ever BUYs at the ask and marks/sells at
the bid, paying the full spread on every round trip. On the thin Polymarket books it actually
forecasts, the spread is the single largest recurring cost — and it may be that the real edge on these
books is **providing** liquidity (resting a bid one tick inside the spread) rather than crossing it.
Challenge the assumption — baked into `config/guardrails.md` ("Long BUY only") and `strategy/current.md`
("you buy at the ask, sell at the bid") — that the agent must always be the taker.

## Evidence

- Every fill to date crossed the spread (`skills/trade` paper-fills at `best_ask`); cost honesty (v3
  bet #4) made that cost *visible* but did nothing to *reduce* it.
- CLV, the headline skill signal, is dominated by the `none` edge-source slice — `clv_n 21,
  clv_mean −0.031, hit_rate 0.33` — i.e. on average the market moved *against* us after we spoke. On a
  taker who pays spread, negative CLV and a paid spread compound.
- Today's `snap_clv` on market 631145 had to record `clv=0` because the book was **one-sided** (asks
  only, no bid). On books that thin, a resting bid would often be the *only* bid — high fill priority,
  full spread captured — exactly where a maker has structural advantage and a taker has none.
- The conviction ladder already gates *when* we bet; nothing examines *how* we enter.

## Why it might be wrong (steelman)

Posting resting orders invites **adverse selection**: on a thin book, the counterparties who lift your
resting bid are disproportionately the informed ones, so you get filled exactly when you're wrong and
miss when you're right — the captured spread is an illusion that realized P&L erases. Maker fills are
also *probabilistic* (you may never get filled and miss the move entirely), which breaks the current
deterministic fill model and the disconfirmation-stop accounting. And it adds real execution
complexity (order management, cancels, partial fills) to a system whose edge is supposed to be
*forecasting*, not microstructure — a classic scope creep away from the mission.

## Cheapest falsifying experiment

**Paper-only, zero capital, zero new live risk.** For the N most liquid universe markets each
trade-window, in addition to the existing taker forecast, *simulate* a resting bid one tick inside the
spread and record, over the next 24h of `snap_clv` book reads we already pull: (a) would it have
filled (did `best_ask` trade down through our resting price)? (b) realized spread captured vs the taker
baseline, net of an adverse-selection haircut (mark the simulated fill at the *subsequent* mid, not
entry). If, over ~20 simulated maker entries, fill rate is near zero **or** adverse-selection-adjusted
capture ≤ taker baseline, the idea is dead and we keep the taker stance. No order is ever posted; this
rides existing CLOB reads.

## Impact & cost

- **Edge:** if validated, a structurally lower entry cost on every bet — directly attacks the largest
  recurring drag and could flip marginal-edge candidates from reject to profitable.
- **Learning:** the paper probe itself yields a new, cheap metric (simulated maker capture by
  liquidity bucket) regardless of outcome.
- **Invocations/tokens:** the probe adds **zero** invocations (rides trade-window + existing
  `snap_clv` book reads) and a few lines of JSON/cycle.
- **Capital:** the *probe* has none (simulation only). **Live deployment would have capital + execution
  risk and would change the long-only-taker guardrail + the fill/mark/stop accounting** — which is why
  this is `human_application`, not self-enactable. Surface the probe results to a human; never post a
  resting order autonomously.

## Change sketch

`human_application` — the diff a human would accept, in two stages:

1. **Probe (paper, reversible):** extend the trade-window candidate record with a simulated
   `maker_entry = best_bid + tick` and, in `recalibrate.snap_clv`, when reading a probed market's book,
   append a `maker_sim` annotation (`would_fill`, `sim_capture_net`). Add a `maker_vs_taker` block to
   the daily recap. Touches `skills/markets`, `skills/recalibrate`, `skills/recap` — **none are
   protected-core** — but it changes the forecasting/accounting path, so a human should review before it
   ships.
2. **Only if the probe validates:** a separate human decision to relax `config/guardrails.md`
   (human-owned) and add a maker path to `skills/trade`/`skills/sizing`. Not in scope here.

This needs a human because it questions a human-owned guardrail and, at stage 2, touches real capital
and execution — exactly the line `config/autonomy.md` draws as off-limits to self-enactment.
