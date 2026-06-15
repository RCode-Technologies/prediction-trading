---
id: 2026-06-15-longshot-calibration-metric
title: Add a longshot-regime calibration metric; the linear slope is blind where we trade
created: 2026-06-15
lens: measurement
status: surfaced
bucket: human_application
conviction: medium
reversibility: easy
horizon: next
supersedes: null
---

## Claim

Our headline calibration statistic — `calibration_slope` / `calibration_intercept` (OLS of `outcome ~ your_p`) — is **structurally uninformative for this agent**, because nearly every forecast we emit lives at `p < 0.10`. The scorecard should additionally report a calibration metric that is meaningful in the longshot regime: a per-decade **log-odds reliability** statistic (observed vs predicted odds within `p ∈ {<0.02, 0.02–0.05, 0.05–0.10, 0.10–0.25, >0.25}` bands) plus a single scalar **longshot-bias coefficient** (mean signed `logit(outcome_freq) − logit(mean_your_p)` across populated bands).

## Evidence

- `state/scorecard.json` reports `exploit.calibration_slope: 0.0`, `calibration_intercept: 0.0`, and every populated `state/calibration.json` bucket likewise shows `calibration_slope: 0.0` — not a measured calibration of 1.0, but a **degenerate/unestimable** fit at this sample and probability range.
- Today's 12 forecasts: `your_p` ∈ {0.004, 0.004, 0.005, 0.006, 0.02, 0.025, 0.04, 0.07, 0.10, 0.20, 0.95, 0.005} — 10 of 12 below 0.10. The 06-14 batch was identical in shape. This is the *normal* output distribution, not an outlier day.
- Resolved buckets are all extreme: calibration.json shows live data only in `0-10` (explore n=6) and `40-50`; the `50-90` exploit buckets are all `resolved_n:0`. OLS slope over points clustered at one end of [0,1] is dominated by noise.
- Consequence: `reflect`'s cold-start carve-out already *distrusts* `calibration_slope` (it falls back to `explore.calibration_slope`, also 0.0). We are flying calibration-blind and the scorecard hides it behind a plausible-looking `0.0`.

## Why it might be wrong (steelman)

- With `resolved_n` in single digits, **no** calibration metric is reliable yet — a log-odds reliability table would also be mostly empty, so this may be measuring nothing more honestly. Brier-skill already captures accuracy; calibration shape may be premature to chase.
- Longshot markets are near-efficient; if our `your_p` tracks `market_p` closely (today avg diff −0.0011), there may be little calibration *signal* to extract regardless of the metric's form.
- Adds scorecard surface area (token + maintenance cost) for a metric that only becomes trustworthy after dozens more resolutions.

## Cheapest falsifying experiment

Compute the log-odds reliability table **offline, read-only** over `state/forecasts.resolved.jsonl` (13 rows today) and compare its verdict to the current `calibration_slope: 0.0`. If the table is also entirely empty/uninformative at current n, the proposal is premature → park it with a re-check trigger at `resolved_n >= 20`. If even today's 13 rows reveal a directional longshot bias the slope hides, it's validated. Zero capital, zero new invocations — rides an existing `daily-close`.

## Impact & cost

- **Learning impact:** turns a degenerate headline number into an honest signal about *where* on the probability axis we are mis-calibrated — the single most actionable thing for a longshot-heavy book.
- **Invocation cost:** none (computation rides `recalibrate.sweep`, already running).
- **Token cost:** small (a ~5-row table + one scalar in the scorecard JSON / recap).
- **Capital effect:** none.
- **Why human_application:** the canonical computation belongs in `skills/recalibrate` (scorecard owner), which is on the protected-core denylist (`config/autonomy.md`) — the agent may not self-author it. A human applies the metric definition; alternatively a reviewer may decide a read-only mirror in `skills/recap` (non-protected) is the lighter first step.

## Change sketch

For a human (or a follow-up `recap`-only RFC):
1. In `skills/recalibrate` `sweep()` step 6, after Brier, compute per-band observed frequency and mean `your_p` for bands `[<0.02, 0.02–0.05, 0.05–0.10, 0.10–0.25, >0.25]`; emit `scorecard.<intent>.longshot_reliability[]` (`{band, n, obs_freq, mean_your_p, logit_gap}`) and a scalar `scorecard.<intent>.longshot_bias` = mean `logit_gap` over bands with `n>=3`.
2. `skills/recap` embeds the table under *Smartness scorecard*.
3. `reflect` step 6 may read `longshot_bias` as a calibration signal once any band has `n>=10` (supersedes the degenerate slope for this agent's regime).
Denylist note: step 1 touches protected-core `skills/recalibrate` → human applies; steps 2–3 are non-protected and could ship first as a read-only display.
