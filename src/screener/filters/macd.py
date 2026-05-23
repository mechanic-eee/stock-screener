"""MACD turning bullish: MACD line crosses above signal within the last N days."""
from __future__ import annotations

from .. import indicators
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    close = data.prices["close"].dropna()
    if len(close) < p["slow"] + p["signal"] + 5:
        return FilterOutcome(passed=False, detail="짧은 시계열")
    macd_line, signal_line, _ = indicators.macd(close, p["fast"], p["slow"], p["signal"])
    above = macd_line > signal_line
    # bullish cross = was below/equal yesterday, above today
    cross_up = above & ~above.shift(1).fillna(False)
    window = int(p["within_days"])
    recent = cross_up.tail(window)
    crossed = bool(recent.any())
    detail = "MACD↑" if crossed else "—"
    return FilterOutcome(passed=crossed, detail=detail, value=float(macd_line.iloc[-1]))


register(
    Filter(
        key="macd_cross",
        label="MACD 음→양 전환",
        description="최근 N일 안에 MACD선이 시그널선을 상향 돌파(골든크로스)한 종목.",
        params=[
            Param("fast", "Fast EMA", "int", default=12, min=2, max=50, step=1),
            Param("slow", "Slow EMA", "int", default=26, min=5, max=100, step=1),
            Param("signal", "Signal", "int", default=9, min=2, max=50, step=1),
            Param("within_days", "최근 N일 내 전환", "int", default=5, min=1, max=30, step=1),
        ],
        fn=_apply,
    )
)
