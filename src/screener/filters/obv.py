"""On-Balance Volume accumulation — is smart money quietly buying the bottom?

Sums volume signed by daily price direction, then scores the net change over a
lookback window as a fraction of total volume traded: strongly positive means
accumulation (up-volume dominated), negative means distribution. Orthogonal to
the volume-spike filter, which only sees a single-day surge.

Pure pandas, uses adjusted close only. Default is a pure scorer (min_score=0);
raise min_score to require accumulation as a gate.
"""
from __future__ import annotations

from .. import indicators, scoring
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    close = data.prices["close"].dropna()
    volume = data.prices["volume"].reindex(close.index).fillna(0.0)
    window = int(p["window"])
    if len(close) < window + 2:
        return FilterOutcome(passed=False, detail="짧은 시계열")

    obv = indicators.obv(close, volume)
    vol_sum = float(volume.tail(window).sum())
    if vol_sum <= 0:
        return FilterOutcome(passed=False, detail="거래량 없음", score=0.0)
    net_ratio = float(obv.iloc[-1] - obv.iloc[-1 - window]) / vol_sum
    score = scoring.obv_accumulation_score(net_ratio)
    arrow = "매집↑" if net_ratio > 0.05 else ("분산↓" if net_ratio < -0.05 else "중립")
    return FilterOutcome(
        passed=score >= float(p["min_score"]),
        detail=f"OBV {arrow} {net_ratio * 100:+.0f}% ({score:.0f})",
        value=net_ratio,
        score=score,
    )


register(
    Filter(
        key="obv_accumulation",
        label="OBV 누적매집",
        description="최근 N일 OBV(거래량 방향성 누적) 변화를 거래량 대비 비율로 점수화. "
        "양수=매집(상승일 거래량 우세), 음수=분산. 거래량 스파이크와 달리 '지속 매집'을 봄. "
        "기본은 점수만 기여, '통과 최소 점수'를 올리면 게이트.",
        weight=0.0,  # anti-predictive: negative IC in both markets (KR t−2.3~−3.0,
        # score-validation-2026-06-27) — out of the composite (still a usable gate).
        params=[
            Param("window", "관찰 거래일", "int", default=30, min=5, max=120, step=5,
                  help="OBV 변화를 측정할 최근 거래일 수."),
            Param("min_score", "통과 최소 점수", "float", default=0.0, min=0.0, max=100.0, step=5.0,
                  help="0이면 제외하지 않고 점수만 기여. 올리면 매집 약한 종목을 거름."),
        ],
        fn=_apply,
    )
)
