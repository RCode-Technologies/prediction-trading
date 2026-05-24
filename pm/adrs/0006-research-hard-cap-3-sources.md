# 0006 — Research hard cap: 3 sources per cycle

- **Status:** Accepted
- **Date:** 2026-05-24
- **Related:** PRD v1-instruction-pack, routine 20-research

## Context

Research can balloon token usage. We considered soft caps (agent self-monitors) vs
hard caps (numeric ceiling enforced in the routine).

## Decision

`routines/20-research.md` enforces a **hard cap of 3 external sources per cycle**.
"Source" = one search-API query, one X query, one Polymarket Gamma/Data market-discovery
query, or one generic URL fetch. Polymarket Gamma `/markets` listings count as one
source regardless of how many markets are returned. `20-research.md` and
`30-analyze-markets.md` share the same per-cycle source counter. Execution safety
checks in `40-decide-and-size.md` and `50-execute-trade.md` may fetch fresh CLOB
prices and do not count as research sources. The agent stops further research or
market-discovery fetches once 3 are consumed.

## Consequences

- Predictable token/cost ceiling per cycle.
- Hard limit may starve research on slow news days; mitigated by the hourly cadence —
  the next cycle picks up more sources.
- Cap is encoded in the routine, not in AGENTS.md, to keep boot context lean.
