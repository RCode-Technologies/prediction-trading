# `preflight_failed`

Sent by `skills/trade` when a mainnet preflight gate rejects the cycle. `<reason>` must never echo env-var values, wallet addresses, or token-bearing URLs.

```
⚠️ *Preflight failed* · `<mode>`

Check
  *<check>*
Reason
  <brief reason — no secrets>
```
