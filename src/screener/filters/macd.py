"""MACD turning bullish within the last N days.

Detects two signal types (PRD §4.5): a zero-line cross (DIF -> +) and a
signal-line cross. The freshest cross in the window sets the age; same-day
ties prefer the zero-line cross. Score decays with age, +10 for zero cross.
"""
from __future__ import annotations

from .. import indicators, scoring
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    close = data.prices["close"].dropna()
    if len(close) < p["slow"] + p["signal"] + 5:
        return FilterOutcome(passed=False, detail="짧은 시계열")

    macd_line, signal_line, _ = indicators.macd(close, p["fast"], p["slow"], p["signal"])
    zc = (macd_line > 0) & (macd_line.shift(1, fill_value=0) <= 0)
    diff = macd_line - signal_line
    sc = (diff > 0) & (diff.shift(1, fill_value=0) <= 0)

    window = int(p["within_days"])
    zc_recent = zc.tail(window)
    sc_recent = sc.tail(window)
    if not (zc_recent.any() or sc_recent.any()):
        return FilterOutcome(passed=False, detail="—", score=0.0)

    # age in trading days back from the latest bar (0 = today)
    n = len(close)
    zc_age = (n - 1 - zc[zc].index.map(close.index.get_loc).max()) if zc_recent.any() else 1e9
    sc_age = (n - 1 - sc[sc].index.map(close.index.get_loc).max()) if sc_recent.any() else 1e9
    if zc_age <= sc_age:
        age, is_zero = int(zc_age), True
    else:
        age, is_zero = int(sc_age), False

    label = "MACD0↑" if is_zero else "MACD↑"
    return FilterOutcome(
        passed=True,
        detail=f"{label}{age}d",
        value=float(macd_line.iloc[-1]),
        score=scoring.macd_score(max(1, age + 1), is_zero),
    )


register(
    Filter(
        key="macd_cross",
        label="MACD 음→양 전환",
        description="최근 N일 안에 MACD선이 0선 또는 시그널선을 상향 돌파한 종목. 최근일수록 고점수.",
        weight=0.10,
        params=[
            Param("fast", "Fast EMA", "int", default=12, min=2, max=50, step=1),
            Param("slow", "Slow EMA", "int", default=26, min=5, max=100, step=1),
            Param("signal", "Signal", "int", default=9, min=2, max=50, step=1),
            Param("within_days", "최근 N일 내 전환", "int", default=3, min=1, max=30, step=1),
        ],
        fn=_apply,
    )
)
