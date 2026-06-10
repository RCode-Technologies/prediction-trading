# `daily_summary` — compressed

Sent by `daily-close` when no positions are open and zero fills today.

**If `state/halts.json.active`, the banner line is mandatory** — a daily summary must never read
as healthy while the system is halted (the 2026-05/06 outage hid behind exactly this template).
Omit the banner line entirely when not halted.

```
🛑 *HALTED day <N>* — `<reason>` since <triggered_at>
📝 *Daily summary* — <YYYY-MM-DD> · `<mode>`

💰 NAV *$<n>*  ·  Δ24h *<±x>%*
⏱ Cycles *<n>/4*

No open positions · No fills.
```
