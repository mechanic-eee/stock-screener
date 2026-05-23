"""Bollinger band position — e.g. price bouncing off the lower band."""
from __future__ import annotations

from .. import indicators
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    close = data.prices["close"].dropna()
    window = int(p["window"])
    if len(close) < window + 2:
        return FilterOutcome(passed=False, detail="짧은 시계열")
    mid, upper, lower = indicators.bollinger(close, window, float(p["num_std"]))
    last = close.iloc[-1]
    lo, up = lower.iloc[-1], upper.iloc[-1]
    if up == lo or up != up:
        return FilterOutcome(passed=False, detail="—")
    pctb = (last - lo) / (up - lo)  # 0 = lower band, 1 = upper band
    if p["mode"] == "하단 부근(반등 후보)":
        ok = pctb <= p["pctb_threshold"]
    else:
        ok = pctb >= p["pctb_threshold"]
    return FilterOutcome(passed=bool(ok), detail=f"%B {pctb:.2f}", value=float(pctb))


register(
    Filter(
        key="bollinger",
        label="볼린저밴드 위치",
        description="%B(밴드 내 위치)로 하단 부근(반등 후보) 또는 상단 부근 종목을 거른다.",
        params=[
            Param("window", "기간(일)", "int", default=20, min=5, max=100, step=1),
            Param("num_std", "표준편차 배수", "float", default=2.0, min=1.0, max=4.0, step=0.1),
            Param(
                "mode",
                "조건",
                "select",
                default="하단 부근(반등 후보)",
                choices=["하단 부근(반등 후보)", "상단 부근"],
            ),
            Param("pctb_threshold", "%B 임계", "float", default=0.2, min=0.0, max=1.0, step=0.05),
        ],
        fn=_apply,
    )
)
