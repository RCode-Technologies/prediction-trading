# proposals/ — the agent's self-direction workspace

**Agent-owned.** Written by `skills/envision` (daily) and `skills/enact` (Sunday). Mirrors the
conventions of `recaps/` and `research/`: derived markdown + an append-only log + an index.

This is where the agent reflects beyond its current capabilities and authors the next ones. It is
the counterpart to `pm/` (which is **human-owned**): `pm/` holds ratified PRDs/plans/ADRs; here the
agent originates the ideas that may graduate into `pm/`.

```
proposals/
├── README.md       # this file
├── VISION.md       # living north-star — the agent's evolving thesis on what would make this great
├── LEDGER.md       # index of every proposal + its lifecycle status
├── horizon.jsonl   # append-only raw daily ideation log (one object per envision pass)
└── <YYYY-MM-DD>-<slug>.md   # one RFC per surfaced proposal
```

- **What runs here:** `skills/envision` authors RFCs + updates `VISION.md`/`LEDGER.md`/`horizon.jsonl`.
  `skills/enact` implements ≤1 `self_approved`, denylist-clean proposal per Sunday and records the
  result back into the RFC + ledger.
- **The autonomy envelope** (what may be self-implemented vs. what needs a human) is defined in
  `config/autonomy.md` — the human-owned constitution. The agent cannot edit it.
- **Veto:** the supervisor stops any change by `git revert`, by setting a ledger `status` to
  `vetoed`/`declined`, or by direction. There is no inbound message channel.
