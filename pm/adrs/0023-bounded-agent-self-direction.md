# 0023 — Bounded agent self-direction, governed by a protected core it cannot amend

- **Status:** Accepted
- **Date:** 2026-05-29
- **Related:** part of the **v3 epoch** — PRD [v3-edge-and-learning](../prds/v3-edge-and-learning.md)
  §"Folded into v3" + [plan](../plans/v3-edge-and-learning.md) Phase 7. Sibling: ADR 0024 (weekly groom).
  Extends ADR 0005 (reflection edits strategy only) — self-direction is the governance layer *above*
  calibration. Reuses ADR 0014 (circuit-breaker as a skill) for the halt, ADR 0016 (git-identity
  defaults in `persist`) for the trust boundary, ADR 0013 (Conventional Commits) for the
  enact/auto-rollback subjects, and ADR 0007 (snapshot-every-edit) as the precedent for revertible
  self-change. Respects the ≤15/day scheduled-invocation budget (v3's proposed ADR 0022).

## Context

`skills/reflect` already lets the agent evolve itself — but only within **one file**
(`strategy/current.md`) and **one layer** (calibration prose + a version bump), bounded by Brier/CLV
gates and a 14-day regression simulation (ADR 0005). Every *capability-level* leap — a new skill, a
new metric (CLV), a new routine, a rethink of the mission — has been authored by a human in `pm/`
under an explicit *"the builder prepares the diff, the human accepts"* doctrine. Conceiving and
writing those leaps was the supervisor's manual job, and it was **the bottleneck to real autonomy**:
the system could refine its aim but never grow a new limb without a human typing it.

The supervisor asked (2026-05-29) for the system to **propose its own new versions once a day**, and
to treat that moment as its most ambitious — *"act as a super-intelligent being capable of reflecting
how to change the world and make it better,"* not run a checklist. That creates one hard question:
**how do you let an agent write its own code without letting it write away its own safety rails?**

Options on the table:

- **Propose-only (no self-implementation).** Safe, but leaves the human as the sole author — only
  half-solves the bottleneck.
- **Full self-modification.** Maximizes autonomy, but an agent that can edit its guardrails, breaker,
  or capital math has no enforceable safety envelope at all.
- **Bounded self-implementation behind a constitution the agent cannot amend.** Chosen.

## Decision

The agent may **author** capability proposals daily and **self-implement** a narrow, reversible,
paper-only subset — bounded by a human-owned charter (`config/autonomy.md`) it is structurally unable
to change.

1. **Two new skills, one charter, one workspace.**
   - `skills/envision` (agent-owned): daily creative governance. Reflects on the whole system
     (rotating daily lens; MAX-reasoning Sunday deep pass) and authors proposals into `proposals/`.
     Distinct from `reflect` — envision reaches everything reflect cannot: new skills, new metrics,
     AGENTS.md/guardrail *recommendations*, market-structure pivots, the agent's own cognition, and
     open-ended moonshots including the mission itself.
   - `skills/enact` (agent-executed, **protected core**): Sundays only, **≤1/week**. Self-implements
     one `self_approved`, non-vetoed, denylist-clean proposal as a single revertible commit; arms
     auto-rollback.
   - `config/autonomy.md` (**human-owned, protected core**): the constitution —
     identity-as-trust-boundary, protected-core manifest, self-enactment denylist + allowlist,
     cadence caps, veto + auto-rollback policy.
   - `proposals/` (agent-owned): `VISION.md`, `LEDGER.md`, `YYYY-MM-DD-<slug>.md` RFCs,
     `horizon.jsonl` — mirroring the `recaps/` + `research/INDEX.md` conventions.

2. **Identity is the trust boundary.** The agent commits as `Polymarket Trading Agent` /
   `agent@prediction-trading.local`; humans commit as themselves. Every safety check keys off one
   question — *was this authored by the agent identity?* The agent cannot alter its rails without
   leaving an agent-authored fingerprint on a protected file.

3. **A protected core the agent may never self-modify:** `config/{autonomy,guardrails}.md`,
   `AGENTS.md`, `skills/{boot,persist,circuit-breaker,enact,recalibrate,risk}`. Each is an enforcement
   rail, the capital-safety doc, or the metric ruler — if the agent could edit one, it could unwind
   the rest.

4. **Enforced three ways (defense in depth):** (a) `enact` *intent gate* refuses to write any
   denylist path; (b) `persist` *write gate* refuses to commit a protected-core path under the agent
   identity; (c) `boot` *integrity audit* halts (`protected_core_violation`) if any protected-core
   path's last commit is agent-authored.

5. **Self-enactment is narrow and reversible.** Only changes that are reversible (single
   `git revert`), zero-capital-effect (paper only), denylist-clean, and self-contained may be
   self-enacted. Anything touching guardrails, capital/portfolio state, the breaker, mainnet, or
   secrets is `human_application` — surfaced, never self-enacted.

6. **Veto-after, with a standing ≥7-day window.** Proposals are self-approved daily but enacted no
   earlier than the next Sunday. The human vetoes by repo action (`git revert <sha>`, or set
   `LEDGER.md` status to `vetoed`) at any time — there is no inbound channel. Auto-rollback reverts an
   enactment that regresses, mirroring reflect's 3-strike philosophy.

7. **Rides the existing `daily-close` cycle** — **zero new scheduled invocations** (respects the
   ≤15/day budget).

## Consequences

- **The version-proposal bottleneck is gone.** The system conceives and drafts its own capability
  leaps; the human ratifies or vetoes instead of conceiving from scratch.
- **The agent has a constitution it cannot amend.** Three independent gates, all keyed to commit
  identity, make widening the envelope a self-tripping act. This is the safety backbone; without it,
  self-implementation would be unbounded.
- **A new failure surface: `protected_core_violation`.** If a protected-core file is ever committed
  under the agent identity, the next boot halts the cycle (no phase work) until a human resolves it.
  **Operational corollary:** the protected-core files must be committed under the *human* identity —
  an agent-cycle commit of them would self-halt on the next boot. This is a deliberate forcing
  function, not a bug.
- **Bounded blast radius.** ≤1 enactment/week, paper-only, single revertible commit, auto-rollback
  armed, standing human veto. A bad self-edit costs at most one cycle and one `git revert`.
- **Honest residual gap.** A single cycle could in principle stage a self-edit to `persist` that also
  disables the write gate; it is caught by the next boot's audit + auto-rollback + human veto, and the
  whole system is paper-mode. The threat model targets *emergent overreach*, not a deliberately
  adversarial actor. Documented in `config/autonomy.md` § Enforcement.
- **Proposal quality is not guaranteed.** A novelty gate, conviction threshold, mandatory
  self-critique (steelman + cheapest falsifying experiment), and a ≤1–3/day surface cap guard against
  spam; empirical improvement remains unproven until the loop runs.
