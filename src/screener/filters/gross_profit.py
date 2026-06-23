"""Gross profitability — a temporarily cheap good business vs a dying one.

Novy-Marx (2013): gross profit / total assets has B/M-level cross-sectional
predictive power and is roughly orthogonal to value. Gross profit is the
cleanest line on the income statement (least subject to accounting discretion),
so it's the best single 'quality' tell for separating a structurally profitable
business that merely fell from a value trap that is quietly dying.

Needs the fundamentals bundle; fail-soft to neutral 50 / available=False when
gross profit or assets are missing (e.g. banks). Default scorer.
"""
from __future__ import annotations

from .. import scoring
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    fb = data.fundamentals
    if fb is None or not fb.available or fb.gross_profitability is None:
        return FilterOutcome(passed=True, detail="GP 없음", score=50.0, available=False)
    g = fb.gross_profitability
    score = scoring.gross_profitability_score(g)
    return FilterOutcome(
        passed=score >= float(p["min_score"]),
        detail=f"GP/자산 {g * 100:.0f}% ({score:.0f})",
        value=round(g, 4),
        score=score,
    )


register(
    Filter(
        key="gross_profit",
        label="퀄리티(매출총이익률)",
        description="매출총이익/총자산. 높을수록 구조적으로 돈 버는 사업(가치함정=끝없이 싼 죽은 사업 회피). "
        "밸류(PER/PBR)와 직교 결합 시 '싸면서 좋은' 종목 변별. 기본 점수만.",
        needs_fundamentals=True,
        weight=0.10,
        params=[
            Param("min_score", "통과 최소 점수", "float", default=0.0, min=0.0, max=100.0, step=5.0),
        ],
        fn=_apply,
    )
)
