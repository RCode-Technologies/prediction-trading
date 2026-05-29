---
date: 2026-05-29
phase: v3 Phase 4 — Historical bootstrap + backtest
owner: builder (offline, supervised)
artifact: tools/bootstrap-calibration.json
script: tools/backtest.py
ran_live: true
status: complete
---

# Historical bootstrap + backtest — 2026-05-29

**Implements** PRD [v3-edge-and-learning](../../pm/prds/v3-edge-and-learning.md) Goal #5 +
Acceptance criterion #9 + Resolved decision #2; Plan
[Phase 4](../../pm/plans/v3-edge-and-learning.md). The one approved exception to the
markdown-only rule: a small **offline, diagnostic** Python script (`tools/backtest.py`),
off the runtime path — it never imports wallet/secrets, never places an order, never
writes to `state/`.

**The live pull RAN.** Numbers below are real, pulled 2026-05-29 ~13:19 UTC from
Polymarket's public Gamma + CLOB endpoints, and match the committed
`tools/bootstrap-calibration.json` exactly.

---

## TL;DR

- **538 resolved binary markets** scored (≥500 acceptance bar cleared), filtered for
  quality (clean 0/1 settlement, volume ≥ $1k, lifetime ≥ 2 days) out of **4,000** raw
  closed markets scanned.
- **Market-baseline Brier ≈ 0.121** — this is the number our own forecasts must beat to
  claim skill. (For reference: always-guess-0.5 scores 0.25; a perfect oracle scores 0.)
- **In/out-of-sample split** by resolution date (median = 2026-05-28): in-sample Brier
  **0.149** (n=268), out-of-sample **0.094** (n=270). Both halves are well below 0.25.
- **The price→frequency calibration curve is textbook**: extreme prices (≤0.1, ≥0.9) are
  very well calibrated; mid-range favorites (~0.5–0.7) realize slightly **above** their
  price — the classic favorite-longshot signature — but see the low-information caveat.
- **No mechanical signal beat the market.** Favorite-longshot and price-extremity rules
  each **sign-flipped** across the in/out split — i.e. the in-sample "edge" was noise the
  split correctly caught. **This is the right, honest verdict**, and it is the whole point
  of the split: do not ship an overfit signal as a live edge.
- **Cycle-count rec:** the evidence does **not** justify *adding* cycles, and mildly
  supports the *option* of trimming. Keep ~10/day. Details in §Cycle-count below.

---

## Why this was not "use the final price" (the data gotcha)

The naive plan — "use each market's final/settlement price as the forecast" — produces a
**fake near-zero Brier** and must not be used. For a *closed* market, Gamma's
`outcomePrices` is the **settlement** (≈[1,0]/[0,1]) and `lastTradePrice` is ≈0.999/0.001:
the market has already **converged to the answer**. Scoring those against the outcome
"predicts" a coin that has already landed.

To measure how well the market *forecasts*, we need the price at a meaningful **lead time
before resolution**. The script therefore does a **two-stage pull**:

1. **Gamma `/markets?closed=true`** (paginated, newest-resolved first) → the resolved
   universe + the realized 0/1 outcome from settlement prices, with quality filters.
2. **CLOB `/prices-history`** per market → the price **24h before the market's last tick**
   (`--lead-hours 24`, configurable). *That* pre-close price is the honest "market
   forecast" we score.

A `--forecast-source last_trade` mode exists for speed but is loudly flagged CONVERGED and
is **never** used for the seeded prior.

### Universe filtering (why 4,000 → 538)

The recent tail of closed markets is dominated by 5-minute crypto candles and esports
odd/even props whose price is ~0.5 noise — including them would swamp the calibration
table with coin-flips a generalist can't edge. Filters (from the committed `pull_stats`):

| stage | count |
|---|---:|
| raw closed markets scanned (Gamma, 40 pages) | 4,000 |
| rejected — low volume (< $1k) | 2,451 |
| rejected — short duration (< 2 days) | 893 |
| rejected — not a clean 0/1 binary settlement | 54 |
| **accepted into stage 1** | **560** |
| dropped in stage 2 — no usable CLOB pre-close price | 22 |
| **scored** | **538** |

---

## Market-baseline Brier + in/out-of-sample split

Scored on the outcome-0 YES leg (one observation per market), forecast = CLOB price 24h
pre-close, realized = settlement 0/1.

| slice | n | Brier |
|---|---:|---:|
| **All markets (baseline to beat)** | **538** | **0.12127** |
| In-sample (resolved < 2026-05-28) | 268 | 0.14905 |
| Out-of-sample (resolved ≥ 2026-05-28) | 270 | 0.09369 |

The market is a **strong baseline** — 0.121 is much better than the 0.25 of an
uninformed guesser. Our edge gate (PRD Goal #2) is calibrated for exactly this reality:
most markets are efficient, so most of the time the correct position is zero and we should
be *forecasting to learn*, not paying spread to express a weak opinion.

> **Reproducibility caveat (honest):** the resolved-market window moves continuously, so a
> fresh `--n 500` live pull returns a slightly different set and the headline Brier drifts
> run-to-run (observed 0.121–0.139 across pulls on 2026-05-29). The committed artifact +
> retained cache pin **one** deterministic pull; `python3 tools/backtest.py --offline`
> reproduces it byte-for-byte.

---

## Price → realized-frequency calibration (favorite-longshot curve)

10 equal-width price bins. `realized_freq` = fraction of markets in the bin that resolved
YES. A perfectly calibrated market has `realized_freq ≈ mean_forecast_p` on the diagonal.

| price_bin | n | mean_forecast_p | realized_freq | brier_contrib | low_info |
|---|---:|---:|---:|---:|:--:|
| 0.0–0.1 | 236 | 0.018 | 0.017 | 0.016 | |
| 0.1–0.2 | 31 | 0.148 | 0.129 | 0.114 | |
| 0.2–0.3 | 46 | 0.250 | 0.239 | 0.181 | |
| 0.3–0.4 | 39 | 0.339 | **0.513** | 0.270 | |
| 0.4–0.5 | 39 | 0.451 | 0.436 | 0.255 | |
| 0.5–0.6 | 71 | 0.514 | 0.578 | 0.241 | **LOW-INFO** |
| 0.6–0.7 | 16 | 0.639 | 0.625 | 0.226 | |
| 0.7–0.8 | 18 | 0.736 | 0.611 | 0.254 | |
| 0.8–0.9 | 9 | 0.861 | 1.000 | 0.020 | |
| 0.9–1.0 | 33 | 0.962 | 0.879 | 0.109 | |

**Reading it:**

- **The extremes are well-calibrated.** The 0.0–0.1 bin (n=236, the bulk of the data:
  longshot "will X happen" markets) realizes 0.017 vs a 0.018 mean price — essentially
  perfect. The 0.8–0.9/0.9–1.0 favorites mostly resolve YES as priced.
- **Mid-range bins are noisy** (small n: 9–46) and wobble off-diagonal in both directions
  (0.3–0.4 over-realizes at 0.513; 0.7–0.8 under-realizes at 0.611). With n<50 per bin
  these are not yet reliable signals — they are *priors with wide error bars*, exactly how
  `recalibrate` should treat them.
- **Low-information flag (a real data-quality find):** the 0.5–0.6 bin is flagged because
  **70%** of its observations sit at *exactly* 0.50 — the CLOB **initialization/default**
  price for illiquid markets, not a genuine consensus. Its 0.578 realized rate is largely
  an artifact of low-information markets parked at their seed price, **not** an exploitable
  "mid-favorites are underpriced" edge. The artifact flags this so the consumer **damps**
  the bin rather than mistaking the artifact for alpha.

---

## Mechanical-signal backtest (in/out-of-sample) — verdict: nothing beats the market

A signal "counts" only if it (a) appears in-sample, (b) keeps the **same sign**
out-of-sample, and (c) is materially > 0 (≥1pp) in **both** halves. Sign-flip or vanishing
magnitude ⇒ the in-sample effect was noise.

### Signal 1 — Favorite-longshot

Hypothesis: extreme favorites (price ≥ 0.90) are underpriced; longshots (price ≤ 0.10) are
overpriced.

| metric | in-sample | out-of-sample | verdict |
|---|---:|---:|---|
| favorite_gap (realized − price, p≥0.90) | −0.120 (n=26) | +0.052 (n=7) | **sign_flip → no edge** |
| longshot_overpricing (price − realized, p≤0.10) | −0.017 (n=90) | +0.014 (n=148) | **sign_flip → no edge** |

In-sample, favorites actually **under**-performed their price (gap −0.12) — the *opposite*
of the textbook bias — then flipped positive out-of-sample on just 7 markets. This is
noise, not a tradable favorite-longshot edge, at least in this (recent, weather/sports/
crypto-heavy) window.

### Signal 2 — Price-extremity ("press the market's confidence")

Hypothesis: when the market is very confident (≤0.10 or ≥0.90), snapping its price further
toward 0/1 lowers Brier (the market is under-confident at the extremes).

| metric | in-sample | out-of-sample | verdict |
|---|---:|---:|---|
| Δ = market_brier − snapped_brier (>0 ⇒ snapping helps) | −0.0017 | +0.0004 | **sign_flip → no edge** |

Snapping **hurt** in-sample and was negligibly positive out-of-sample. The market's
extreme prices are already well-calibrated (consistent with the calibration table) — there
is no free confidence edge to press.

**Bottom line:** all three mechanical signals fail the persistence test. **The market is
hard to beat with cheap price-only rules** — which is the honest, expected result and a
direct vindication of the in/out split (without it, the −0.12 in-sample favorite_gap or a
mid-bin wobble could have been mis-sold as a live edge). Any real edge must come from
*information* (parsed resolution + reference class + catalyst), not from a mechanical price
transform — exactly what the v3 edge gate (Goal #2) requires.

---

## Cycle-count / edge-source analysis (Resolved decision #2)

Gamma's `category` is empty for ~all of the resolved universe, so the script derives a
coarse `edge_source` bucket from question text. **Caveat (honest):** the keyword heuristic
is leaky — "Russia"/"Iran" weather and Egypt-vs-Russia soccer markets land in
`geopolitics`; weather/temperature markets dominate `other`. So the **small** buckets
(geopolitics n=14, tech_ai n=4, politics) are contaminated and **not** trustworthy. Only
the high-n buckets (`other`, `sports`, `crypto`) carry signal.

| edge_source | n | market_brier | mean_signed_movement_toward_truth |
|---|---:|---:|---:|
| other (mostly weather/temperature bands) | 296 | 0.071 | 0.353 |
| sports | 141 | 0.195 | 0.125 |
| crypto | 83 | 0.179 | 0.167 |
| geopolitics *(contaminated, n small)* | 14 | 0.024 | 0.409 |
| tech_ai *(contaminated, n small)* | 4 | 0.363 | 0.027 |

`mean_signed_movement_toward_truth` = how far, on average, the 24h-pre-close price had
already moved from 0.5 toward the realized outcome. **Higher = the category resolves
informatively early ⇒ CLV is learnable there. Near zero = coin-flip-like ⇒ little for a
generalist to add.**

**What this says about ~10/day:**

1. **`sports` and `crypto` are the hardest buckets for a generalist** — high Brier
   (0.18–0.20, near the 0.25 coin-flip wall) and low pre-close movement-toward-truth
   (0.13/0.17). These are efficient, fast, liquid markets where a generalist LLM has no
   informational edge. **Spending paid cycles forecasting them is low-value.**
2. **`other` (weather/temperature)** is mechanically well-priced (Brier 0.071) but that is
   meteorology, not a tradable generalist edge either — the market already integrates the
   forecast.
3. The buckets where a *researched* generalist edge is most plausible (geopolitics,
   politics, macro, tech/AI events) are **too sparse in the recent resolved window** to
   measure here. That sparsity is itself informative: such markets are **rarer and resolve
   over weeks**, which fits a **forecast-broadly, snapshot-on-pulse, bet-rarely** cadence —
   not a high-frequency one.

**Recommendation: keep ~10/day; do NOT add cycles; consider trimming as a future option.**

- There is **no evidence** that more frequent cycles would improve learning: the markets a
  generalist can plausibly edge resolve slowly (weeks), so CLV snapshots at the existing
  6 pulse + 2 content + 2 risk cycles already over-sample them. Adding cycles would mostly
  re-snapshot fast/efficient sports/crypto markets where there is no edge to learn.
- The data **mildly supports the option to reduce** pulse frequency (e.g. 6→4 snapshots/
  day) for slow-resolving books without hurting CLV resolution — a cost saving to revisit
  after the live CLV window (PRD Success signal) confirms which buckets actually generate
  positive CLV. **Defer the actual trim** until live CLV data exists; the backtest can only
  say "more is not justified," not pick the exact floor.
- **Concrete steer for the edge gate / market selection (decision #5):** the historical
  evidence says `sports` and `crypto` should have to *earn* their right to size via live
  CLV (they start at Tier 0 like everything, and this data predicts they will struggle to
  graduate). No hardcoded ban — the CLV-by-bucket mechanism already demotes them.

---

## The seeded prior artifact + how `recalibrate` ingests it

`tools/backtest.py` writes **`tools/bootstrap-calibration.json`** (NOT `state/`). It is a
**baseline to beat + a calibration map**, explicitly flagged `source:"historical_bootstrap"`
— **not** a fabricated track record of the agent's own trades. Each calibration row:

```json
{"price_bin":"0.9-1.0","n":33,"mean_forecast_p":0.9621,"realized_freq":0.8788,
 "brier_contrib":0.10934,"default_price_share":0.0,"low_information_flag":false,
 "source":"historical_bootstrap"}
```

**Ingestion contract (documented in the artifact's `ingestion_contract` block, for
`skills/recalibrate` to implement as a code path — do NOT hand-edit
`state/calibration.json`; parallel live cycles own it):**

1. Treat each `calibration_rows` entry as a **Beta prior** for its price bin:
   pseudo-count = `n` (optionally damped), prior mean = `realized_freq`.
2. `recalibrate` maps the 0.1-wide Polymarket price bins onto its own `lo-hi` calibration
   buckets and seeds each bucket's `adjustment`/`status` **from the prior** until live
   `resolved_n` accumulates and dominates the posterior. The seed is clearly tagged
   `source:"historical_bootstrap"` so it is distinguishable from live-earned calibration.
3. **Damp low-information bins:** rows with `low_information_flag:true`
   (`default_price_share ≥ 0.30`) are dominated by illiquid markets parked at the 0.50 CLOB
   seed price; their `realized_freq` is an artifact. Down-weight their pseudo-count (e.g.
   ×0.25) or skip seeding them.
4. **Never** present these numbers as the agent's own performance.

> This file is the **input** to a future `recalibrate` seeding step. Phase 4's deliverable
> is the artifact + this contract; wiring the actual `recalibrate` read-path is a small
> follow-on (it must not collide with live cycles — hence "code path that reads this file,"
> not a manual `state/` edit).

---

## How to (re)run

```bash
# Live pull, 500+ quality markets, with a reproducibility cache (the run used here):
python3 tools/backtest.py --n 500 --cache

# Reproduce the committed artifact byte-for-byte from the cache (no network):
python3 tools/backtest.py --offline

# Full options:
python3 tools/backtest.py --help
```

Defaults: `--n 500`, `--lead-hours 24`, `--forecast-source clob_pre_close`,
`--min-volume 1000`, `--min-duration-days 2`, `--bins 10`, timeout 20s, 3 retries with
exponential backoff. stdlib-only (uses `requests` if importable, else `urllib`). The run
takes ~90s (≈40 Gamma pages + ≈560 CLOB history calls).

**Safety:** read-only public HTTP GETs only; writes ONLY `tools/bootstrap-calibration.json`
(+ `tools/.backtest-cache.json` when `--cache`); never touches `state/`, wallet, secrets;
never trades.

---

## Acceptance (PRD AC #9 / Plan Phase 4 verify)

- [x] Script exists and is runnable (`tools/backtest.py`, `--help` works, compiles clean).
- [x] Report from ≥500 resolved markets — **538** scored.
- [x] In/out-of-sample split — by resolution date (median 2026-05-28); in n=268 Brier
      0.149, out n=270 Brier 0.094.
- [x] Market-baseline Brier — **0.12127**.
- [x] Price→frequency calibration table (10 bins) — above, with low-information flagging.
- [x] ≥1 signal that did/didn't beat market — **3 signals, all DID NOT beat the market**
      (favorite-longshot ×2 and price-extremity all sign-flip across the split).
- [x] Seeded + flagged calibration prior — `tools/bootstrap-calibration.json`, every row
      `source:"historical_bootstrap"`; ingestion contract documented;
      `state/calibration.json` **untouched**.
- [x] Cycle-count recommendation — keep ~10/day, do not add, trimming is a deferred option.
- [x] Honesty about whether it ran — **it ran**; numbers are real and match the artifact.
