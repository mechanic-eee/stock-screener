"""Base screen: close is >= X% below its N-year high (always on)."""
from __future__ import annotations

from .. import indicators
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register

TRADING_DAYS_PER_YEAR = 252


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    years = p["years"]
    threshold = p["min_drop_pct"]
    lookback = int(years * TRADING_DAYS_PER_YEAR)
    dd = indicators.drawdown_from_high(data.prices["close"], lookback_days=lookback)
    if dd != dd:  # NaN
        return FilterOutcome(passed=False, detail="no data")
    return FilterOutcome(
        passed=dd >= threshold,
        detail=f"-{dd:.0f}%",
        value=dd,
    )


register(
    Filter(
        key="drawdown",
        label="고가 대비 폭락 (기본)",
        description="종가가 최근 N년 최고가 대비 일정 비율 이상 하락한 종목만 통과시키는 기본 스크린.",
        is_base=True,
        params=[
            Param("years", "기준 기간(년)", "int", default=5, min=1, max=10, step=1),
            Param(
                "min_drop_pct",
                "최소 하락률(%)",
                "int",
                default=80,
                min=30,
                max=95,
                step=1,
                help="고가 대비 이 % 이상 떨어진 종목만 후보로.",
            ),
        ],
        fn=_apply,
    )
)
