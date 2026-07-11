"""Market benchmark price series, for relative-strength comparison.

Reuses the price fetch+SQLite cache (the index is fetched like any ticker:
US=^GSPC via yfinance, KR=KS11 via FinanceDataReader) and memoizes per process,
so a whole scan compares against one benchmark fetched once.
"""
from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

from .data import prices as prices_mod

log = logging.getLogger(__name__)

_BENCH = {"US": "^GSPC", "KR": "KS11"}  # S&P 500, KOSPI
_cache: dict[str, Optional[pd.Series]] = {}


def prime(mapping: dict[str, Optional[pd.Series]]) -> None:
    """Seed the per-process cache from a precomputed source (e.g. the snapshot).

    The hosted app can't reliably fetch ^GSPC/KS11 live (rate-limited/blocked),
    so the daily scan bakes the benchmark series into the snapshot and the app
    primes them here — get_benchmark() then returns the cached series without
    any network call, and the relative-strength filter actually works.
    """
    for market, series in mapping.items():
        if series is not None and not series.empty:
            s = series.dropna()
            s.index = pd.to_datetime(s.index)
            _cache[market] = s


def peek(market: str) -> Optional[pd.Series]:
    """Cached/primed-only lookup — never triggers a live fetch.

    The app's header renders on every rerun; on the hosted app a cache miss in
    get_benchmark() would block first paint on a (datacenter-blocked) network
    call. The regime badge therefore only ever *peeks*.
    """
    return _cache.get(market)


def get_benchmark(market: str, years: int = 2) -> Optional[pd.Series]:
    """Benchmark close series for a market (date-indexed), or None if unavailable."""
    if market in _cache:
        return _cache[market]
    series: Optional[pd.Series] = None
    sym = _BENCH.get(market)
    if sym:
        try:
            df = prices_mod.get_prices(market, sym, years=years)
            if df is not None and not df.empty:
                s = df["close"].dropna()
                s.index = pd.to_datetime(s.index)
                series = s
        except Exception as e:  # noqa: BLE001 — fail-soft to neutral RS
            log.warning("benchmark fetch failed %s: %s", market, e)
    _cache[market] = series
    return series
