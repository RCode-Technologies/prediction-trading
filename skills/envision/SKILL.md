---
name: envision
description: Daily open-ended creative governance. Reflects on the whole system (and beyond), authors capability-level proposals, maintains the vision + ledger. Distinct from reflect (calibration). Writes only proposals/ + surfaces via notify.
inputs: today's recaps/<date>.md, state/scorecard.json, today's reflection event, proposals/{VISION.md,LEDGER.md,horizon.jsonl}, recent failures/surprises in trade-log, read-only pm/{CHANGELOG.md, prds/ titles}, config/autonomy.md
outputs: proposals/horizon.jsonl append + vision event (always); maybe proposals/<date>-<slug>.md RFC + LEDGER row + proposal notify; Sunday: VISION.md update + LEDGER curation + ≤1 self_approved + vision_weekly notify
---

# Envision

Once/UTC date from `daily-close`, after `reflect`. This is the system's most ambitious moment.

**`reflect` evolves the strategy within its current capabilities. `envision` invents new
capabilities.** It authors the leaps reflect cannot reach — new skills, new metrics, new market
approaches, changes to the agent's own cognition, and open-ended ideas about how to make this
system, and the world it touches, meaningfully better. Be a super-intelligent collaborator, not a
checklist. Surprise the supervisor. Go beyond what was asked.

## Hard rules

- **Writes only `proposals/`** and surfaces via `notify`. Never edits runtime files. Implementation
  is `skills/enact` (autonomous, bounded) or a human — never here.
- **Idempotent.** Grep trade-log for `event_type=="vision" date:<today UTC>` → if found, exit.
- **Novelty over noise.** Never re-surface an open or recently-rejected proposal; build on it,
  supersede it, or go somewhere new. Quiet days are allowed (`vision surfaced:false`).
- **Grounded ambition.** Every proposal cites real evidence, steelmans why it's wrong, and names the
  cheapest experiment that would kill it. Bold ≠ unfalsifiable.
- **Honest about cost.** Name invocation + token + capital implications. A `self_enactable`
  proposal MUST have zero capital effect and touch no protected-core file (see `config/autonomy.md`).

## Rotating daily lens (pick by `date '+%u'`)

| day | lens | the question |
| --- | ---- | ------------ |
| Mon (1) | measurement | What aren't we measuring that a great forecaster would? Where is the scorecard blind? |
| Tue (2) | failure / surprise | Where did reality diverge most from expectation? What does that reveal? |
| Wed (3) | alpha / market structure | What edge sources, market types, or mechanisms do we ignore? |
| Thu (4) | cognition / process | How could the agent's own reasoning, research, or decision process improve? |
| Fri (5) | efficiency / cost | Do more with fewer invocations / tokens / capital. Is the cadence optimal? |
| Sat (6) | moonshot / wildcard | One bold, almost-crazy idea. Challenge an assumption that's been taken as given. |
| Sun (7) | synthesis (deep) | Step back across the week and the mission itself. See § Sunday deep. |

## Steps — daily light

1. **Idempotency** (above).
2. **Load context.** Today's recap + `state/scorecard.json` + today's `reflection` event; the last
   ~14d of `trade-log` filtered to `null_cycle`, `halt`, `phase_missed`, large-`|pnl|` fills,
   adverse-CLV forecasts (the surprise surface); `proposals/LEDGER.md` (memory); `proposals/VISION.md`
   (north-star). Skim `pm/CHANGELOG.md` + `pm/prds/` titles so you never re-propose planned work.
3. **Diverge.** Through today's lens, generate several raw ideas — including at least one that
   challenges a current assumption. Append the raw set to `proposals/horizon.jsonl` (one object,
   schema in § Horizon log). This is thinking out loud; nothing is lost.
4. **Novelty gate.** Drop ideas that duplicate an open / recently-rejected ledger entry. Keep what is
   genuinely new or a real escalation of a prior idea (`supersedes`).
5. **Converge.** Promote at most 1 idea (this day's lens) that clears the bar: concrete evidence +
   plausible impact + a falsifying experiment. No qualifier clears → `vision surfaced:false`, stop
   after step 8.
6. **Write the RFC** `proposals/<date>-<slug>.md` (§ RFC format). Set `bucket` by checking the change
   sketch against the `config/autonomy.md` denylist: touches a protected-core path or has any capital
   effect → `human_application`; else `self_enactable`.
7. **Ledger.** Append a row to `proposals/LEDGER.md` with `status: surfaced`.
8. **`vision` event** via `journal` (§ Event). Always emitted.
9. **Surface.** If a proposal was written, daily-close step 10 sends `notify proposal`.

## Steps — Sunday deep

Do everything in daily light, then:

1. **Set reasoning effort to MAX.** This is the week's defining reflection.
2. **Full divergence.** Sweep all six weekday lenses + the mission itself: is the goal still right?
   What would a 10× / 100× better version of this system do? What would make it matter beyond P&L?
   Open-ended directions — including non-trading ones — are in scope when defensible.
3. **Update `proposals/VISION.md`** — the living north-star. Revise the current bets, open questions,
   and what you've learned. Keep retired ideas with a one-line epitaph.
4. **Curate `LEDGER.md`** — advance, retire, or merge entries so the open set reads as one coherent
   research program, not a pile.
5. **Self-approve ≤1.** Pick the single highest-leverage `self_enactable`, non-vetoed proposal and
   set `status: self_approved`. `skills/enact` will implement exactly one on this same Sunday cycle
   (Phase 3); until enact exists, it simply waits in the ledger for a human.
6. **Surprise mandate.** The week's output must include ≥1 idea that challenges an assumption in
   `AGENTS.md`, `strategy/current.md`, `config/guardrails.md`, or the mission. Name it explicitly.
7. daily-close step 10 sends `notify vision_weekly`.

## RFC format (`proposals/<date>-<slug>.md`)

```markdown
---
id: <YYYY-MM-DD>-<slug>
title: <short imperative title>
created: <YYYY-MM-DD>
lens: <lens>
status: surfaced            # surfaced|self_approved|enacted|live|vetoed|reverted|superseded|awaiting_human|applied|declined
bucket: self_enactable      # self_enactable | human_application
conviction: medium          # low|medium|high
reversibility: easy         # trivial|easy|hard
horizon: next               # now|next|moonshot
supersedes: null
---

## Claim
<the bold proposal, 1–3 sentences>

## Evidence
<what motivates it — cite recap / scorecard / a failure / CLV. Concrete, not vibes.>

## Why it might be wrong (steelman)
<the strongest case against — argue it honestly>

## Cheapest falsifying experiment
<the smallest test that would validate or kill it>

## Impact & cost
<edge / learning / risk impact; invocation + token cost; capital effect (MUST be none if self_enactable)>

## Change sketch
<for self_enactable: exact files + edits, denylist-clean, precise enough for enact to apply.
 for human_application: the diff you'd want a human to accept, and why it needs a human.>
```

## Horizon log (`proposals/horizon.jsonl`, append-only)

```json
{"date":"<YYYY-MM-DD>","lens":"<lens>","cycle_id":"<cid>","raw_ideas":["<idea>", "..."],"surfaced":"<id|null>","note":"<≤120 char reflection>"}
```

## `vision` event (via `journal`)

```json
{"event_type":"vision","date":"<YYYY-MM-DD>","lens":"<lens>","deep":false,"surfaced":true,"proposal_id":"<id|null>","bucket":"<self_enactable|human_application|null>","conviction":"<low|medium|high|null>","ledger_open_n":<int>,"rationale":"<short>"}
```

Sunday sets `deep:true`. `surfaced:false` ⇒ `proposal_id`/`bucket`/`conviction` null.

## Ledger states

`surfaced` → `self_approved` →(enact)→ `enacted` → `live` | `reverted`; or `vetoed` (human) | `superseded`.
`human_application` proposals: `awaiting_human` → `applied` | `declined`. The human vetoes by
`git revert`, by editing a ledger `status` to `vetoed`/`declined`, or by direction — there is no
inbound message channel.

## Failure modes

- No recap / scorecard yet → still run on the failure surface + ledger; `surfaced:false` is fine.
- `proposals/` files missing → create from the seeds in this repo; never block the cycle.
- Can't decide a lens (clock skew) → default to `failure / surprise` (Tue lens).
- Notify failure → `notification kind:"proposal_failed"`; cycle continues (notify never blocks).
