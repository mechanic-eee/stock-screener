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


def _us_valuation(ticker: str) -> ValuationBundle:
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


def _kr_valuation(ticker: str) -> ValuationBundle:
    market_cap = _market_cap(ticker)
    # ensure DART financials are cached, then read the latest raw figures
    fundamentals_mod.get_fundamentals("KR", ticker)
    raw = fundamentals_mod.latest_raw(ticker)
    if not market_cap or not raw or not raw.get("total_equity"):
        return ValuationBundle(available=False)

    equity = float(raw["total_equity"])
    ni = raw.get("net_income")
    month = int(raw["period"][5:7]) if raw.get("period") else 12
    ni_annual = float(ni) * _ANNUALIZE.get(month, 1.0) if ni is not None else None

    pbr = market_cap / equity if equity > 0 else None
    per = market_cap / ni_annual if (ni_annual and ni_annual > 0) else None
    roe = ni_annual / equity if (ni_annual is not None and equity > 0) else None
    if all(v is None for v in (per, pbr, roe)):
        return ValuationBundle(available=False)
    return ValuationBundle(available=True, per=per, pbr=pbr, roe=roe, dividend_yield=None)


def get_valuation(market: str, ticker: str) -> ValuationBundle:
    """Valuation multiples for a ticker; available=False -> treat as neutral."""
    cached = _primed.get(ticker)
    if cached is not None:
        return cached
    try:
        return _us_valuation(ticker) if market == "US" else _kr_valuation(ticker)
    except Exception as e:  # noqa: BLE001 — never kill the scan
        log.warning("valuation failed %s/%s: %s", market, ticker, e)
        return ValuationBundle(available=False)
