# Project Management

This folder holds everything about **planning, requirements, decisions and history** for the
Polymarket trading agent. It is **not loaded by the agent at runtime** — `CLAUDE.md`
only points at `AGENTS.md`, and `AGENTS.md` deliberately ignores this directory.

Humans and AI builders (e.g. Claude Code when extending the project) use this folder; the
runtime agent does not.

## Layout

```
pm/
├── README.md          # This file
├── CHANGELOG.md       # Chronological log of features shipped, newest first
├── prds/              # Product Requirements Docs — one per feature/version
│   └── <id>-<slug>.md
├── plans/             # Implementation plans — one per feature/version
│   └── <id>-<slug>.md
└── adrs/              # Architecture Decision Records
    ├── README.md      # ADR conventions + template
    └── NNNN-<slug>.md
```

## Conventions

- **PRD** = _what_ and _why_. Problem, goals, non-goals, acceptance criteria. Stable once
  approved; superseded only by a new PRD with a later id.
- **Plan** = _how_. Phases, file list, verification steps. Iterates freely during work.
- **ADR** = an irreversible-ish design decision worth remembering. Short. Numbered
  monotonically (`0001`, `0002`, …). Status: `Accepted` / `Superseded by NNNN` / `Deprecated`.
- **CHANGELOG** = human-readable summary of what landed and when. Newest entry on top.
  Versioning is loose semver-ish (`v0.x` until first mainnet trade, then `v1.0`).

## Workflow for a new feature

1. Open a PRD: `pm/prds/<id>-<slug>.md` — what & why & acceptance criteria.
2. Open a plan: `pm/plans/<id>-<slug>.md` — how, with phased steps and verification.
3. Capture any non-trivial design choices as ADRs in `pm/adrs/`.
4. Implement.
5. Add a CHANGELOG entry under a new version heading.

For tiny changes (typo, doc tweak), skip PRD/plan and just log in CHANGELOG.
