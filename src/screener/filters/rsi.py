"""RSI below a threshold (oversold) — or above, via the direction param."""
from __future__ import annotations

from .. import indicators
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    close = data.prices["close"].dropna()
    if len(close) < p["period"] + 5:
        return FilterOutcome(passed=False, detail="짧은 시계열")
    r = indicators.rsi(close, int(p["period"])).iloc[-1]
    if r != r:  # NaN
        return FilterOutcome(passed=False, detail="—")
    thr = p["threshold"]
    if p["direction"] == "이하(과매도)":
        ok = r <= thr
    else:
        ok = r >= thr
    return FilterOutcome(passed=bool(ok), detail=f"RSI {r:.0f}", value=float(r))


register(
    Filter(
        key="rsi",
        label="RSI 임계",
        description="RSI가 지정 임계값 이하(과매도) 또는 이상인 종목.",
        params=[
            Param("period", "기간", "int", default=14, min=2, max=50, step=1),
            Param("threshold", "임계값", "int", default=35, min=5, max=95, step=1),
            Param(
                "direction",
                "방향",
                "select",
                default="이하(과매도)",
                choices=["이하(과매도)", "이상"],
            ),
        ],
        fn=_apply,
    )
)
