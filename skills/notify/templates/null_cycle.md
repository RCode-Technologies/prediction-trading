# `null_cycle`

One message per routine that missed its action floor.

```
🚨 *Null cycle* · `<mode>`

Phase
  *<phase>*
Floor missed
  <missed_floors>
Actual
  forecast=<n>, research_note=<n>, candidate_rank=<n>
Cycle
  `<cycle_id>`
```

Notes:
- A `null_cycle` is auditable evidence, NOT a halt. The cycle still pushed.
- Investigate: was the universe empty? Was Gamma down? Did `sizing` reject every candidate?
- If null cycles repeat 3+ days in a row, `reflect` should surface a guardrail recommendation.
