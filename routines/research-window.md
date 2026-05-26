---
name: research-window
cron: "0 12 * * *"
cron_tz: UTC
local_time: "07:00 ET"
phase: research_window
expected_frequency: 1/day
---

# Research Window — 12:00 UTC / 07:00 ET

US wake-up. Build today's watchlist. **Heaviest research routine** — most of the day's source budget spent here. **Action commitment: ≥1 `research_note`, ≥1 `candidate_rank`, ≥3 `forecast` events.**

## v2 flow: universe-first

Old (v1) flow ran research blind on a news angle, then queried Gamma for top-volume markets, then took the empty intersection. v2 reverses it:

1. Pull/refresh the liquid universe (`markets.universe()`, 24h cached).
2. Identify the universe's most actionable themes (top-N markets by category × liquidity).
3. Run **targeted** research keyed off those market questions — not blind news scraping.
4. Attach signals back to the universe.
5. Build the watchlist + emit forecasts (including mandatory exploration probes).

## Steps

1. **Set reasoning effort to MAX.** This is the day's most consequential routine; the watchlist built here drives every downstream trade-window decision.
2. `boot`
3. `circuit-breaker.evaluate()` — cp1. Halted → skip to 12.
4. **Universe refresh.** If `state/universe.jsonl` is missing or `cached_at < now - 24h`, run `markets.universe()` (costs 1 Gamma source). Else load from cache.
5. **Identify research targets.** From the universe, pick the top 10-15 markets by `category` diversity × liquidity. For each, derive a short research angle (e.g. "what's the latest polling on <market_question>?"). Sources reserved: 2 (research) + 1 (already spent on universe if refreshed).
6. `research` — run **targeted lookups** keyed off the chosen market questions, not a free-floating news angle. Budget ≤2 sources (external keys → native WebSearch/WebFetch → Polymarket only). Each thesis card MUST set `market_ids` field so `attach_signals` can join later.
7. `markets` — `attach_signals` + `rank`. Builds candidate slate from universe + research. Slate may have any mix of exploit-eligible (thesis-matched, `|your_p - market_p| >= 0.03`) and exploration-fallback (no thesis or sub-edge) candidates.
8. **Build forecast slate (≥3 mandatory).** Same algorithm as `trade-window` step 6:
   - Exploit slots first (cap 3).
   - Fill remaining slots with explore probes (`learning_intent:"explore"`, `explore_rank ∈ {1,2,3}`).
9. `sizing` per slate entry. Exploit candidates may produce paper fills post-observation; explore probes are forecast-only.
10. `trade` for any exploit decision with `shares > 0`. Research-window typically doesn't fire mainnet (that's trade-window's role) but paper fills are allowed.
11. **Self-audit.** Count `forecast` events this cycle. If `< 3`, append `null_cycle reason:"forecast_floor_missed"` and notify. Count `research_note` and `candidate_rank` too — those have their own floor of 1 each.
12. `journal.phase_completed` with `forecasts:<N>`, `research_notes:<N>`, `candidate_rank:<N>`, `slate_composition`.
13. `notify` — `discovery_summary` summarizing slate composition. If `null_cycle` was emitted, also send the `null_cycle` alert.
14. `persist`.

## Source budget

3 max/cycle. Typical: 1 (universe refresh) + 2 (targeted research) = 3.

## Output artifacts

- `state/universe.jsonl` (refreshed daily, persistent)
- `research/YYYY-MM-DD/<slug>.md` per thesis lookup
- `research/YYYY-MM-DD/watchlist.md` (top 5 with fresh marks + slate composition)

## Trade behavior

- Paper observation (`mode.observation_only==true`): forecast-only on both exploit and explore paths. Sizing's observation short-circuit handles this.
- Paper post-observation: exploit candidates fill at midpoint; explore probes remain forecast-only.
- Mainnet: not prioritized here (US news drops after 09:30 ET = `trade-window`). Execute only if strong, time-sensitive edge closes before 18:00 UTC.

## Failure modes

- Gamma down AND universe cache stale → `null_cycle reason:"no_market_data"`, exit clean after persist.
- All research providers error → continue on Polymarket-only; explore probes still emit (they don't need news).
- No exploit candidates → fine. Explore slate fills, ≥3 forecasts still emitted.
- < 3 forecasts emitted → `null_cycle reason:"forecast_floor_missed"`, cycle still persists for auditability.

## Notify

Send `discovery_summary` in paper and mainnet (concise: slate composition `N_exploit + N_explore`, top thesis if any). For exploration-only cycles, the summary names the 3 probed markets and their ε.

`null_cycle` alert sent in paper + mainnet whenever any floor is missed.

## Commit

- Normal: `feat(research): window <YYYY-MM-DD> [cycle <cid>]`
- Universe refresh + explore-only: `feat(research): window explore_only <N>fcsts [cycle <cid>]`
- Floor missed: `fix(cycle): null_cycle <reason> [cycle <cid>]`

Use a short commit body for slate composition, sources used, and notification status. Do not create a follow-up bookkeeping commit.
