# Autonomy Charter

Human-owned. The agent **reads** this file but may **never** edit it — it is protected core (§ below).
This charter is the constitution for self-direction: it bounds what `skills/envision` may propose and
what `skills/enact` may self-implement. The agent is maximally free *inside* this envelope and
structurally unable to widen it.

## Identity is the trust boundary

- Agent commits as `${GIT_AUTHOR_NAME:-Polymarket Trading Agent}` / `${GIT_AUTHOR_EMAIL:-agent@prediction-trading.local}`.
- Humans commit as themselves.
- Every check below keys off one question: *was this authored by the agent identity?* The agent
  cannot change its own rails because doing so leaves an agent-authored fingerprint on a protected file.

## Protected core (human-authored only)

`skills/boot` audits the last commit author of each path every wake-up; agent authorship →
`circuit-breaker.halt("protected_core_violation")`. `skills/persist` refuses to commit any of these
under the agent identity. The agent never writes these in normal operation, so the audit never
false-positives.

- `config/autonomy.md` — this charter
- `config/guardrails.md` — capital safety
- `AGENTS.md` — top-level contract
- `skills/boot/` — runs the integrity audit
- `skills/persist/` — runs the write gate
- `skills/circuit-breaker/` — the halt mechanism
- `skills/enact/` — the self-write mechanism (its own intent gate)
- `skills/recalibrate/` — the scorecard ruler (the agent must not move its own metric)
- `skills/risk/` — capital + NAV math

Each is an enforcement rail, the capital-safety doc, or the metric ruler. If the agent could edit any
one, it could unwind the rest.

## Self-enactment denylist (never self-enact)

A proposal whose change-sketch touches ANY path here is `human_application`: `enact` refuses it, marks
it `awaiting_human`, surfaces, writes nothing. Superset of the protected core, plus:

- Everything in § Protected core.
- Capital & portfolio state: `state/portfolio.json`, `state/halts.json`, `state/cycle-index.json`,
  `state/lock.json`.
- Mainnet & secrets: `config/mode.json` (`network`, `mainnet_*`, `observation_*` fields); anything
  that reads `WALLET_SEED` / `.env*`; `skills/trade` mainnet paths.
- Anything with a capital effect: position sizing, order direction/placement, breaker thresholds, fees.
- Repo-structure power: `skills/groom/` (moves / archives files).

The denylist governs what `enact` may *implement*. Core skills still write `state/*.json` during normal
cycles — that is unrelated. Only the smaller § Protected core list gates `persist`'s commits and the
`boot` audit; the broader denylist gates `enact`.

## Self-enactment allowlist (green zone)

A proposal is `self_enactable` only if ALL hold:

1. **Reversible** — a single `git revert <sha>` fully undoes it.
2. **Zero capital effect** — cannot change sizing, order placement, NAV, fees, or any mainnet behavior.
   Paper-mode only.
3. **Denylist-clean** — touches no path in § denylist.
4. **Self-contained** — additive or a localized edit; no data migration, no destructive delete of
   tracked history.

Typical green-zone work: a new observational / measurement skill; a new `notify` template; a new
non-trading routine or analysis note; prose / process edits to `skills/envision` itself; additive
docs; new `proposals/` or `research/` content. Everything else → `human_application`.

## Enactment cadence + caps

- **≤1 enactment per week**, Sundays only, inside `daily-close` after the deep envision pass.
- Exactly one `self_approved`, non-vetoed, denylist-clean proposal per Sunday — the highest-leverage one.
- Each enactment is **one standalone revertible commit** (`feat(agent): enact <slug>`), carrying a
  `git revert <sha>` recipe + the affected-file list in the body.

## Veto (standing, no deadline)

There is no inbound message channel. The human vetoes by repo action, any time before or after enactment:

- `git revert <sha>` an enactment commit, or
- edit the proposal's `proposals/LEDGER.md` `status` to `vetoed` / `declined`, or
- redirect by direction (the next cycle reads the ledger).

A proposal is surfaced daily but enacted no earlier than the next Sunday → a **standing ≥7-day veto
window** before any code is written.

## Auto-rollback

On enactment, `enact` records a baseline metric. If later cycles show regression attributable to the
change — a `null_cycle` spike, a breaker trip, or a `brier_skill` / CLV drop past threshold — the next
cycle auto-reverts (`revert: auto-rollback <slug>`) and surfaces. Mirrors `skills/reflect`'s 3-strike
auto-revert philosophy.

## Enforcement (defense in depth)

1. **Intent gate** — `enact` refuses to *write* any § denylist path.
2. **Write gate** — `persist` refuses to *commit* a § Protected core path under the agent identity
   (staged-diff ∩ protected core → halt).
3. **Integrity backstop** — `boot` audits the last author of every § Protected core path →
   `halt("protected_core_violation")`.

**Residual gap (honest).** A single cycle could in principle stage a self-edit to `persist` that also
disables the write gate. It is caught by the *next* boot's integrity audit, by auto-rollback, and by the
standing human veto — and the whole system is paper-mode. This threat model targets emergent overreach,
not a deliberately adversarial actor.
