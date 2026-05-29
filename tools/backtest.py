#!/usr/bin/env python3
"""
tools/backtest.py — OFFLINE historical bootstrap + backtest for the Polymarket agent.

WHAT THIS IS
------------
A one-shot, OFFLINE, diagnostic script (v3 Plan, Phase 4 — the single approved
exception to the markdown-only rule). It pulls *already-resolved* Polymarket
markets and answers three questions that let day-1 v3 start with a realistic
baseline instead of a cold start:

  1. How well-calibrated is the *market itself*?  -> market-baseline Brier, the
     number our own forecasts must beat to claim skill.
  2. What does the price -> realized-frequency map look like?  -> the
     favorite-longshot bias curve (a calibration table, 10 price bins).
  3. Do any cheap mechanical signals beat the market historically?  -> a first
     pass at favorite-longshot and price-extremity edges, with an
     IN/OUT-OF-SAMPLE split by resolution date so we don't fool ourselves.

It also reports which market categories ("edge_source" buckets) historically
carry the most price movement toward truth, which informs the cycle-count
question (is ~10 invocations/day justified, or could it be reduced?).

WHY IT IS NOT TRIVIAL (the data gotcha, read this)
--------------------------------------------------
Polymarket's Gamma `/markets` endpoint, for a *closed* market, reports
`outcomePrices` and `lastTradePrice` as the *settlement* state — i.e. ~[1,0] or
~[0,1] and a last trade ~0.999/~0.001. Those are NOT a forecast; the market has
already converged to the answer. Scoring Brier against them yields a fake ~0.

To get an HONEST market-baseline Brier we need the market's forecast price at a
meaningful LEAD time *before* resolution. We get that from the CLOB
price-history endpoint (`/prices-history`), sampling the price `--lead-hours`
before the market's last tick. That pre-close price is the genuine "market
forecast"; we score it against the realized binary outcome.

  forecast source (default, honest) : CLOB price `--lead-hours` before close.
  forecast source (fast, flagged)   : Gamma `lastTradePrice` (CONVERGED — do
                                       NOT use for the seeded prior; diagnostic
                                       only, loudly flagged in output).

OUTPUTS
-------
  tools/bootstrap-calibration.json   machine-readable seeded prior. Rows:
      {price_bin, n, realized_freq, brier_contrib, source:"historical_bootstrap"}
    plus top-level metadata + signal verdicts + the cycle-count note.
    This is a *prior to beat*, not a fabricated track record of our own trades.
    skills/recalibrate ingests it as a seeded prior (see the docstring section
    "HOW recalibrate SHOULD INGEST THIS" and the Phase 4 research report).

  (the research report is written by hand from this script's printed summary;
   the script itself only writes the JSON artifact.)

HARD SAFETY CONSTRAINTS (by construction)
-----------------------------------------
  * OFFLINE / diagnostic only. OFF the runtime path.
  * Never imports or touches wallet / secrets / private keys.
  * Never places an order. Read-only public HTTP (GET) to public endpoints.
  * Never writes to state/. Writes ONLY tools/bootstrap-calibration.json
    (and tools/.backtest-cache.json when --cache is used).
  * Idempotent: re-running overwrites the artifact deterministically (modulo
    fresh market data); --offline/--cache make it fully reproducible.

DEPENDENCIES
------------
  stdlib only. Uses `requests` if importable (nicer pooling) else falls back to
  urllib. No third-party install required.

USAGE
-----
  python3 tools/backtest.py --help
  python3 tools/backtest.py --n 500                  # live pull, 500 markets
  python3 tools/backtest.py --n 500 --cache          # pull + write a cache
  python3 tools/backtest.py --offline                # replay from cache only
  python3 tools/backtest.py --n 500 --lead-hours 24  # forecast price 24h pre-close

EXIT CODES
----------
  0  success (artifact written)
  2  insufficient usable markets pulled (artifact written with status flag)
  3  network unreachable and no cache (artifact written as template_unrun)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone

# ----------------------------------------------------------------------------
# HTTP layer — prefer requests, degrade gracefully to urllib. Read-only GETs.
# ----------------------------------------------------------------------------

_USER_AGENT = "polymarket-agent-offline-backtest/1.0 (diagnostic; no-auth)"

try:  # optional dependency
    import requests  # type: ignore

    _HAVE_REQUESTS = True
except Exception:  # pragma: no cover - environment dependent
    requests = None  # type: ignore
    _HAVE_REQUESTS = False

import urllib.error
import urllib.request


class NetworkError(RuntimeError):
    """Raised when a GET ultimately fails after retries/backoff."""


def http_get_json(url: str, *, timeout: float, retries: int, backoff: float):
    """GET a URL and parse JSON, with timeout + exponential backoff.

    Pure read-only. Returns the parsed object, or raises NetworkError after
    exhausting retries. 4xx (except 429) are treated as fatal (no retry); 429
    and 5xx and transport errors are retried with backoff.
    """
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            if _HAVE_REQUESTS:
                resp = requests.get(  # type: ignore[union-attr]
                    url, timeout=timeout, headers={"User-Agent": _USER_AGENT}
                )
                status = resp.status_code
                if status == 200:
                    return resp.json()
                if status != 429 and 400 <= status < 500:
                    raise NetworkError(f"HTTP {status} for {url}")
                last_exc = NetworkError(f"HTTP {status} for {url}")
            else:
                req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    return json.load(r)
        except urllib.error.HTTPError as e:  # urllib path
            if e.code != 429 and 400 <= e.code < 500:
                raise NetworkError(f"HTTP {e.code} for {url}") from e
            last_exc = e
        except NetworkError:
            # already-categorized retryable (requests 429/5xx) -> fall through
            pass
        except Exception as e:  # timeouts, conn reset, DNS, JSON decode
            last_exc = e

        if attempt < retries:
            sleep_s = backoff * (2 ** attempt)
            time.sleep(sleep_s)

    raise NetworkError(f"GET failed after {retries + 1} tries: {url} :: {last_exc}")


# ----------------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------------

GAMMA_MARKETS = "https://gamma-api.polymarket.com/markets"
CLOB_PRICES_HISTORY = "https://clob.polymarket.com/prices-history"


# ----------------------------------------------------------------------------
# Small parsing helpers — Gamma encodes several fields as JSON *strings*.
# ----------------------------------------------------------------------------

def _json_field(market: dict, key: str):
    """Several Gamma fields ('outcomes','outcomePrices','clobTokenIds') arrive
    as JSON-encoded strings. Decode defensively; return [] on any failure."""
    raw = market.get(key)
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return []


def _parse_iso(s):
    """Robustly parse the several timestamp shapes Gamma emits. Examples seen:
      '2026-06-04T08:00:00Z'        (endDate — ISO, Z)
      '2026-05-29 13:05:58+00'      (closedTime — space sep, '+00' offset)
    Python 3.9's fromisoformat rejects both the space form and the bare '+00'
    offset, so we normalize first."""
    if not s or not isinstance(s, str):
        return None
    t = s.strip().replace("Z", "+00:00").replace(" ", "T")
    # Normalize a bare '+00' / '-05' style offset to '+00:00' / '-05:00'.
    for i in range(len(t) - 1, 0, -1):
        if t[i] in "+-" and i >= 10:  # an offset sign after the date part
            off = t[i:]
            if len(off) == 3:  # e.g. '+00'
                t = t[:i] + off + ":00"
            break
    try:
        return datetime.fromisoformat(t)
    except (ValueError, TypeError):
        return None


def _duration_days(market: dict):
    s = _parse_iso(market.get("startDate"))
    e = _parse_iso(market.get("endDate"))
    if s is None or e is None:
        return None
    return (e - s).total_seconds() / 86400.0


_EDGE_SOURCE_KEYWORDS = [
    ("crypto", ["bitcoin", "btc", "ethereum", "eth", "solana", " sol ", "crypto", "dogecoin", "xrp", "up or down"]),
    ("sports", ["nba", "nfl", "mlb", "nhl", "ufc", "soccer", "premier league", "la liga",
                 "champions league", "world cup", "match", "vs.", " vs ", "win the", "playoff",
                 "super bowl", "kills", "map ", "tennis", "f1", "grand prix", "cricket"]),
    ("politics", ["president", "election", "senate", "congress", "governor", "primary",
                   "parliament", "minister", "vote", "poll", "trump", "biden", "democrat",
                   "republican", "nominee", "cabinet", "impeach"]),
    ("geopolitics", ["war", "ceasefire", "iran", "russia", "ukraine", "israel", "gaza",
                      "china", "north korea", "nuclear", "treaty", "sanction", "nato",
                      "military", "strike", "invasion", "diplomatic", "summit"]),
    ("macro", ["fed", "interest rate", "inflation", "cpi", "gdp", "recession", "fomc",
                "unemployment", "jobs report", "rate cut", "rate hike"]),
    ("tech_ai", ["ai ", "gpt", "openai", "google", "model", "chatgpt", "llm", "apple",
                  "tesla", "spacex", "launch", "release"]),
]


def derive_edge_source(market: dict):
    """Gamma's `category` is empty for most of the resolved universe, so derive
    a coarse 'edge_source' bucket from the question text. This is a heuristic
    tag for the cycle-count / per-bucket analysis — not authoritative — but it
    turns an all-'uncategorized' breakdown into something actionable. Mirrors
    the spirit of the agent's own `edge_source` tagging (PRD decision #5)."""
    cat = (market.get("category") or "").strip().lower()
    if cat and cat not in ("none", "uncategorized"):
        return cat
    q = (market.get("question") or "").lower()
    for label, kws in _EDGE_SOURCE_KEYWORDS:
        if any(k in q for k in kws):
            return label
    return "other"


def _settlement_outcome(market: dict):
    """For a resolved binary market, return (won0, prices) where won0 is 1 if
    outcome[0] settled True, else 0; or None if not a clean 0/1 binary
    settlement. We require the two settled prices to round to {0,1}."""
    prices = _json_field(market, "outcomePrices")
    if len(prices) != 2:
        return None
    try:
        fp = [float(x) for x in prices]
    except (ValueError, TypeError):
        return None
    rounded = sorted(round(x) for x in fp)
    if rounded != [0, 1]:
        return None  # still-proposed (e.g. [0.5,0.5]) or degenerate ([0,0])
    won0 = 1 if round(fp[0]) == 1 else 0
    return won0, fp


# ----------------------------------------------------------------------------
# Stage 1 — pull the resolved-market universe from Gamma.
# ----------------------------------------------------------------------------

def pull_resolved_markets(
    *,
    target_n: int,
    min_volume: float,
    min_duration_days: float,
    timeout: float,
    retries: int,
    backoff: float,
    page_size: int = 200,
    max_pages: int = 200,
    polite_delay: float = 0.05,
    log=print,
):
    """Paginate Gamma `?closed=true`, newest-resolved first, keeping only
    quality binary markets (clean 0/1 settlement, volume + duration filters),
    until we have `target_n` candidates or run out of pages.

    Returns (candidates, stats). Quality filters matter: the recent tail of
    closed markets is dominated by 5-minute crypto candles and esports
    odd/even props whose price is ~0.5 noise — including them would swamp the
    calibration table with coin-flips. We filter for markets a generalist could
    plausibly have an edge on (multi-day, non-trivial volume)."""
    candidates: list[dict] = []
    seen_ids: set = set()
    stats = Counter()
    for page in range(max_pages):
        offset = page * page_size
        url = (
            f"{GAMMA_MARKETS}?closed=true&limit={page_size}&offset={offset}"
            f"&order=closedTime&ascending=false"
        )
        batch = http_get_json(url, timeout=timeout, retries=retries, backoff=backoff)
        if not isinstance(batch, list) or not batch:
            stats["empty_page_stop"] += 1
            break
        stats["raw_markets_seen"] += len(batch)
        for m in batch:
            mid = m.get("id")
            if mid in seen_ids:
                continue
            seen_ids.add(mid)
            settle = _settlement_outcome(m)
            if settle is None:
                stats["rej_not_clean_binary"] += 1
                continue
            vol = float(m.get("volumeNum") or m.get("volume") or 0.0)
            if vol < min_volume:
                stats["rej_low_volume"] += 1
                continue
            dur = _duration_days(m)
            if dur is None or dur < min_duration_days:
                stats["rej_short_duration"] += 1
                continue
            won0, _prices = settle
            candidates.append(
                {
                    "id": mid,
                    "question": (m.get("question") or "")[:140],
                    "category": derive_edge_source(m),
                    "category_raw": (m.get("category") or "uncategorized"),
                    "outcomes": _json_field(m, "outcomes"),
                    "clob_token_ids": _json_field(m, "clobTokenIds"),
                    "won_outcome0": won0,
                    "last_trade_price": m.get("lastTradePrice"),
                    "end_date": m.get("endDate"),
                    "closed_time": m.get("closedTime"),
                    "volume": vol,
                    "duration_days": round(dur, 2),
                }
            )
            stats["accepted"] += 1
            if len(candidates) >= target_n:
                break
        log(
            f"  page {page:>3} offset {offset:>5}: "
            f"seen {stats['raw_markets_seen']:>5}, accepted {stats['accepted']:>4}"
        )
        if len(candidates) >= target_n:
            break
        if polite_delay:
            time.sleep(polite_delay)
    return candidates, stats


# ----------------------------------------------------------------------------
# Stage 2 — for each market, sample the pre-close forecast price (CLOB history).
# ----------------------------------------------------------------------------

def sample_pre_close_price(
    token_id: str,
    *,
    lead_hours: float,
    timeout: float,
    retries: int,
    backoff: float,
):
    """Return the CLOB price `lead_hours` before the market's last tick, using
    the prices-history timeseries for outcome-0's token. None if history is too
    sparse. This is the honest 'market forecast' for Brier."""
    url = (
        f"{CLOB_PRICES_HISTORY}?market={token_id}&interval=max&fidelity=720"
    )  # fidelity in minutes (12h bars) -> light, plenty for a lead-time sample
    data = http_get_json(url, timeout=timeout, retries=retries, backoff=backoff)
    hist = (data or {}).get("history") or []
    if len(hist) < 2:
        return None
    t_last = hist[-1]["t"]
    cutoff = t_last - lead_hours * 3600.0
    pre = [pt for pt in hist if pt["t"] <= cutoff]
    if not pre:
        return None
    p = float(pre[-1]["p"])
    # Guard against settlement leakage: if the "pre-close" sample is itself
    # essentially converged (<=0.005 or >=0.995) AND the series is very short,
    # it's unreliable as a forecast. Keep it but the caller can see extremity.
    return max(0.0, min(1.0, p))


def attach_forecast_prices(
    candidates: list[dict],
    *,
    source: str,
    lead_hours: float,
    timeout: float,
    retries: int,
    backoff: float,
    polite_delay: float,
    log=print,
):
    """Populate each candidate with `forecast_p` (outcome-0 forecast). Markets
    without a usable forecast price are dropped (counted). Returns (kept,
    dropped_count)."""
    kept = []
    dropped = 0
    n = len(candidates)
    for i, m in enumerate(candidates):
        if source == "last_trade":
            ltp = m.get("last_trade_price")
            if ltp is None:
                dropped += 1
                continue
            m["forecast_p"] = max(0.0, min(1.0, float(ltp)))
            m["forecast_source"] = "last_trade(CONVERGED)"
            kept.append(m)
            continue

        # default: clob_pre_close
        tids = m.get("clob_token_ids") or []
        if not tids:
            dropped += 1
            continue
        try:
            p0 = sample_pre_close_price(
                tids[0],
                lead_hours=lead_hours,
                timeout=timeout,
                retries=retries,
                backoff=backoff,
            )
        except NetworkError:
            p0 = None
        if p0 is None:
            dropped += 1
        else:
            m["forecast_p"] = p0
            m["forecast_source"] = f"clob_{lead_hours:g}h_pre_close"
            kept.append(m)
        if polite_delay:
            time.sleep(polite_delay)
        if (i + 1) % 50 == 0:
            log(f"  forecast prices: {i + 1}/{n} (kept {len(kept)}, dropped {dropped})")
    return kept, dropped


# ----------------------------------------------------------------------------
# Metrics — Brier, calibration table, signals.
# ----------------------------------------------------------------------------

def brier(forecast_p: float, outcome: int) -> float:
    """Single-event Brier score for the YES leg: (p - y)^2."""
    return (forecast_p - outcome) ** 2


def market_baseline_brier(rows: list[dict]):
    """Mean Brier of the market's pre-close forecast vs realized outcome,
    scored on outcome-0's YES leg. Returns (mean_brier, n)."""
    contribs = [brier(r["forecast_p"], r["won_outcome0"]) for r in rows]
    if not contribs:
        return None, 0
    return statistics.fmean(contribs), len(contribs)


def calibration_table(rows: list[dict], n_bins: int = 10):
    """Bin outcome-0 forecast prices into n_bins equal-width bins; report
    realized win-frequency per bin (the favorite-longshot curve). Each row is
    one (forecast_p, outcome) observation."""
    edges = [i / n_bins for i in range(n_bins + 1)]
    buckets: list[list[tuple]] = [[] for _ in range(n_bins)]
    for r in rows:
        p = r["forecast_p"]
        idx = min(int(p * n_bins), n_bins - 1)
        buckets[idx].append((p, r["won_outcome0"]))
    table = []
    for i in range(n_bins):
        obs = buckets[i]
        lo, hi = edges[i], edges[i + 1]
        if obs:
            mean_p = statistics.fmean(p for p, _ in obs)
            freq = statistics.fmean(y for _, y in obs)
            brier_contrib = statistics.fmean((p - y) ** 2 for p, y in obs)
            # Share of observations sitting at exactly 0.50 — the CLOB
            # initialization/default price for illiquid markets. A high share
            # means the bin's realized_freq is driven by low-information markets
            # parked at their seed price, NOT a genuine market consensus; the
            # consumer should DAMP such a bin's prior. (This is why the 0.5-0.6
            # bin can look like it 'underprices YES' — mostly a default-price
            # artifact, not an exploitable edge.)
            default_share = statistics.fmean(1.0 if abs(p - 0.5) < 1e-9 else 0.0 for p, _ in obs)
        else:
            mean_p = freq = brier_contrib = None
            default_share = None
        table.append(
            {
                "price_bin": f"{lo:.1f}-{hi:.1f}",
                "lo": round(lo, 3),
                "hi": round(hi, 3),
                "n": len(obs),
                "mean_forecast_p": None if mean_p is None else round(mean_p, 4),
                "realized_freq": None if freq is None else round(freq, 4),
                "brier_contrib": None if brier_contrib is None else round(brier_contrib, 5),
                "default_price_share": None if default_share is None else round(default_share, 3),
                "low_information_flag": bool(default_share is not None and default_share >= 0.30),
            }
        )
    return table


def _binary_obs_from_rows(rows: list[dict]):
    """Expand each market into a single (forecast_p, outcome) observation on
    the outcome-0 YES leg. (One market = one observation; we deliberately do
    NOT double-count the NO leg, which is just the mirror.)"""
    return [(r["forecast_p"], r["won_outcome0"]) for r in rows]


def signal_favorite_longshot(obs):
    """SIGNAL: 'back the favorite at the market price' is the trivial market
    bet; the favorite-longshot *edge* hypothesis is that extreme favorites are
    UNDER-priced and longshots OVER-priced. We test a simple rule: when the
    market price is in the 'favorite' zone (>=0.90), does the realized freq
    exceed the price (market too cheap on favorites)? And symmetrically for
    longshots (<=0.10): is realized freq below price (longshots too expensive)?

    Returns a dict with the favorite/longshot gaps. A positive `favorite_gap`
    (realized - price) means favorites paid more than priced (an edge to buy
    favorites); a positive `longshot_overpricing` (price - realized) means
    longshots were systematically overpriced (an edge to fade longshots)."""
    fav = [(p, y) for p, y in obs if p >= 0.90]
    longshot = [(p, y) for p, y in obs if p <= 0.10]
    out = {}
    if fav:
        out["favorite_n"] = len(fav)
        out["favorite_mean_price"] = round(statistics.fmean(p for p, _ in fav), 4)
        out["favorite_realized_freq"] = round(statistics.fmean(y for _, y in fav), 4)
        out["favorite_gap"] = round(out["favorite_realized_freq"] - out["favorite_mean_price"], 4)
    if longshot:
        out["longshot_n"] = len(longshot)
        out["longshot_mean_price"] = round(statistics.fmean(p for p, _ in longshot), 4)
        out["longshot_realized_freq"] = round(statistics.fmean(y for _, y in longshot), 4)
        out["longshot_overpricing"] = round(out["longshot_mean_price"] - out["longshot_realized_freq"], 4)
    return out


def signal_extremity_vs_market_brier(obs):
    """SIGNAL: 'price-extremity' rule — compare the Brier of always trusting the
    market price against a naive rule that snaps extreme prices to {0,1}
    (i.e. 'when the market is very confident, be MORE confident'). If the
    snapped rule's Brier is lower, extremity is under-confident (an edge);
    if higher, the market's extremes are already well-calibrated or
    over-confident. Threshold for 'extreme' is price<=0.10 or >=0.90."""
    if not obs:
        return {}
    market_brier = statistics.fmean((p - y) ** 2 for p, y in obs)

    def snap(p):
        if p >= 0.90:
            return 0.98
        if p <= 0.10:
            return 0.02
        return p

    snapped_brier = statistics.fmean((snap(p) - y) ** 2 for p, y in obs)
    return {
        "market_brier": round(market_brier, 5),
        "extremity_snapped_brier": round(snapped_brier, 5),
        "extremity_improves_brier": snapped_brier < market_brier,
        "delta": round(market_brier - snapped_brier, 5),  # >0 => snapping helps
    }


def split_in_out_of_sample(rows: list[dict]):
    """Split by resolution date (closed_time) at the median: older half = IN
    (training), newer half = OUT (validation). Returns (in_rows, out_rows,
    split_iso). A signal that 'works' must persist across the split."""
    dated = []
    for r in rows:
        ct = _parse_iso(r.get("closed_time") or r.get("end_date"))
        if ct is not None:
            dated.append((ct, r))
    if len(dated) < 4:
        return rows, [], None
    dated.sort(key=lambda x: x[0])
    mid = len(dated) // 2
    split_dt = dated[mid][0]
    in_rows = [r for ct, r in dated if ct < split_dt]
    out_rows = [r for ct, r in dated if ct >= split_dt]
    return in_rows, out_rows, split_dt.isoformat()


def edge_source_breakdown(rows: list[dict]):
    """Per-category ('edge_source') market-baseline Brier + a crude
    'price-movement-toward-truth' proxy: how far, on average, the pre-close
    forecast had already moved from 0.5 toward the realized outcome. Larger =
    the category resolves informatively early -> CLV is learnable there; tiny =
    coin-flip-like -> little edge for a generalist. Informs cycle-count."""
    by_cat = defaultdict(list)
    for r in rows:
        by_cat[r["category"]].append(r)
    out = []
    for cat, rs in by_cat.items():
        b, n = market_baseline_brier(rs)
        # movement toward truth: |forecast - 0.5| signed toward outcome,
        # averaged. forecast that points the right way from 0.5 scores positive.
        movement = statistics.fmean(
            (r["forecast_p"] - 0.5) * (1 if r["won_outcome0"] == 1 else -1) for r in rs
        )
        out.append(
            {
                "edge_source": cat,
                "n": n,
                "market_brier": None if b is None else round(b, 5),
                "mean_signed_movement_toward_truth": round(movement, 4),
            }
        )
    out.sort(key=lambda x: x["n"], reverse=True)
    return out


# ----------------------------------------------------------------------------
# Cache (for --offline / reproducibility). Cache stores the STAGE-2 rows
# (markets with forecast_p already attached), so replay is exact.
# ----------------------------------------------------------------------------

CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".backtest-cache.json")


def write_cache(rows: list[dict], meta: dict, path: str = CACHE_PATH):
    payload = {"meta": meta, "rows": rows}
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f)
    os.replace(tmp, path)


def read_cache(path: str = CACHE_PATH):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


# ----------------------------------------------------------------------------
# Artifact + report assembly
# ----------------------------------------------------------------------------

ARTIFACT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "bootstrap-calibration.json"
)


def write_template_unrun(reason: str, path: str = ARTIFACT_PATH):
    """Write an empty-schema template clearly marked unrun (network-unreachable
    path). Honest: NO numbers are fabricated."""
    payload = {
        "status": "template_unrun",
        "reason": reason,
        "source": "historical_bootstrap",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": (
            "Live pull did not run (no egress / no cache). Re-run with: "
            "python3 tools/backtest.py --n 500"
        ),
        "calibration_rows": [],  # schema: {price_bin,n,realized_freq,brier_contrib,source}
    }
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, path)


def build_artifact(
    *,
    rows,
    cal_table,
    mkt_brier,
    in_rows,
    out_rows,
    split_iso,
    fav_signal_in,
    fav_signal_out,
    ext_signal_in,
    ext_signal_out,
    cat_table,
    forecast_source,
    lead_hours,
    pull_stats,
    dropped,
):
    """Assemble the machine-readable seeded prior. The `calibration_rows` are
    the heart: skills/recalibrate ingests them as a Bayesian prior keyed by
    price bin (see module docstring + the Phase 4 report)."""
    cal_rows = [
        {
            "price_bin": b["price_bin"],
            "n": b["n"],
            "mean_forecast_p": b["mean_forecast_p"],
            "realized_freq": b["realized_freq"],
            "brier_contrib": b["brier_contrib"],
            "default_price_share": b.get("default_price_share"),
            "low_information_flag": b.get("low_information_flag", False),
            "source": "historical_bootstrap",
        }
        for b in cal_table
    ]

    # A mechanical-signal edge "counts" only if it (a) is present in-sample,
    # (b) keeps the SAME SIGN out-of-sample, and (c) is materially > 0 in BOTH
    # halves (>=1pp). Sign-flip or vanishing magnitude => the in-sample edge was
    # noise. We pick a deliberately conservative 0.01 (1pp) materiality floor.
    _MATERIAL = 0.01

    def verdict(name, in_metric, out_metric, key):
        iv = in_metric.get(key) if in_metric else None
        ov = out_metric.get(key) if out_metric else None
        if iv is None or ov is None:
            return {
                "signal": name,
                "metric": key,
                "in_sample": iv,
                "out_of_sample": ov,
                "persists_across_split": False,
                "beats_market": None,
                "verdict": "insufficient_data",
            }
        same_sign = (iv > 0) == (ov > 0)
        material = abs(iv) >= _MATERIAL and abs(ov) >= _MATERIAL
        beats = bool(same_sign and material and ov > 0)
        return {
            "signal": name,
            "metric": key,
            "in_sample": iv,
            "out_of_sample": ov,
            "persists_across_split": bool(same_sign and material),
            "beats_market": beats,
            "verdict": "edge_persists" if beats else ("sign_flip" if not same_sign else "immaterial_or_negative"),
        }

    # For price_extremity, `delta` (= market_brier - snapped_brier) > 0 means
    # snapping extreme prices toward 0/1 LOWERS Brier, i.e. the market is
    # under-confident at the extremes (an edge to press favorites). Same
    # persistence test as the other signals.
    signal_verdicts = [
        verdict("favorite_longshot", fav_signal_in, fav_signal_out, "favorite_gap"),
        verdict("favorite_longshot", fav_signal_in, fav_signal_out, "longshot_overpricing"),
        verdict("price_extremity", ext_signal_in, ext_signal_out, "delta"),
    ]

    return {
        "status": "ok",
        "source": "historical_bootstrap",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "methodology": {
            "universe": "Polymarket Gamma /markets?closed=true (resolved binary markets)",
            "forecast_price_source": forecast_source,
            "lead_hours_before_close": lead_hours,
            "outcome": "outcome-0 YES leg; realized 0/1 from settlement prices",
            "quality_filter": "clean 0/1 settlement, volume + duration thresholds",
            "note_on_last_trade": (
                "Gamma lastTradePrice for closed markets is CONVERGED (~0/1) and "
                "must NOT be used as the seeded prior; default source is the CLOB "
                "pre-close price."
            ),
        },
        "n_markets_scored": len(rows),
        "n_markets_dropped_no_forecast_price": dropped,
        "market_baseline_brier": None if mkt_brier is None else round(mkt_brier, 5),
        "in_out_of_sample": {
            "split_date": split_iso,
            "in_sample_n": len(in_rows),
            "out_of_sample_n": len(out_rows),
            "in_sample_brier": (lambda b: None if b is None else round(b, 5))(market_baseline_brier(in_rows)[0]),
            "out_of_sample_brier": (lambda b: None if b is None else round(b, 5))(market_baseline_brier(out_rows)[0]),
        },
        "calibration_rows": cal_rows,
        "signal_verdicts": signal_verdicts,
        "signal_detail": {
            "favorite_longshot_in_sample": fav_signal_in,
            "favorite_longshot_out_of_sample": fav_signal_out,
            "price_extremity_in_sample": ext_signal_in,
            "price_extremity_out_of_sample": ext_signal_out,
        },
        "edge_source_breakdown": cat_table,
        "pull_stats": dict(pull_stats),
        "ingestion_contract": {
            "consumer": "skills/recalibrate",
            "how": (
                "Treat each calibration_rows entry as a Beta prior for its price "
                "bin: pseudo-count = n (optionally damped), prior mean = "
                "realized_freq. recalibrate maps Polymarket price bins (0.1 wide) "
                "onto its own lo-hi calibration buckets and seeds bucket "
                "`adjustment`/`status` from the prior until live resolved_n "
                "dominates. DO NOT hand-edit state/calibration.json — live cycles "
                "own it; ingestion is a code path in recalibrate that reads THIS "
                "file and is clearly flagged source:'historical_bootstrap'."
            ),
            "damp_low_information_bins": (
                "Bins with low_information_flag=true (default_price_share>=0.30) "
                "are dominated by illiquid markets parked at the 0.50 CLOB seed "
                "price; their realized_freq is an artifact, not an edge. Down-"
                "weight their pseudo-count (e.g. x0.25) or skip seeding them."
            ),
            "do_not": "Never present these as the agent's own track record.",
        },
    }


def write_artifact(payload: dict, path: str = ARTIFACT_PATH):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, path)


# ----------------------------------------------------------------------------
# Pretty summary
# ----------------------------------------------------------------------------

def print_summary(payload: dict, log=print):
    log("\n" + "=" * 72)
    log("HISTORICAL BOOTSTRAP — SUMMARY")
    log("=" * 72)
    log(f"status                 : {payload['status']}")
    if payload["status"] not in ("ok", "ok_partial"):
        log(f"reason                 : {payload.get('reason')}")
        return
    if payload["status"] == "ok_partial":
        log(f"partial_reason         : {payload.get('partial_reason')}")
    log(f"forecast price source  : {payload['methodology']['forecast_price_source']}")
    log(f"lead hours before close: {payload['methodology']['lead_hours_before_close']}")
    log(f"markets scored         : {payload['n_markets_scored']}")
    log(f"markets dropped (no px): {payload['n_markets_dropped_no_forecast_price']}")
    log(f"market-baseline Brier  : {payload['market_baseline_brier']}")
    ios = payload["in_out_of_sample"]
    log(
        f"in/out split           : {ios['split_date']}  "
        f"(in n={ios['in_sample_n']} Brier={ios['in_sample_brier']} | "
        f"out n={ios['out_of_sample_n']} Brier={ios['out_of_sample_brier']})"
    )
    log("\nprice -> realized-frequency calibration (favorite-longshot curve):")
    log(f"  {'bin':<10}{'n':>6}{'mean_p':>9}{'realized':>10}{'brier':>9}{'dflt%':>7}  flag")

    def _fmt(v, nd):
        return "-" if v is None else f"{v:.{nd}f}"

    for b in payload["calibration_rows"]:
        flag = "LOW-INFO" if b.get("low_information_flag") else ""
        log(
            f"  {b['price_bin']:<10}{b['n']:>6}"
            f"{_fmt(b.get('mean_forecast_p'), 3):>9}"
            f"{_fmt(b.get('realized_freq'), 3):>10}"
            f"{_fmt(b.get('brier_contrib'), 4):>9}"
            f"{_fmt(b.get('default_price_share'), 2):>7}  {flag}"
        )
    log("\nsignal verdicts (must persist across in/out split to count):")
    for v in payload["signal_verdicts"]:
        log(
            f"  - {v['signal']}/{v['metric']}: in={v.get('in_sample')} "
            f"out={v.get('out_of_sample')} -> {v.get('verdict', 'n/a')} "
            f"(beats_market={v.get('beats_market')})"
        )
    log("\nedge_source breakdown (top by n):")
    for c in payload["edge_source_breakdown"][:12]:
        log(
            f"  {c['edge_source'][:28]:<28} n={c['n']:>4} "
            f"brier={c['market_brier']} move_to_truth={c['mean_signed_movement_toward_truth']}"
        )
    log("\nartifact written: " + ARTIFACT_PATH)
    log("=" * 72)


# ----------------------------------------------------------------------------
# Cycle-count recommendation (printed; also folded into the report by hand).
# ----------------------------------------------------------------------------

def cycle_count_note(payload: dict, log=print):
    log("\n" + "-" * 72)
    log("CYCLE-COUNT / EDGE-SOURCE NOTE (decision #2)")
    log("-" * 72)
    cats = payload.get("edge_source_breakdown", [])
    if not cats:
        log("  (insufficient data)")
        return
    # Rank categories by how informatively they resolve (movement toward truth):
    ranked = sorted(cats, key=lambda c: abs(c["mean_signed_movement_toward_truth"]), reverse=True)
    log("  Categories whose price moves most toward truth pre-close (where CLV")
    log("  is most learnable, i.e. worth spending paid cycles on):")
    for c in ranked[:5]:
        log(f"    {c['edge_source'][:30]:<30} move={c['mean_signed_movement_toward_truth']:+.3f} (n={c['n']})")
    log("")
    log("  Interpretation for the ~10/day question is written up in the Phase 4")
    log("  research report; the raw inputs above are the evidence.")


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def build_arg_parser():
    p = argparse.ArgumentParser(
        prog="backtest.py",
        description=(
            "OFFLINE historical bootstrap + backtest for the Polymarket agent "
            "(v3 Phase 4). Pulls resolved markets, computes market-baseline "
            "Brier + a price->frequency calibration table + mechanical-signal "
            "edges with an in/out-of-sample split, and writes a seeded "
            "calibration prior to tools/bootstrap-calibration.json. "
            "Read-only; never touches state/, wallet, or secrets; never trades."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--n", type=int, default=500, help="target number of quality resolved markets to score")
    p.add_argument("--lead-hours", type=float, default=24.0, help="how many hours before close to sample the market's forecast price (clob_pre_close source)")
    p.add_argument("--forecast-source", choices=["clob_pre_close", "last_trade"], default="clob_pre_close", help="clob_pre_close = honest pre-resolution price (default); last_trade = Gamma lastTradePrice (CONVERGED, diagnostic only, NOT for the seeded prior)")
    p.add_argument("--min-volume", type=float, default=1000.0, help="minimum market volume (USDC) to include")
    p.add_argument("--min-duration-days", type=float, default=2.0, help="minimum market lifetime in days (filters out 5-min crypto candles)")
    p.add_argument("--bins", type=int, default=10, help="number of price bins for the calibration table")
    p.add_argument("--timeout", type=float, default=20.0, help="per-request HTTP timeout (seconds)")
    p.add_argument("--retries", type=int, default=3, help="retries per request (exponential backoff)")
    p.add_argument("--backoff", type=float, default=0.5, help="base backoff seconds (doubles each retry)")
    p.add_argument("--max-pages", type=int, default=200, help="max Gamma pages to scan (page size 200)")
    p.add_argument("--overfetch", type=float, default=1.12, help="stage-1 over-pull factor; ~3pct of markets lack CLOB history and get dropped in stage 2, so pull this multiple of --n candidates to still clear the >=N bar")
    p.add_argument("--cache", action="store_true", help="after a live pull, write tools/.backtest-cache.json for reproducible replay")
    p.add_argument("--offline", action="store_true", help="do not hit the network; replay from tools/.backtest-cache.json (fails to template_unrun if absent)")
    p.add_argument("--no-clob-delay", action="store_true", help="disable the polite inter-request delay (faster, less polite)")
    return p


def main(argv=None):
    args = build_arg_parser().parse_args(argv)
    log = print
    polite = 0.0 if args.no_clob_delay else 0.05

    log("polymarket offline backtest — v3 Phase 4")
    log(f"  requests available: {_HAVE_REQUESTS}")
    log(f"  target n={args.n}  forecast_source={args.forecast_source}  lead_hours={args.lead_hours}")

    # ---- OFFLINE replay path -------------------------------------------------
    if args.offline:
        cache = read_cache()
        if not cache or not cache.get("rows"):
            log("OFFLINE: no cache found at " + CACHE_PATH)
            write_template_unrun("offline mode requested but no cache present")
            print_summary({"status": "template_unrun", "reason": "no cache"}, log)
            return 3
        rows = cache["rows"]
        meta = cache.get("meta", {})
        forecast_source = meta.get("forecast_source", args.forecast_source)
        lead_hours = meta.get("lead_hours", args.lead_hours)
        pull_stats = Counter(meta.get("pull_stats", {}))
        dropped = meta.get("dropped", 0)
        log(f"OFFLINE: replaying {len(rows)} cached rows")
    else:
        # ---- LIVE pull ------------------------------------------------------
        try:
            log("\n[stage 1] pulling resolved-market universe from Gamma ...")
            overfetch_n = max(args.n, int(math.ceil(args.n * max(1.0, args.overfetch))))
            candidates, pull_stats = pull_resolved_markets(
                target_n=overfetch_n,
                min_volume=args.min_volume,
                min_duration_days=args.min_duration_days,
                timeout=args.timeout,
                retries=args.retries,
                backoff=args.backoff,
                max_pages=args.max_pages,
                polite_delay=polite,
                log=log,
            )
            log(f"  stage 1 accepted {len(candidates)} quality markets")
            if not candidates:
                raise NetworkError("zero quality markets returned")

            log("\n[stage 2] sampling pre-close forecast prices ...")
            rows, dropped = attach_forecast_prices(
                candidates,
                source=args.forecast_source,
                lead_hours=args.lead_hours,
                timeout=args.timeout,
                retries=args.retries,
                backoff=args.backoff,
                polite_delay=polite,
                log=log,
            )
            forecast_source = args.forecast_source
            lead_hours = args.lead_hours
            log(f"  stage 2 kept {len(rows)} markets with a usable forecast price (dropped {dropped})")
        except NetworkError as e:
            log(f"\nNETWORK UNREACHABLE: {e}")
            cache = read_cache()
            if cache and cache.get("rows"):
                log("  falling back to cache ...")
                rows = cache["rows"]
                meta = cache.get("meta", {})
                forecast_source = meta.get("forecast_source", args.forecast_source)
                lead_hours = meta.get("lead_hours", args.lead_hours)
                pull_stats = Counter(meta.get("pull_stats", {}))
                dropped = meta.get("dropped", 0)
            else:
                write_template_unrun(f"network unreachable and no cache: {e}")
                print_summary({"status": "template_unrun", "reason": str(e)}, log)
                return 3

        if args.cache and not args.offline:
            write_cache(
                rows,
                {
                    "forecast_source": forecast_source,
                    "lead_hours": lead_hours,
                    "pull_stats": dict(pull_stats),
                    "dropped": dropped,
                    "cached_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            log("  cache written: " + CACHE_PATH)

    # ---- compute ------------------------------------------------------------
    if not rows:
        write_template_unrun("no rows with forecast prices after stage 2")
        print_summary({"status": "template_unrun", "reason": "no usable rows"}, log)
        return 2

    mkt_brier, n_scored = market_baseline_brier(rows)
    cal_table = calibration_table(rows, n_bins=args.bins)
    in_rows, out_rows, split_iso = split_in_out_of_sample(rows)

    fav_in = signal_favorite_longshot(_binary_obs_from_rows(in_rows))
    fav_out = signal_favorite_longshot(_binary_obs_from_rows(out_rows))
    ext_in = signal_extremity_vs_market_brier(_binary_obs_from_rows(in_rows))
    ext_out = signal_extremity_vs_market_brier(_binary_obs_from_rows(out_rows))
    cat_table = edge_source_breakdown(rows)

    payload = build_artifact(
        rows=rows,
        cal_table=cal_table,
        mkt_brier=mkt_brier,
        in_rows=in_rows,
        out_rows=out_rows,
        split_iso=split_iso,
        fav_signal_in=fav_in,
        fav_signal_out=fav_out,
        ext_signal_in=ext_in,
        ext_signal_out=ext_out,
        cat_table=cat_table,
        forecast_source=forecast_source,
        lead_hours=lead_hours,
        pull_stats=pull_stats,
        dropped=dropped,
    )

    # Flag insufficient-N honestly but still write the artifact.
    if n_scored < args.n:
        payload["status"] = "ok_partial"
        payload["partial_reason"] = (
            f"scored {n_scored} < target {args.n}; acceptance wants >=500. "
            f"Increase --max-pages or relax --min-volume/--min-duration-days."
        )

    write_artifact(payload)
    print_summary(payload, log)
    cycle_count_note(payload, log)

    if n_scored < 500:
        log(f"\nNOTE: only {n_scored} markets scored (<500 acceptance bar).")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
