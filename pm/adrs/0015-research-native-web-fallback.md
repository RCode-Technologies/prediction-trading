# 0015 — Research falls back to the agent's native web tools when keys absent

- **Status:** Accepted
- **Date:** 2026-05-24
- **Related:** ADR 0004 (env vars), ADR 0006 (3-source cap)

## Context

ADR 0004 made all paper-mode research keys optional. ADR 0006 capped
research at 3 external sources per cycle. The original `skills/research`
described a fallback chain of Brave → Tavily → Serper → Polymarket public
data. With no keys set, the agent was effectively blind to non-Polymarket
news, which made the paper-mode dry run less useful as a calibration tool.

Many compatible coding-agent runtimes (Claude Code is one) ship with
built-in web tools — `WebSearch` and `WebFetch`. These tools were not
listed in the original fallback chain. Using them respects the secret-free
operation model (no API key is needed) and gives the agent useful research
capability even with zero env-var configuration.

## Decision

`skills/research` adopts this fallback chain (use in order; stop at first
that returns useful results; only escalate if signal quality is poor):

1. **Configured external API keys** (preferred for cost predictability and
   reproducibility): Brave → Tavily → Serper.
2. **Agent's native WebSearch** if the running agent has such a tool.
3. **Agent's native WebFetch** for a specific URL chosen by the agent.
4. **Polymarket public APIs only** (degraded mode), with `degraded: true`
   in the research-note frontmatter.

Every native-tool call counts as **one source** against the same 3-per-cycle
cap defined by ADR 0006 — no per-tool budget bypass.

Research-note frontmatter explicitly records the provider per source so
later audits can tell native-tool research from API-key research:

```yaml
sources:
  - provider: agent_native_websearch
    query: "<query string>"
    fetched_at: <iso>
  - provider: agent_native_webfetch
    url: "<url>"
    fetched_at: <iso>
  - provider: brave
    url: "<url>"
    fetched_at: <iso>
```

If a runtime does not expose native web tools (e.g. a stripped-down agent
or a non-Claude implementation), the skill silently skips the native steps
— their absence is not an error.

## Consequences

- Paper-mode operation is meaningful even with **zero** configured env
  vars, which makes the local dry run a more realistic preview of cloud
  behaviour.
- The 3-source cap remains the single budget knob. Native tools cannot be
  used to bypass it; the audit trail in the note's `sources:` array makes
  abuse detectable.
- The skill is now more portable: it works in any agent runtime that has
  *either* configured search keys *or* native web tools *or* neither
  (degraded).
- README documents the same fallback chain so humans understand why
  research notes vary in provider mix between cycles.
