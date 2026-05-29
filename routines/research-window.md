---
name: research-window
cron: "0 12 * * *"
cron_tz: UTC
local_time: "07:00 ET"
phase: research_window
expected_frequency: 1/day
---

# Research Window — 12:00 UTC / 07:00 ET

Heaviest research routine. **Target (v3): ≥1 `research_note`, ≥1 `candidate_rank`, a broad forecast-only batch (~4–6; combined daily target ~8–12 with trade-window).** Only gate-passers risk capital. Emitting **zero** forecasts is a `null_cycle`. (The AGENTS.md "Action commitment" mirror still shows the v2 rigid `≥3 forecast` floor — orchestrator syncs it in Phase 6.)

## v3 flow: universe-first, forecast-many / bet-few

Universe → identify targets → targeted research (parse resolution `description` + name reference class for any exploit candidate) → attach signals → watchlist + broad forecast-only batch; only § Edge-gate passers go through `trade`.

## Steps

1. **Set reasoning effort to MAX** — this drives downstream trade-window decisions.
2. `boot`
3. `circuit-breaker.evaluate()` — cp1. Halted → jump to 12.
4. **Universe refresh.** `state/universe.jsonl` missing or `cached_at < now - 24h` → run `markets.universe()` (1 Gamma source). Else load cache.
5. **Identify targets.** Top 10-15 universe markets by `category` × liquidity. Derive a short angle per target. Budget reserved: 2 (research) + 1 (universe if refreshed).
6. `research` — targeted lookups by market question. ≤2 sources (Brave/Tavily/Serper → native WebSearch/WebFetch → Polymarket-only). Each thesis card MUST set `market_ids` for `attach_signals` join. **Exploit candidates** MUST parse the Gamma `description` into `resolution_criteria` (`resolution_parsed:true`) + name a `reference_class` backed by ≥2 sources, else they are demoted to explore-only (`skills/research` gate).
7. `markets` — `attach_signals` + `rank`. Slate mix of exploit-eligible + explore-only candidates; gate fields carried forward.
8. **Build broad forecast-only batch (~4–6)** — top ranked candidates. Default `learning_intent:"explore"` (forecast, no capital); a candidate becomes an exploit only if it clears the § Edge gate in `sizing`. Tag every forecast with `edge_source`. Never duplicate a market within the cycle.
9. `sizing` per slate entry — emits a `forecast` for all; the **edge gate** (provenance conjuncts + `edge_net ≥ 0.03`) decides exploit-vs-explore. Post-obs, only gate-passers produce a sized `decision`; all else is forecast-only with a gate-miss `reason`.
10. `trade` for **gate-passing** exploit decisions with `shares > 0`. Mainnet rare here (trade-window owns it).
11. **Self-audit.** Count `forecast` (`0` → `null_cycle reason:"forecast_floor_missed"`), `research_note` (`<1` → null_cycle), `candidate_rank` (`<1` → null_cycle). Notify on any.
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
- All research providers error → Polymarket-only; explore forecasts still emit (don't need news).
- 0 exploit (gate-passing) candidates → fine, and expected most days. The forecast-only batch still emits.
- 0 forecasts emitted → `null_cycle reason:"forecast_floor_missed"` (cycle still persists).

## Notify

`discovery_summary` paper + mainnet (slate composition, top thesis, `N_exploit + N_explore`). Explore-only cycles: name a few of the forecast-only markets + their `edge_source`. `null_cycle` suppression-exempt.

## Commit

Per `skills/commit` § Routine-mapped subjects. Body: slate composition, sources used, notifications. One commit.
