"""Price reclaiming a moving average — a basic trend-turn confirmation."""
from __future__ import annotations

from .. import indicators
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    close = data.prices["close"].dropna()
    window = int(p["window"])
    if len(close) < window + 2:
        return FilterOutcome(passed=False, detail="짧은 시계열")
    ma = indicators.sma(close, window)
    last_close = close.iloc[-1]
    last_ma = ma.iloc[-1]
    if last_ma != last_ma:
        return FilterOutcome(passed=False, detail="—")
    above = last_close > last_ma
    if p["mode"] == "MA 상향 돌파(최근)":
        was_below = close.iloc[-2] <= ma.iloc[-2]
        ok = above and was_below
        detail = "MA돌파" if ok else "—"
    else:  # "MA 위"
        ok = above
        detail = "MA위" if ok else "MA아래"
    return FilterOutcome(passed=bool(ok), detail=detail, value=float(last_close / last_ma - 1) * 100)


register(
    Filter(
        key="moving_average",
        label="이동평균선",
        description="종가가 N일 이동평균선을 상향 돌파했거나 그 위에 있는 종목.",
        params=[
            Param("window", "이동평균 기간(일)", "int", default=20, min=5, max=200, step=1),
            Param(
                "mode",
                "조건",
                "select",
                default="MA 상향 돌파(최근)",
                choices=["MA 상향 돌파(최근)", "MA 위"],
            ),
        ],
        fn=_apply,
    )
)
