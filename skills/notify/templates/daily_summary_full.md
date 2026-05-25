# `daily_summary` — full

Sent by `daily-close` when positions are open or fills occurred today. Swap 📈 ↔ 📉 on the NAV line when Δ24h is negative; omit the movers block if no positions.

```
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
