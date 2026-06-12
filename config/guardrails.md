# Guardrails

Human-owned. Reflection cannot edit this file; recommendations surface via daily summary. (v3 cost-honest edits supervisor-authorized 2026-05-29 — see pm/prds/v3-edge-and-learning.md.)

> **Protected-core rail (HARD) — human-authored only.** Enforced mechanically by `config/autonomy.md` § Enforcement (intent gate · write gate · `boot` audit · `.githooks/pre-commit`). A `protected_core_violation` is valid only when `skills/boot/protected-core-audit.sh` exits 3 — never from authorship reasoning or "which files the last fix touched."

## Cost-honest prices (v3)

You **buy at the ask, sell at the bid** — midpoint is never the trade or mark price. Sizing prices entries at `best_ask` (`new_order_notional = shares * best_ask`); NAV marks longs at `best_bid` (liquidation value). The 5% cap and the circuit breaker both operate on **liquidation NAV**. Midpoint is reference/display only.

## Position sizing — conviction ladder (v3; `skills/sizing`)

**Size is earned, not granted.** The flat 5%/token cap is gone as the *primary* rule — it sized a fabricated coin-flip identically to a proven edge. The doctrine: **default to capital preservation; earn the right to be aggressive; skill is the only license to size.** Most days you have no edge, so the correct position is **Tier 0 (zero)** and you do not pay the spread to express an opinion. The § Edge gate (provenance + net-edge floor) runs **first**; only a gate-passer is eligible for a tier above 0.

The ladder (every `decision` carries its `sizing_tier ∈ {0,1,2,3}` + the preconditions it cleared):

| Tier | Name | Preconditions (ALL required) | Max size |
|---|---|---|---|
| 0 | **Observe** | default — no proven bucket skill, **or** `edge_net < net_edge_floor`, **or** resolution unparsed | **0%** (forecast-only) |
| 1 | **Lean** | `edge_net ≥ net_edge_floor` + resolution parsed + reference class (≥2 sources) + bucket `clv_mean ≥ 0` | **0.5–2% NAV** |
| 2 | **Conviction** | Tier 1 + *proven* bucket skill (`clv_mean > 0` with `clv_n ≥ 20`, **or** `brier_skill > 0`) + hard near-term catalyst | **≤ 5% NAV** |
| 3 | **Degen (earned)** | Tier 2 + exceptional edge (`edge_net ≥ 2 × net_edge_floor`) + high calibration confidence + uncorrelated + portfolio heat **< 10%** | **≤ 10% NAV (hard ceiling)** |

```
existing_token_risk + new_order_notional + fees <= tier_cap_pct * NAV
new_order_notional + fees                       <= cash_usdc
```

`tier_cap_pct ∈ {0, 0.02, 0.05, 0.10}` by tier (Tier 1's *floor* 0.5% is the min-size threshold below which the fill is dropped). `NAV = cash + Σ(shares * mark_liquidation)`, `mark_liquidation = best_bid` for a long (CLOB `ts ≤ 15min`). `new_order_notional = shares * best_ask` (entry at the ask). `existing_token_risk` includes open positions + open orders on the same token. Stale NAV → no new trades. **10% is the hard ceiling — no tier, multiplier, or override may exceed it.**

An **unproven bucket** (`edge_source` with `clv_mean` not yet `> 0` at `clv_n ≥ 20` and `brier_skill` not `> 0`) is capped at **≤ Tier 1** regardless of edge magnitude. Until a bucket earns skill the whole book is Tier ≤ 1 — early v3 will mostly not bet, **and that is the point.**

## Portfolio heat (`skills/risk`, `skills/sizing`)

**Total liquidation-risk across the book ≤ 25% of NAV, spread over ≤ 4 uncorrelated buckets.**

```
portfolio_heat = Σ_open (position.shares * mark_liquidation) / NAV     # current book exposure, liquidation-marked
```

A new exploit is **rejected** if it would push `portfolio_heat > 0.25` or open a 5th uncorrelated bucket. **Tier 3 is reachable only when current `portfolio_heat < 0.10`** (don't back the truck into an already-hot book). Correlated positions count in one bucket (see § Correlation).

## Correlation

Related-fact markets (same election/match/regulatory event) share one bucket — one tier cap *and* one heat bucket. Uncertain → reject.

## Order direction

Long BUY only. SELL only to reduce/close.

## Mark freshness

Quotes >15 min stale → no sizing, no trade.

## Equity governors — drawdown-from-peak (v3; primary control; `skills/circuit-breaker`)

A 5%-capped book can never lose 10% in 24h from positions, so the 24h breaker was security theater for a multi-week book. **Drawdown-from-peak is now the primary equity control**, evaluated alongside the catastrophic halt:

```
peak_nav             = max NAV over history (nav_snapshots + current)        # liquidation-marked
drawdown_from_peak   = (current_NAV - peak_nav) / peak_nav                    # ≤ 0
```

- **−8% from peak → probation:** all sizing × 0.5 (`sizing_mult:0.5`) + `notify`. Not a halt — new bets continue at half size. Lifts automatically once NAV recovers above the −8% line.
- **−15% from peak → forecast-only freeze:** no new capital risk (every candidate demoted to forecast-only / Tier 0); **human review required to resume.** Records a `halt`-class governor trip; exits still allowed (a freeze must never trap a losing position).

## Circuit breaker — -10% / 24h (`skills/circuit-breaker`)

`rolling_24h_pnl <= -0.10 * baseline_NAV` → halt, log, notify, commit, push, stop. Both current and baseline NAV are liquidation-marked (longs at `best_bid`). Baseline = latest `nav_snapshot` with `ts ≤ now - 24h`, else `starting_capital`. Only humans clear. Unexplained cash delta also halts. **Retained as the catastrophic hard halt** — the drawdown-from-peak governors above are the everyday control; this remains the floor for a fast, deep one-day loss.

## Disconfirmation stop — reduce/close (v3; `skills/sizing` risk_reduction; non-negotiable)

A held position is **reduced or closed** (a `risk_reduction` SELL — paper: a reducing/closing `paper_fill` at `best_bid`) when **either** trips:

```
pnl_from_entry = (mark_liquidation - avg_price) / avg_price <= -0.25      # −25% mark-from-entry (longs)
```

- **−25% mark-from-entry**, OR
- a **named disconfirming event** materialises (a `disconfirming_signals` item from the forecast actually occurs).

This is the control the Iran position never had: v2 could *see* its thesis break and still could not act. v2's "no auto-SELL" rule is **replaced**. Exits are exempt from the freeze/halt (you may always reduce risk).

## Research cap — 3 sources/cycle

Shared between `skills/research` + `skills/markets`. Native WebSearch/WebFetch count. Safety re-checks in `sizing`/`trade` don't.

## Append-only log

`state/trade-log.jsonl`: append only, never edit. Each line = valid JSON with `schema_version`, `event_id`, `cycle_id`, `event_type`, `ts`, `mode`.

## Push = success

Every cycle: one Conventional Commit + pull --rebase + push. No `--force` / `--no-verify`. `--force-with-lease` only for human-directed history consolidation after verifying clean tree + unchanged remote. No push = `persist_conflict`.

## Mainnet gate

`skills/trade` is the only skill that reads wallet secrets. Preflights are fail-closed. Never infer Polymarket eligibility, never VPN, never bypass platform restrictions.

## Secrets

`WALLET_SEED` is the only wallet secret. Presence check only: `[ -n "${WALLET_SEED:-}" ]`. Never print, log, or commit values.
