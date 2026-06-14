---
name: vision
maintained_by: skills/envision (Sunday deep pass)
created: 2026-05-29
last_revised: 2026-06-14
---

# North-Star

The living thesis on what would make this system genuinely great. `skills/envision` revises it
every Sunday. It is allowed to be ambitious. It is required to be honest.

## Mission (current framing — open to revision)

Become a forecaster that earns its edge: calibrated enough that its probabilities beat the market's,
disciplined enough to bet only when the edge is real and net of cost, and self-improving fast enough
that each week it is measurably smarter than the last. P&L is the eventual scoreboard; **learning
speed is the leading indicator.**

But the mission is not frozen. A system that only ever optimizes its own Brier score is small. The
Sunday pass should periodically ask the larger question: *what would make this matter beyond its own
account?* — sharper public forecasts, transparent reasoning others can learn from, a template for
how an autonomous agent can be trusted with consequential decisions. Those are legitimate directions
to propose.

## Weekly synthesis — 2026-W24 (assumption overturned)

The week's defining shift is **structural, not performance**: the 06-10→06-12 confabulated
`protected_core_violation` halt was closed for good (mechanical audit + pre-commit gate), and
forecasting resumed. But the sharper update is to our own model of the binding constraint:

> **The keystone has moved.** For three weeks the standing belief (VISION bet #1, the 06-13 horizon)
> was "every forecast is `resolution_parsed:false`, so the edge gate can *never* pass and exploit-n is
> frozen at 4 — the missing piece is a resolution-criteria parser." **That is now false.** The
> 2026-06-14 trade-window emitted forecasts carrying *fully parsed* `resolution_criteria` with explicit
> dates. The parser works. The constraint has moved downstream — to **emission integrity** (those same
> forecasts dropped `close_time` to null, making them silently unresolvable) and **gate wiring** (does a
> parsed criterion actually flip `resolution_parsed:true` and let `sizing` consider an exploit?).

The lesson generalizes: as one bottleneck clears, the next is rarely the glamorous one (better
calibration, new edge sources) — it is plumbing. **Calibration data is a scarce resource** (AGENTS
cost model), and this week we silently burned 6 data points to a null field. Right now,
**data-integrity guards out-leverage new alpha.** Hence this Sunday's self-enacted groom lint.

## Current bets (what we believe will move the needle)

1. **Provenance beats magnitude.** The Iran loss came from an *unverifiable* edge, not a thin one.
   Forecasts should be gated on parsed resolution criteria + a named reference class, not just spread.
   *(2026-06-14 update: the parser now produces parsed criteria — the gate's remaining blocker is
   wiring + emission integrity, not parsing capability.)*
2. **Forecast many, bet few.** Decouple learning (broad, cheap, no capital) from earning (rare,
   gated). Most cycles should teach us something even when we don't trade.
3. **Closing-line value is the fast signal.** Did the market move toward us after we spoke? That is
   knowable in hours; resolution Brier takes weeks.
4. **Cost honesty or nothing.** Midpoint fills and mid-marks flatter us into bad habits. Mark at
   liquidation, fill at the executable side, model fees.

## Open questions (where the next surprises probably live)

- What are we *systematically* not measuring? (Mon lens keeps returning here.)
- Is 10 invocations/day the right metabolism, or could fewer, deeper cycles learn faster?
- Where does the agent's own reasoning waste itself — and could a different process fix it?
- Is there an edge source we dismiss out of habit (mechanical biases, cross-market structure)?
- Could the human↔agent interface carry more signal than a daily Telegram digest?
- **Now that the parser works, what is the actual end-to-end path from a parsed criterion to a
  gate-passing exploit bet?** Trace it: emission must keep `close_time`; `resolution_parsed` must flip
  true; `reference_class` + ≥2 sources must attach; `sizing` must then size it. Where does it break?
- **How much calibration data have we lost to silent emission bugs**, and what minimal set of
  emission-integrity invariants (close_time present, resolution_parsed consistent with non-empty
  criteria) would make the learning loop trustworthy?

## Principles for envisioning

- Cite evidence; steelman the counter-case; name the cheapest experiment.
- One assumption-challenge per week, minimum.
- Reversible and paper-safe first. Nothing that risks capital or removes a safety rail is ever
  self-enacted.
- Coherence over volume: a few proposals that ladder up to this north-star beat a daily flood.

## Retired ideas

*(Kept with a one-line epitaph once tried-and-dropped. Empty at seed.)*
