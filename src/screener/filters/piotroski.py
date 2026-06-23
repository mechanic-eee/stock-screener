"""Piotroski F-score — is a fallen, cheap company actually getting healthier?

Piotroski designed the 9-point checklist (profitability, leverage/liquidity,
operating efficiency) specifically to separate winners from losers *inside* a
beaten-down low-P/B universe — exactly this screener's job. The four trend
signals (ΔROA, CFO>NI, Δleverage, Δmargin) are a dimension none of the other
filters capture: not a level, but whether the financials are *turning*.

Needs the fundamentals bundle (fetched lazily for survivors). Fail-soft: when
the score can't be computed (sparse financials), neutral 50 / available=False —
never excluded. Default is a pure scorer; raise '통과 최소 점수' to gate.
"""
from __future__ import annotations

from .. import scoring
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    fb = data.fundamentals
    if fb is None or not fb.available or fb.f_score is None:
        return FilterOutcome(passed=True, detail="F점수 없음", score=50.0, available=False)
    score = scoring.piotroski_score(fb.f_score)
    return FilterOutcome(
        passed=score >= float(p["min_score"]),
        detail=f"F {fb.f_score}/9 ({score:.0f})",
        value=float(fb.f_score),
        score=score,
    )


register(
    Filter(
        key="piotroski",
        label="피오트로스키 F",
        description="9점 회계건전성 체크리스트(수익성·레버리지/유동성·효율)로 재무가 개선 중인지 점수화. "
        "폭락한 저평가주 중 '돌아서는 놈'을 가려내는 추세 신호(ΔROA·현금흐름·마진). "
        "기본은 점수만 기여, '통과 최소 점수'를 올리면 게이트.",
        needs_fundamentals=True,
        weight=0.20,
        params=[
            Param("min_score", "통과 최소 점수", "float", default=0.0, min=0.0, max=100.0, step=5.0,
                  help="F점수→0~100 환산값(F×100/9)이 이 값 이상이면 통과. 0=점수만."),
        ],
        fn=_apply,
    )
)
