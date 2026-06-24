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
        return FilterOutcome(passed=True, detail="재무없음(중립)", value=50.0,
                             score=50.0, available=False)

    # Lethal flags = exchange-/audit-confirmed near-certain delisting: exclude
    # standalone, regardless of min_violations. Soft flags accumulate.
    lethal: list[str] = []
    if fb.capital_impairment:
        lethal.append("자본잠식")
    if fb.four_quarters_all_loss:
        lethal.append("4Q적자")
    if getattr(fb, "audit_qualified", False):
        lethal.append("감사의견❌")
    if getattr(fb, "risk_event", None):
        lethal.append(str(fb.risk_event))

    soft: list[str] = []
    if fb.revenue_yoy is not None and fb.revenue_yoy < float(p["rev_yoy_floor"]) / 100.0:
        soft.append("매출급감")
    if fb.debt_to_equity is not None and fb.debt_to_equity > float(p["max_d2e"]) / 100.0:
        soft.append("고부채")

    score = scoring.fundamental_score(fb.revenue_yoy, fb.op_margin, fb.debt_to_equity)
    min_v = int(p["min_violations"])
    excluded = (bool(p.get("drop_lethal", True)) and bool(lethal)) \
        or (min_v > 0 and len(soft) >= min_v)

    parts: list[str] = []
    if fb.revenue_yoy is not None:
        parts.append(f"매출{fb.revenue_yoy * 100:+.0f}%")
    if fb.op_margin is not None:
        parts.append(f"영익{fb.op_margin * 100:.0f}%")
    if fb.debt_to_equity is not None:
        parts.append(f"부채{fb.debt_to_equity * 100:.0f}%")
    detail = " ".join(parts) if parts else "재무"
    flags = lethal + soft
    if flags:
        detail += f" ⚠️{'/'.join(flags)}"
    detail += f" ({score:.0f})"

    return FilterOutcome(passed=not excluded, detail=detail, value=score, score=score)


register(
    Filter(
        key="fundamental",
        label="펀더멘털",
        description="재무 가치함정 자동제외 + 점수(PRD §5.4.3). **치명 신호**(자본잠식·4Q적자·"
        "감사의견 비적정·부도/회생 등 DART 이벤트)는 단독 제외, **약신호**(매출급감·고부채)는 "
        "min_violations개 이상일 때 제외. 재무 없으면 중립 50점. KR은 DART_API_KEY 필요(감사의견·"
        "위험공시 포함), US는 yfinance.",
        weight=0.25,
        needs_fundamentals=True,
        params=[
            Param("drop_lethal", "치명신호 단독제외", "bool", default=True,
                  help="자본잠식·4Q적자·감사의견 비적정·부도/회생 등은 단독으로도 제외(상폐 직행 신호)."),
            Param("min_violations", "약신호 자동제외 개수", "int", default=2, min=0, max=4, step=1,
                  help="매출급감·고부채 등 약신호가 이 개수 이상이면 제외. 0이면 약신호로는 제외 안 함."),
            Param("rev_yoy_floor", "매출 YoY 하한 %", "float", default=-30.0, min=-90.0, max=0.0, step=5.0,
                  help="최근 분기 매출 YoY가 이 값 미만이면 위반(기본 -30%)."),
            Param("max_d2e", "부채비율 상한 %", "float", default=300.0, min=100.0, max=1000.0, step=50.0,
                  help="부채/자본이 이 값 초과면 위반(기본 300%)."),
        ],
        fn=_apply,
    )
)
