"""Accruals (earnings quality) — is the 'turnaround' real cash or an illusion?

Accrual ratio = (net income − operating cash flow) / total assets. Sloan (1996):
low-accrual firms outperform high-accrual ones, and the effect survives in small,
low-coverage names. For a fallen stock reporting a profit swing, this asks the
key question: is the reported improvement backed by cash, or by accounting
accruals that will reverse? Lower (more negative) = cleaner = higher score.

Needs the fundamentals bundle; fail-soft to neutral 50 / available=False when
net income or cash flow is missing. Default scorer.
"""
from __future__ import annotations

from .. import scoring
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    fb = data.fundamentals
    if fb is None or not fb.available or fb.accrual_ratio is None:
        return FilterOutcome(passed=True, detail="발생액 없음", score=50.0, available=False)
    r = fb.accrual_ratio
    score = scoring.accruals_score(r)
    return FilterOutcome(
        passed=score >= float(p["min_score"]),
        detail=f"발생액 {r * 100:+.0f}% ({score:.0f})",
        value=round(r, 4),
        score=score,
    )


register(
    Filter(
        key="accruals",
        label="이익의 질(발생액)",
        description="(순이익−영업현금흐름)/총자산. 낮을수록(현금기반) 고점수 — 흑자전환이 진짜 현금인지 "
        "회계 발생액 착시인지 가린다. ★폭락주 유니버스에선 역설적: 점수 검증(score-validation-2026-06-27)서 "
        "KR per-date IC −0.085(t−3.5)·US 무력 — NI≪CFO('깨끗')가 손상·감액 기업 신호(distress 혼입). "
        "게이트로는 유효하나 합성 점수엔 불참(weight 0).",
        needs_fundamentals=True,
        weight=0.0,  # consistently negative/inert IC on the drawdown universe (KR t−3.5,
        # US ~0; score-validation-2026-06-27) — distress confound. Out of composite.
        params=[
            Param("min_score", "통과 최소 점수", "float", default=0.0, min=0.0, max=100.0, step=5.0),
        ],
        fn=_apply,
    )
)
