"""Volatility contraction (base building) — has the fall stopped and tightened?

After a big drawdown, a sideways base with *contracting* volatility often
precedes a real turn (Minervini's VCP idea). Proxy: Bollinger band width
((upper-lower)/mid). We score how tight the latest band width is versus its own
trailing distribution — the tighter (lower percentile), the higher the score.
Directly targets this strategy's main failure mode: catching a still-falling
knife instead of a stock that has actually based.

Pure pandas. Default scorer; raise min_score to require a tight base as a gate.
"""
from __future__ import annotations

from .. import indicators, scoring
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    close = data.prices["close"].dropna()
    bb_window = int(p["bb_window"])
    lookback = int(p["lookback"])
    if len(close) < bb_window + lookback // 2:
        return FilterOutcome(passed=False, detail="짧은 시계열")

    mid, upper, lower = indicators.bollinger(close, window=bb_window, num_std=2.0)
    width = ((upper - lower) / mid).dropna()
    if len(width) < 5:
        return FilterOutcome(passed=False, detail="밴드폭 부족")

    look = width.tail(lookback)
    cur = float(width.iloc[-1])
    # percentile of current width within the trailing window (0 = tightest)
    pctile = float((look <= cur).mean())
    score = scoring.contraction_score(pctile)
    state = "수축(베이스)" if pctile <= 0.3 else ("보통" if pctile <= 0.6 else "확장(변동성↑)")
    return FilterOutcome(
        passed=score >= float(p["min_score"]),
        detail=f"밴드폭 {cur * 100:.0f}% {state} ({score:.0f})",
        value=pctile,
        score=score,
    )


register(
    Filter(
        key="vcp_contraction",
        label="변동성 수축(베이스)",
        description="볼린저 밴드폭이 자기 과거 분포 대비 얼마나 좁아졌는지로 베이스 형성을 점수화. "
        "수축=하락 멈추고 다지는 중(고점수), 확장=변동성 큼(저점수). falling knife 회피용. "
        "기본은 점수만 기여, '통과 최소 점수'를 올리면 게이트.",
        weight=0.10,
        params=[
            Param("bb_window", "볼린저 기간", "int", default=20, min=5, max=60, step=1),
            Param("lookback", "백분위 비교 거래일", "int", default=120, min=20, max=250, step=10,
                  help="현재 밴드폭을 비교할 과거 거래일 수."),
            Param("min_score", "통과 최소 점수", "float", default=0.0, min=0.0, max=100.0, step=5.0),
        ],
        fn=_apply,
    )
)
