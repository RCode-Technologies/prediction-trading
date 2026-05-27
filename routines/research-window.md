---
name: research-window
cron: "0 12 * * *"
cron_tz: UTC
local_time: "07:00 ET"
phase: research_window
expected_frequency: 1/day
---

# Research Window — 12:00 UTC / 07:00 ET

Heaviest research routine. **Floor: ≥1 `research_note`, ≥1 `candidate_rank`, ≥3 `forecast`.**

## v2 flow: universe-first

Universe → identify targets → targeted research → attach signals → watchlist + forecasts (incl. mandatory probes). Avoids v1's empty intersection.

## Steps

1. **Set reasoning effort to MAX** — this drives downstream trade-window decisions.
2. `boot`
3. `circuit-breaker.evaluate()` — cp1. Halted → jump to 12.
4. **Universe refresh.** `state/universe.jsonl` missing or `cached_at < now - 24h` → run `markets.universe()` (1 Gamma source). Else load cache.
5. **Identify targets.** Top 10-15 universe markets by `category` × liquidity. Derive a short angle per target. Budget reserved: 2 (research) + 1 (universe if refreshed).
6. `research` — targeted lookups by market question. ≤2 sources (Brave/Tavily/Serper → native WebSearch/WebFetch → Polymarket-only). Each thesis card MUST set `market_ids` for `attach_signals` join.
7. `markets` — `attach_signals` + `rank`. Slate mix of exploit-eligible + exploration-fallback candidates.
8. **Build forecast slate (≥3 mandatory)** — same algorithm as `trade-window` step 6.
9. `sizing` per slate entry. Exploit may fill (post-obs); explore is forecast-only.
10. `trade` for exploit decisions with `shares > 0`. Mainnet rare here (trade-window owns it).
11. **Self-audit.** Count `forecast` (`<3` → `null_cycle reason:"forecast_floor_missed"`), `research_note` (`<1` → null_cycle), `candidate_rank` (`<1` → null_cycle). Notify on any.
12. `journal.phase_completed forecasts:<N>, research_notes:<N>, candidate_rank:<N>, slate_composition`.
13. `notify discovery_summary`. `null_cycle` if emitted (suppression-exempt).
14. `persist`.

## Source budget

3 max/cycle. Typical: 1 (universe) + 2 (research) = 3.

## Output artifacts

- `state/universe.jsonl` (refreshed daily)
- `research/YYYY-MM-DD/<slug>.md` per thesis
- `research/YYYY-MM-DD/watchlist.md` (top 5 + slate composition)

## Trade behavior

- Paper obs: forecast-only on both paths (sizing's observation short-circuit).
- Paper post-obs: exploit may fill; explore stays forecast-only.
- Mainnet: not prioritized; trade-window owns it.

## Failure modes

- Gamma down AND universe cache stale → `null_cycle reason:"no_market_data"`.
- All research providers error → Polymarket-only; explore probes still emit (don't need news).
- 0 exploit candidates → fine. Explore fills.
- < 3 forecasts → `null_cycle reason:"forecast_floor_missed"` (cycle still persists).

## Notify

`discovery_summary` paper + mainnet (slate composition, top thesis). For explore-only cycles: name the 3 probed markets and their ε. `null_cycle` suppression-exempt.

## Commit

Per `skills/commit` § Routine-mapped subjects. Body: slate composition, sources used, notifications. One commit.
