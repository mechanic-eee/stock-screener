"""Fundamental value-trap screen + score (PRD §5.4.3).

Auto-excludes a ticker when it trips at least `min_violations` of the four
red flags (revenue collapse, over-leverage, four straight loss quarters,
capital impairment). Otherwise contributes a 0-100 score from revenue YoY,
operating margin and debt/equity. Missing financials -> neutral 50, never
excluded (fail-soft).

The engine fetches `data.fundamentals` lazily for survivors (external API +
cache), like the news filter — this filter only reads it.
"""
from __future__ import annotations

from .. import scoring
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    fb = data.fundamentals
    if fb is None or not fb.available:
        return FilterOutcome(passed=True, detail="재무없음(중립)", value=50.0, score=50.0)

    violations: list[str] = []
    if fb.revenue_yoy is not None and fb.revenue_yoy < float(p["rev_yoy_floor"]) / 100.0:
        violations.append("매출급감")
    if fb.debt_to_equity is not None and fb.debt_to_equity > float(p["max_d2e"]) / 100.0:
        violations.append("고부채")
    if fb.four_quarters_all_loss:
        violations.append("4Q적자")
    if fb.capital_impairment:
        violations.append("자본잠식")

    score = scoring.fundamental_score(fb.revenue_yoy, fb.op_margin, fb.debt_to_equity)
    min_v = int(p["min_violations"])
    excluded = min_v > 0 and len(violations) >= min_v

    parts: list[str] = []
    if fb.revenue_yoy is not None:
        parts.append(f"매출{fb.revenue_yoy * 100:+.0f}%")
    if fb.op_margin is not None:
        parts.append(f"영익{fb.op_margin * 100:.0f}%")
    if fb.debt_to_equity is not None:
        parts.append(f"부채{fb.debt_to_equity * 100:.0f}%")
    detail = " ".join(parts) if parts else "재무"
    if violations:
        detail += f" ⚠️{'/'.join(violations)}"
    detail += f" ({score:.0f})"

    return FilterOutcome(passed=not excluded, detail=detail, value=score, score=score)


register(
    Filter(
        key="fundamental",
        label="펀더멘털",
        description="재무 가치함정 자동제외 + 점수(PRD §5.4.3). 매출급감/고부채/4Q적자/자본잠식 중 "
        "min_violations개 이상이면 제외. 재무 데이터 없으면 중립 50점(제외 안 함). "
        "KR은 DART_API_KEY 필요(없으면 중립), US는 yfinance(키 불요).",
        weight=0.25,
        needs_fundamentals=True,
        params=[
            Param("min_violations", "자동제외 위반 개수", "int", default=2, min=0, max=4, step=1,
                  help="이 개수 이상의 red flag면 제외. 0이면 제외 안 하고 점수만 기여."),
            Param("rev_yoy_floor", "매출 YoY 하한 %", "float", default=-30.0, min=-90.0, max=0.0, step=5.0,
                  help="최근 분기 매출 YoY가 이 값 미만이면 위반(기본 -30%)."),
            Param("max_d2e", "부채비율 상한 %", "float", default=300.0, min=100.0, max=1000.0, step=50.0,
                  help="부채/자본이 이 값 초과면 위반(기본 300%)."),
        ],
        fn=_apply,
    )
)
