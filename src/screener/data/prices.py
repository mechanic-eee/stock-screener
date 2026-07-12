"""Fetch daily OHLCV with retries, caching to SQLite.

KR via pykrx (adjusted), US via yfinance (keeps Adj Close). Internally we store
open/high/low/close/adj_close/volume; the cache returns a screening frame whose
`close` is the adjusted close. Robustness (retries, backoff, optional sleep) is
ported from the predecessor project's chunk fetchers.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from . import cache

log = logging.getLogger(__name__)


def _fetch_kr(ticker: str, years: int) -> Optional[pd.DataFrame]:
    # FinanceDataReader returns adjusted prices; no KRX login needed.
    import FinanceDataReader as fdr

    start = (datetime.now() - timedelta(days=years * 365 + 30)).strftime("%Y-%m-%d")
    raw = fdr.DataReader(ticker, start)
    if raw is None or raw.empty:
        return None
    raw = raw.rename(columns={"Open": "open", "High": "high", "Low": "low",
                              "Close": "close", "Volume": "volume"})
    raw["adj_close"] = raw["close"]  # FDR Close is already adjusted
    raw.index = pd.to_datetime(raw.index)
    return raw[["open", "high", "low", "close", "adj_close", "volume"]]


def _fetch_us(ticker: str, years: int) -> Optional[pd.DataFrame]:
    import yfinance as yf

    end = datetime.now()
    start = end - timedelta(days=years * 365 + 30)
    yt = yf.Ticker(ticker)
    raw = yt.history(start=start, end=end, auto_adjust=False, raise_errors=False)
    if raw is None or raw.empty:
        return None
    raw = raw.rename(columns={"Open": "open", "High": "high", "Low": "low",
                              "Close": "close", "Adj Close": "adj_close", "Volume": "volume"})
    if "adj_close" not in raw.columns:
        raw["adj_close"] = raw["close"]
    raw.index = pd.to_datetime(raw.index).tz_localize(None)
    return raw[["open", "high", "low", "close", "adj_close", "volume"]]


def _fetch(market: str, ticker: str, years: int, max_retries: int = 3) -> Optional[pd.DataFrame]:
    last_err = None
    for attempt in range(max_retries):
        try:
            df = _fetch_kr(ticker, years) if market == "KR" else _fetch_us(ticker, years)
            if df is None or df.empty:
                return None
            return df.sort_index()[~df.sort_index().index.duplicated(keep="last")]
        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    log.warning("fetch failed %s/%s: %s", market, ticker, last_err)
    return None


def get_prices(
    market: str,
    ticker: str,
    years: int = 5,
    max_age_days: float = 1.0,
    use_cache: bool = True,
    sleep_between: float = 0.0,
) -> Optional[pd.DataFrame]:
    """Return a screening frame (index=date; open/high/low/close[=adj]/volume)."""
    if use_cache:
        cached = cache.load_prices(market, ticker, max_age_days)
        if cached is not None:
            return cached
    df = _fetch(market, ticker, years)
    if sleep_between:
        time.sleep(sleep_between)
    if df is None or df.empty:
        return None
    # adj_close is NOT NULL in the DB: fill from close, then drop rows still empty
    df = df.copy()
    df["adj_close"] = df["adj_close"].fillna(df["close"])
    df = df.dropna(subset=["adj_close"])
    if df.empty:
        return None
    try:
        cache.save_prices(market, ticker, df)
    except Exception as e:  # noqa: BLE001 — one bad ticker must not kill the scan
        log.warning("cache save failed %s/%s: %s", market, ticker, e)
    # canonical screening shape: adjusted close, O/H/L scaled to match
    return cache.screen_frame(df)
