---
version: v3
created: 2026-05-24
last_edited: 2026-05-29
owner: agent
---

# Strategy v3 — Self-Bootstrapping Action-Biased Learner

Agent-owned. Edited only by `skills/reflect`. Snapshotted to `strategy/history/` on every edit.

v3 separates **learning** (forecast broadly, pay nothing) from **earning** (bet rarely, only past the edge gate). The two content cycles emit a broad forecast-only batch each; only gate-passers risk capital. The v2 cold-start device (≥3 mandatory ε-probes/cycle) is retired — it manufactured noise. See pm/prds/v3-edge-and-learning.md.

## Decision rules

- **Phase:** Observation auto-flips off in `skills/boot` at `observation_started_at + observation_hours`. Post-obs:
  - `exploit` — thesis-driven, risks capital. Allowed **only** past the edge gate (§ Edge gate). Any miss → forecast-only.
  - `explore` — forecast-only (no fill). The default for everything that isn't a gate-passer.
  - `risk_reduction` — reserved; auto-SELL path lands in Phase 5.
- **Edge gate (the binding exploit gate):** an exploit fill requires ALL of `resolution_parsed == true` ∧ `reference_class != null` ∧ `len(source_providers) >= 2` ∧ `edge_net >= net_edge_floor` (300 bps, measured on `edge_net` — net of spread, **not** midpoint distance). Any miss → forecast-only `explore`, with `decision reason ∈ {resolution_unparsed, no_reference_class, insufficient_sources, edge_below_net_threshold}`. See § Edge gate + § Net edge.
- **Sizing:** fractional Kelly `f=0.25`, cap 5% NAV/token. `sizing_tier` default `0` (the tier ladder lands in Phase 5). Forecast-only entries pinned to 0 notional / 0 shares.
- **Forecast target** (daily, routine-aware; enforced by `skills/persist` audit per phase):
  - research_window: ≥1 research_note, ≥1 candidate_rank, **broad forecast-only batch** (~4–6).
  - trade_window: **broad forecast-only batch** (~4–6); gate-passers (expected 0–2/day) become bets.
  - Combined daily target ~8–12 forecasts; only gate-passers risk capital.
  - daily_close: ≥1 recap, ≥1 reflection.
  - overnight_watch: ≥1 nav_snapshot.
  - pulse / other cycles: emit **no** new forecasts (snapshot only).
  - Floor miss (no forecasts emitted in a content cycle) → `null_cycle` (still pushed, flagged).
  - NOTE: the AGENTS.md "Action commitment" mirror still shows the v2 rigid `≥3 forecast` floor — it is synced by the orchestrator in Phase 6.
- **Market filter:** Gamma `liquidityNum >= 2000`, `endDate <= 90d`, two-sided book, midpoint ≤15min.
- **Discovery:** universe-first (`state/universe.jsonl` daily cache, then attach research signals).

## Probability + sizing

### Net edge (the only edge that counts)

You **buy at the ask, sell at the bid** — midpoint is never the trade price (`skills/trade`, `skills/markets`). So the sole edge measure for a YES BUY is net of spread:

```
edge_net = your_p - best_ask        # YES BUY (executable_price)
```

(`best_ask` from `markets.book()`. SELL-side symmetry: `your_p` vs `best_bid`.) `edge_net` is what the net-edge floor is measured against — an exploit fill must clear the **net-edge floor (300 bps / 0.03)** *after* spread, not midpoint distance. Midpoint stays only as a reference mark and for Kelly payout odds. The net-floor is one of four conjuncts in the binding § Edge gate below.

### Edge gate (binding; exploit only)

The lesson of the 2026-05-27 Iran trade: the edge was **unverifiable**, not merely thin. So the gate blocks on *provenance*, not just magnitude. An **exploit** fill is allowed only if ALL hold:

```
resolution_parsed == true           # Gamma `description` fetched + parsed into resolution_criteria
reference_class    != null          # a NAMED base-rate class…
len(source_providers) >= 2          # …backed by ≥2 independent sources
edge_net           >= 0.03          # net-of-spread edge clears the 300 bps floor
```

Any miss → **forecast-only** (`learning_intent` demoted to `explore`), emit a `decision` with `reason ∈ {resolution_unparsed, no_reference_class, insufficient_sources, edge_below_net_threshold}` and `shares:0`. `skills/sizing` is the enforcement point; `skills/research` pre-screens (a thesis missing parsed `description` or a ≥2-source reference class is demoted to explore-only before sizing). `sizing_tier` is assigned `0` here (the conviction ladder is Phase 5).

> The Iran inputs (single source, invented "0.45–0.55" base rate, `description` never parsed) fail three conjuncts — `resolution_unparsed`, `no_reference_class`, `insufficient_sources` — even though `edge_net ≈ 7pp` cleared the net floor. Magnitude alone would have passed it; provenance is what blocks it.

### Exploit path

`market_p` = fresh midpoint (reference). Executable buy price = `best_ask`. Research → `raw_your_p`. Calibration adj → `your_p`.

Cold-start fallback (exploit bucket `resolved_n < 10`): if `raw_your_p == market_p`, nudge `your_p = clamp(market_p + sign(thesis_direction) * 0.01, 0.02, 0.98)`. **`your_p == market_p` on exploit path is forbidden** (dead-loop signal).

```
edge_net         = your_p - best_ask              # net of spread (executable)
kelly_fraction   = edge_net / (1 - best_ask)       # cost-honest: edge & odds at the ask
notional         = clamp(0.25 * kelly_fraction * NAV, 0, 0.05 * NAV)
```

Fill only if the full § Edge gate passes (provenance conjuncts + `edge_net >= 0.03`). Any miss (or Kelly ≤ 0) → forecast-only, demoted to `explore`.

### Explore path (forecast-only — the default)

Every candidate that doesn't clear the § Edge gate is `explore`: a genuine forecast that risks **no capital**. This is the broad learning batch the two content cycles emit (target ~8–12/day combined). Use your honest estimate, not a synthetic offset:

```
your_p   = your genuine estimate (research-informed where available, else market_p ± small judgment nudge)
notional = 0, shares = 0
edge_source = best applicable tag (news_latency|base_rate|structural|sentiment), else "none"
```

A demoted exploit (gate miss) lands here too, tagged with its gate-miss `reason`. Always emits `forecast`; never `paper_fill` / `mainnet_order_submitted`. (The v2 ε-rank probe device is retired — see § Changelog.)

## Forecast attribution (mandatory fields)

`strategy_version`, `forecast_id`, `thesis_id`, `evidence_refs`, `feature_tags`, `source_providers`, `prior_p`, `raw_your_p`, `your_p`, `market_p`, `confidence`, `calibration_bucket`, `close_time`, `resolution_criteria`, `disconfirming_signals`, **`learning_intent ∈ {"explore","exploit","risk_reduction"}`**.

**v3 gate/cost fields (mandatory; see `skills/journal` for the schema):** `resolution_parsed` (bool), `reference_class` (named base-rate class, nullable), `edge_source` (tag ∈ {`news_latency`,`base_rate`,`structural`,`sentiment`,`none`}), `best_bid`, `best_ask`, `spread`, `edge_net`, `sizing_tier` (int 0–3; default `0` until the Phase 5 ladder). Exploit forecasts MUST have `resolution_parsed:true` + non-empty `resolution_criteria` + `reference_class != null` + `source_providers` len ≥ 2; explore forecasts may carry `reference_class:null`, `edge_source:"none"`.

## Calibration ledger (sliced by `learning_intent`)

Exploit metrics drive sizing; explore metrics drive bucket population only.

### Exploit

| bucket | resolved_n | brier | hit_rate | adjustment | status  |
| ------ | ---------: | ----: | -------: | ---------: | ------- |
| 50-60  |          0 |   tbd |      tbd |       0.00 | collect |
| 60-70  |          0 |   tbd |      tbd |       0.00 | collect |
| 70-80  |          0 |   tbd |      tbd |       0.00 | collect |
| 80-90  |          0 |   tbd |      tbd |       0.00 | collect |

### Explore

| bucket | resolved_n | brier_explore | brier_market_p | calibration_slope | status  |
| ------ | ---------: | ------------: | -------------: | ----------------: | ------- |
| 30-40  |          0 |           tbd |            tbd |               tbd | collect |
| 40-50  |          0 |           tbd |            tbd |               tbd | collect |
| 50-60  |          0 |           tbd |            tbd |               tbd | collect |
| 60-70  |          0 |           tbd |            tbd |               tbd | collect |
| 70-80  |          0 |           tbd |            tbd |               tbd | collect |

## Hypothesis registry

Statuses: `watch` (full sizing), `probation` (mult 0.5), `demoted` (excluded until `next_retry_date`), `retired`.

| thesis/tag                  | status  | evidence_n | sizing_mult | next_retry_date | note                                              |
| --------------------------- | ------- | ---------: | ----------: | --------------- | ------------------------------------------------- |
| base-rate-anchored-research | watch   |          0 |        1.00 | n/a             | Name a base rate before news adjustments.         |
| closing-line-value          | watch   |          0 |        1.00 | n/a             | Midpoint drift = interim signal, not truth.       |
| thin-book-drift             | caution |          0 |        1.00 | n/a             | Need fresh two-sided quotes; drop thin-book.      |
| correlated-news-markets     | caution |          0 |        1.00 | n/a             | Same fact = same bucket; uncertain = reject.      |
| explore-rank1-epsPos        | retired |          0 |        0.00 | n/a             | v2 ε-probe; retired in v3 (forecast-batch policy). |
| explore-rank2-epsZero       | retired |          0 |        0.00 | n/a             | v2 ε-probe; retired in v3.                         |
| explore-rank3-epsNeg        | retired |          0 |        0.00 | n/a             | v2 ε-probe; retired in v3.                         |

## Source-quality ledger

Rolling 30d Brier vs market baseline per provider (exploit slice only).

| provider | resolved_n | brier_provider | brier_market_p | penalty | status |
| -------- | ---------: | -------------: | -------------: | ------: | ------ |
| (collect)                                                                       |

## Pending evidence

- Target ~30 resolutions across explore buckets within 30 days of v2 deploy.
- Once any explore bucket hits `resolved_n >= 10`, flag if `|slope - 1.0| > 0.15` (market mispricing signal).
- Compare exploit forecasts (when they exist) vs explore baselines to validate thesis beats ε-noise.

## Smartness scorecard (read from `state/scorecard.json`)

`skills/recalibrate` keeps it fresh. Schema:
- `exploit.{brier_agent, brier_market_p, brier_skill, calibration_slope, calibration_intercept, auc, kl_vs_market, drift_skill, clv_mean, clv_hit_rate, clv_n, resolved_n, unresolved_n}`
- `explore.{brier_explore, brier_market_p, calibration_slope, buckets_filled, clv_mean, clv_hit_rate, clv_n, resolved_n, unresolved_n}`
- `by_edge_source[]`, `by_provider[]`, `by_feature_tag[]`

### CLV is the headline metric (while `resolved_n < 30`)

Resolution Brier is the slow ground truth — at multi-week close times it is **months** from significance, so it is reported as **"pending ground truth"** and does not drive any decision until `resolved_n >= 30`. The **headline skill metric is closing-line value (CLV)**: does the market move *toward* our forecast after we make it?

```
clv = (market_p_later - market_p_t0) * sign(your_p - market_p_t0)   # >0 ⇒ market moved our way
```

- Snapshotted by `skills/recalibrate.snap_clv()` at **+6h / +24h / close** on every pulse, overnight-watch, and daily-close — no Gamma, no new forecasts, no added invocations. Non-null once any forecast has aged ≥6h.
- `clv_mean` / `clv_hit_rate` are tracked **per `learning_intent`** and **per `edge_source`** (`by_edge_source[]`) — this is what tells us *which signal* is generating edge weeks before Brier can.
- `drift_skill` is the legacy single-number seed; once `clv_n > 0`, `clv_mean` supersedes it.
- Recaps + reflection lead with CLV while `resolved_n < 30`; Brier shown alongside as "pending ground truth." Positive CLV is *speed-of-learning* evidence, not P&L — the § Edge gate + liquidation marks still decide whether to bet (CLV can be positive while paying the spread loses money).

## Convergent calibration update law

Per **exploit** bucket with `resolved_n >= 10`:
```
shrink     = min(1.0, resolved_n / 30)
adjustment = clamp(shrink * (hit_rate - bucket_midpoint), -0.08, +0.08)
your_p     = clamp(raw_your_p + bucket_adjustment, 0.02, 0.98)
```

Explore buckets compute `adjustment` diagnostically; never feed back into exploit sizing.

## Reflection-quality gate

Refuse v(N+1) if `exploit.brier_skill_after < brier_skill_before - 0.005` on trailing 14d. Risk-tightening edits bypass.

**v2 cold-start carve-out:** when trailing-30d `exploit.resolved_n < 5`, gate operates on `explore.calibration_slope` instead.

## Auto-revert

`last_good_version` = highest historical version whose 30d `exploit.brier_skill > max_brier_skill - 0.01`. If last 3 `reflection` events all have `brier_skill < last_good.brier_skill`, next reflection MUST revert: copy snapshot to `current.md`, bump version, snapshot failed run, emit `reflection edited:true reason:"auto_revert" reverted_to:"<vN>"`.

## Hypothesis retry policy

Demote → `next_retry_date = today + 14d`. On/after date → `probation, sizing_mult:0.5`, clear date. After 5 probation resolutions: `brier_skill > 0` → `watch, mult:1.0`; else re-demote `+14d`. Exploit theses only; explore probes never demote.

## Source-quality penalty

`brier_provider > brier_market_p + 0.03` over `resolved_n >= 8` (exploit) → `penalty:0.5, status:penalized` (sizing applies `confidence *= 0.5` to citing forecasts). Lifts after 5 resolved cite-events restore `brier_provider <= brier_market_p`.

## Forecast batch policy (replaces the v2 ε-probe floor)

`trade-window` and `research-window` each emit a **broad forecast-only batch** (~4–6 each, ~8–12/day combined) over the top ranked candidates. Every entry is `explore` (forecast-only) unless it clears the § Edge gate, in which case it becomes an `exploit` bet (expected 0–2/day). Pulse / other cycles emit **no** new forecasts.

- Forecast your honest `your_p` per candidate; no synthetic ε offset. Tag each with `edge_source`.
- Never duplicate a market that already has any forecast this cycle. Dedupe key: `paper:<market_id>:<token_id>:explore:<UTC-date>`.
- No fixed numeric hard floor per cycle; the daily routine-aware target governs (see § Decision rules → Forecast target). A content cycle that emits zero forecasts is a `null_cycle`.

## Smartness threshold (human hint)

OLS slope of daily `brier_skill` over 30d negative for 14 consecutive UTC dates → `risk.surface_recommendation()` with candidate tightenings. Reflection surfaces; humans own guardrails.

## Reflection notes

(Updated by `skills/reflect`. v2 starts empty.)

## Changelog

- v3 — 2026-05-29 — cost-honest accounting, edge gate, CLV, risk doctrine (see pm/prds/v3-edge-and-learning.md). Phase 1: liquidation-priced fills/marks + `edge_net`. Phase 2: binding edge gate (provenance conjuncts + net-floor), forecast/trade split, new mandatory fields (`resolution_parsed`, `reference_class`, `edge_source`, `best_bid`/`best_ask`/`spread`/`edge_net`, `sizing_tier`), v2 ε-probe floor retired for a daily routine-aware forecast target. Phase 3 (this edit, scorecard section only): CLV promoted to headline skill metric while `resolved_n<30` (Brier "pending ground truth"); scorecard gains `clv_mean`/`clv_hit_rate`/`clv_n` per intent + `by_edge_source[]`, snapshotted on pulse/overnight-watch/daily-close (zero added invocations). Snapshot: `strategy/history/2026-05-29-v2.md`.
- v2 — 2026-05-26 — cold-start deadlock fix: mandatory exploration, `learning_intent` taxonomy, sliced calibration ledger, action commitment per cycle, relaxed filter (liq≥2000, end≤90d), universe-first discovery. Snapshot: `strategy/history/2026-05-26-v1.md`.
- v1 — 2026-05-24 — self-learning contract, attribution fields, smartness gates. Snapshot: `strategy/history/2026-05-24-v0.md`.
- v0 — 2026-05-24 — observation-only seed.
