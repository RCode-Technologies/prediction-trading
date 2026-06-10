# `halt_active`

Sent by `boot` once per UTC date while `state/halts.json.active == true` (date-deduped,
suppression-exempt). This is escalation, not news: the system cannot clear its own halt, so it
nags daily until the human acts. Day count from `triggered_at`.

```
🛑 *HALT ACTIVE — day <N>* · `<mode>`

Reason
  *<reason>*
Since
  <triggered_at>

Capital actions stopped · calibration sweeps continue.
Resume: human clears `state/halts.json`
(see `skills/circuit-breaker` § Recovery).
```
