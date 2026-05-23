"""Fetch daily OHLCV history, normalized and cached.

KR via pykrx, US via yfinance. Both are normalized to a DataFrame indexed by
date (ascending) with columns: open, high, low, close, volume.
"""
from __future__ import annotations

import datetime as dt
from typing import Optional

import pandas as pd

from . import cache


def _normalize(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    df = df.rename(columns=mapping)
    keep = ["open", "high", "low", "close", "volume"]
    df = df[[c for c in keep if c in df.columns]].copy()
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="last")]
    return df.dropna(how="all")


def _fetch_kr(ticker: str, years: int) -> Optional[pd.DataFrame]:
    from pykrx import stock

    end = dt.date.today()
    start = end - dt.timedelta(days=int(years * 365.25) + 10)
    raw = stock.get_market_ohlcv(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), ticker)
    if raw is None or raw.empty:
        return None
    return _normalize(
        raw,
        {"시가": "open", "고가": "high", "저가": "low", "종가": "close", "거래량": "volume"},
    )


def _fetch_us(ticker: str, years: int) -> Optional[pd.DataFrame]:
    import yfinance as yf

    period = f"{years}y"
    raw = yf.download(
        ticker, period=period, interval="1d",
        auto_adjust=True, progress=False, threads=False,
    )
    if raw is None or raw.empty:
        return None
    # yfinance may return a MultiIndex column frame for single tickers
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    return _normalize(
        raw,
        {"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"},
    )


def get_prices(
    market: str,
    ticker: str,
    years: int = 5,
    max_age_days: float = 1.0,
    use_cache: bool = True,
) -> Optional[pd.DataFrame]:
    if use_cache:
        cached = cache.load_prices(market, ticker, max_age_days)
        if cached is not None:
            return cached
    try:
        df = _fetch_kr(ticker, years) if market == "KR" else _fetch_us(ticker, years)
    except Exception:
        return None
    if df is None or df.empty:
        return None
    cache.save_prices(market, ticker, df)
    return df
