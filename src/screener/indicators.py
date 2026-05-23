"""Technical indicators in pure pandas.

Deliberately dependency-free (no pandas-ta / TA-Lib) so the project stays
portable across Python versions and new indicators are easy to add.
All functions take/return pandas objects aligned to the price index.
"""
from __future__ import annotations

import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Return (macd_line, signal_line, histogram)."""
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    # Wilder's smoothing
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def bollinger(close: pd.Series, window: int = 20, num_std: float = 2.0):
    """Return (mid, upper, lower)."""
    mid = sma(close, window)
    std = close.rolling(window).std()
    return mid, mid + num_std * std, mid - num_std * std


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume: cumulative volume signed by daily price direction.

    Uses close only (no high/low), so it's unaffected by the screening frame
    mixing adjusted close with unadjusted OHL.
    """
    direction = close.diff().fillna(0.0)
    signed = volume.where(direction > 0, -volume).where(direction != 0, 0.0)
    return signed.cumsum()


def drawdown_from_high(close: pd.Series, lookback_days: int | None = None) -> float:
    """Percent drop of the latest close below the rolling-window high.

    Returns a positive percentage (e.g. 82.0 means the latest close is 82%
    below the highest close in the window). lookback_days=None uses the whole
    series.
    """
    s = close.dropna()
    if s.empty:
        return float("nan")
    window = s if lookback_days is None else s.tail(lookback_days)
    peak = window.max()
    last = s.iloc[-1]
    if peak <= 0:
        return float("nan")
    return float((1 - last / peak) * 100)
