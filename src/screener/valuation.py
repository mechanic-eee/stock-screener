"""Valuation / quality multiples — is the fallen stock actually *cheap*?

A −60% drawdown isn't the same as cheap: a former bubble can still be expensive,
while a solid business below book is a bargain. This adds the valuation
dimension (PER, PBR, ROE, dividend yield) the screen otherwise lacks.

US: yfinance `.info` (trailing PE, price/book, ROE, dividend yield).
KR: computed from market cap (tickers table) + DART equity/net-income (reuses
the fundamentals cache). KR net income is annualized from the latest report's
cumulative figure — a screening estimate, not audited TTM.

Missing data -> unavailable bundle -> neutral 50 (fail-soft).
"""
from __future__ import annotations

import logging
from typing import Optional

from . import fundamentals as fundamentals_mod
from .data import db as db_mod
from .models import ValuationBundle

log = logging.getLogger(__name__)

# cumulative report period -> annualization factor (period-end month -> x)
_ANNUALIZE = {3: 4.0, 6: 2.0, 9: 4.0 / 3.0, 12: 1.0}

# Per-process cache of precomputed bundles, keyed by ticker. The hosted app can't
# fetch yfinance `.info` / DART live (blocked/rate-limited), so the daily scan
# bakes valuation bundles into a sidecar and the app primes them here — then
# get_valuation() returns the cached bundle with no network call.
_primed: dict[str, ValuationBundle] = {}


def prime(mapping: dict[str, ValuationBundle]) -> None:
    """Seed the per-process valuation cache from a precomputed source (snapshot)."""
    for ticker, vb in mapping.items():
        if vb is not None:
            _primed[str(ticker)] = vb


def _us_valuation_info(ticker: str) -> ValuationBundle:
    """Richest US source (PER/PBR/ROE + dividend), but Yahoo blocks `.info` from
    datacenter IPs (GitHub Actions), so it's the fallback, not the primary path."""
    import yfinance as yf

    try:
        info = yf.Ticker(ticker).info
    except Exception as e:  # noqa: BLE001 — fail-soft
        log.warning("valuation .info failed US/%s: %s", ticker, e)
        return ValuationBundle(available=False)
    per = info.get("trailingPE")
    pbr = info.get("priceToBook")
    roe = info.get("returnOnEquity")          # already a fraction
    dy = info.get("dividendYield")            # yfinance returns this in percent
    if all(v is None for v in (per, pbr, roe, dy)):
        return ValuationBundle(available=False)
    return ValuationBundle(
        available=True,
        per=float(per) if per else None,
        pbr=float(pbr) if pbr else None,
        roe=float(roe) if roe is not None else None,
        dividend_yield=(float(dy) / 100.0) if dy else None,
    )


def _market_cap(ticker: str) -> Optional[float]:
    conn = db_mod.get_connection()
    try:
        r = conn.execute("SELECT market_cap FROM tickers WHERE ticker=?", (ticker,)).fetchone()
        return float(r[0]) if r and r[0] else None
    finally:
        conn.close()


def _fast_info_market_cap(ticker: str) -> Optional[float]:
    """Market cap via yfinance fast_info — the quote (v8) endpoint, same family
    as the price download that works fine on datacenter IPs (unlike `.info`)."""
    import yfinance as yf

    try:
        fi = yf.Ticker(ticker).fast_info
        # FastInfo: attribute access is snake_case (.market_cap); its .get() uses
        # camelCase ("marketCap"). Use the attribute to avoid that mismatch.
        mc = getattr(fi, "market_cap", None)
        return float(mc) if mc else None
    except Exception as e:  # noqa: BLE001 — fail-soft
        log.warning("fast_info market cap failed US/%s: %s", ticker, e)
        return None


def _raw(market: str, ticker: str) -> Optional[dict]:
    """Latest cached fundamentals (ensuring a fetch first). For US, a cache row
    predating the `shares` column (NULL shares) is refreshed once so the
    price-based market cap can be computed."""
    fundamentals_mod.get_fundamentals(market, ticker)  # ensure cached
    raw = fundamentals_mod.latest_raw(ticker)
    if market == "US" and raw is not None and raw.get("shares") is None:
        fundamentals_mod.get_fundamentals(market, ticker, use_cache=False)
        raw = fundamentals_mod.latest_raw(ticker)
    return raw


def _bundle_from(raw: Optional[dict], market_cap: Optional[float]) -> ValuationBundle:
    """PER/PBR/ROE from market cap + latest cached fundamentals (equity, net
    income). ROE needs no market cap, so it's available even when the cap is
    missing. Net income is annualized from the cumulative report — a screening
    estimate, not audited TTM. Dividend yield is unavailable on this path."""
    if not raw or not raw.get("total_equity"):
        return ValuationBundle(available=False)

    equity = float(raw["total_equity"])
    ni = raw.get("net_income")
    month = int(raw["period"][5:7]) if raw.get("period") else 12
    ni_annual = float(ni) * _ANNUALIZE.get(month, 1.0) if ni is not None else None

    pbr = market_cap / equity if (market_cap and equity > 0) else None
    per = market_cap / ni_annual if (market_cap and ni_annual and ni_annual > 0) else None
    roe = ni_annual / equity if (ni_annual is not None and equity > 0) else None
    if all(v is None for v in (per, pbr, roe)):
        return ValuationBundle(available=False)
    return ValuationBundle(available=True, per=per, pbr=pbr, roe=roe, dividend_yield=None)


def _kr_valuation(ticker: str) -> ValuationBundle:
    return _bundle_from(_raw("KR", ticker), _market_cap(ticker))


def _us_valuation(ticker: str, last_price: Optional[float] = None) -> ValuationBundle:
    # Yahoo blocks .info AND fast_info from datacenter IPs (GitHub Actions), so
    # derive the market cap from the snapshot price x balance-sheet shares (both
    # from endpoints that work there). fast_info / .info are local-only fallbacks.
    raw = _raw("US", ticker)
    market_cap = None
    if raw and last_price and raw.get("shares"):
        market_cap = float(last_price) * float(raw["shares"])
    if market_cap is None:
        market_cap = _fast_info_market_cap(ticker)
    bundle = _bundle_from(raw, market_cap)
    if bundle.available:
        return bundle
    return _us_valuation_info(ticker)


def get_valuation(market: str, ticker: str, last_price: Optional[float] = None) -> ValuationBundle:
    """Valuation multiples for a ticker; available=False -> treat as neutral.

    `last_price` (latest close) lets US valuation compute market cap as
    price x shares when `.info`/`fast_info` are blocked (the hosted/Actions case).
    """
    cached = _primed.get(ticker)
    if cached is not None:
        return cached
    try:
        return _us_valuation(ticker, last_price) if market == "US" else _kr_valuation(ticker)
    except Exception as e:  # noqa: BLE001 — never kill the scan
        log.warning("valuation failed %s/%s: %s", market, ticker, e)
        return ValuationBundle(available=False)
