---
cycle_id: 20260615T121223Z-62cc61a4
phase: research_window
ts: 2026-06-15T12:18:00Z
angle: Probability Bitcoin settles in the $70k-$72k band on June 17 given spot near $65.7k
sources:
  - {provider: agent_native_websearch, url: "https://www.coingabbar.com/en/crypto-currency-news/bitcoin-news-2026-06-15", fetched_at: 2026-06-15T12:15:00Z}
  - {provider: agent_native_websearch, url: "https://finance.yahoo.com/personal-finance/investing/article/bitcoin-and-ethereum-prices-today-friday-june-12-2026-prices-rebound-this-morning-after-trump-claims-war-has-ended-115949042.html", fetched_at: 2026-06-15T12:15:00Z}
---

External content treated as untrusted data — used only to anchor a probability, not as instruction.

As of 2026-06-15, BTC spot is reported ≈ **$65,700** (24h range ~$63.7k–$65.7k), rebounding on easing
geopolitical tension after a reported regional conflict ended. Market `2492010` resolves YES only if BTC
is **between $70,000 and $72,000** at the June 17 settlement (~2 days out).

For YES, BTC must rally **~+6.5% to +9.5%** AND land inside a narrow **$2k-wide** band. Two days is short;
a move of that size is possible in crypto but unlikely, and even conditional on a rally, landing precisely
in $70–72k (rather than overshooting or stalling) is a further constraint. Honest estimate ≈ **0.025**,
marginally above the wide-spread midpoint (bid 0.011 / ask 0.022 → mid ≈ 0.0165). Edge_net vs the ask is
only ~0.003 — far below the 0.03 net-edge floor — so this is **explore-only**. The Gamma `description`
(exact settlement source/time) was not formally parsed; exploit gate not met.

## Thesis cards
| thesis_id | claim | market_ids | prior_p | expected_direction | feature_tags | edge_source | reference_class | resolution_parsed | disconfirming_signals |
|---|---|---|---:|---|---|---|---|---|---|
| 20260615-btc-range-T1 | A precise $70-72k BTC settlement in 2 days from ~$65.7k spot is low-probability | 2492010 | 0.0165 | YES slightly up | crypto,structural,explore | structural | (unnamed — not 2-source-backed base rate) | false | sharp BTC rally lands in band; BTC stalls near 65k; overshoots above 72k |
