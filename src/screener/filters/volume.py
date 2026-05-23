"""Volume surge: recent average volume well above its longer-term average.

A spike in volume on a beaten-down name often marks accumulation / a turn.
"""
from __future__ import annotations

from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    vol = data.prices["volume"].dropna()
    short_w = int(p["short_window"])
    long_w = int(p["long_window"])
    if len(vol) < long_w + 1:
        return FilterOutcome(passed=False, detail="짧은 시계열")
    short_avg = vol.tail(short_w).mean()
    long_avg = vol.tail(long_w).mean()
    if long_avg <= 0:
        return FilterOutcome(passed=False, detail="—")
    ratio = short_avg / long_avg
    return FilterOutcome(
        passed=ratio >= p["min_ratio"],
        detail=f"거래량 {ratio:.1f}x",
        value=float(ratio),
    )


register(
    Filter(
        key="volume_surge",
        label="거래량 급증",
        description="최근 단기 평균 거래량이 장기 평균 대비 배수 이상으로 늘어난 종목.",
        params=[
            Param("short_window", "단기 평균(일)", "int", default=5, min=2, max=30, step=1),
            Param("long_window", "장기 평균(일)", "int", default=60, min=20, max=250, step=5),
            Param("min_ratio", "최소 배수", "float", default=1.5, min=1.0, max=10.0, step=0.1),
        ],
        fn=_apply,
    )
)
