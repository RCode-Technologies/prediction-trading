# `daily_summary` — full

Sent by `daily-close` when positions are open or fills occurred today. Swap 📈 ↔ 📉 on the NAV line when Δ24h is negative; omit the movers block if no positions.

**If `state/halts.json.active`, the banner line is mandatory** — a daily summary must never read
as healthy while the system is halted. Omit the banner line entirely when not halted.

```
🛑 *HALTED day <N>* — `<reason>` since <triggered_at>
📝 *Daily summary* — <YYYY-MM-DD> · `<mode>`

💰 NAV *$<n>*  ·  Δ24h 📈 *<+x>%*
⏱ Cycles *<n>/4*
🎯 Forecasts *<n>* · Paper fills *<n>* · Mainnet fills *<n>*

📂 *Open positions* (<n>)
💵 Cash *$<n>*

🔝 *Top movers*
  • <market>  📈 *<+x>%*
  • <market>  📉 *<-x>%*
```
