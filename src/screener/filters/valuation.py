"""Valuation / quality score — cheap & sound, not just beaten-down (PER/PBR/ROE/배당).

Rewards low PER/PBR (cheap), high ROE (quality) and a dividend (downside
support). Complements the fundamental value-trap filter: that one *excludes*
broken businesses, this one *prefers* genuinely cheap, sound ones. Missing data
-> neutral 50, never excludes (fail-soft).

The engine fetches `data.valuation` lazily for survivors (yfinance .info for US,
DART+market-cap for KR), like the fundamentals filter.
"""
from __future__ import annotations

from .. import scoring
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    vb = data.valuation
    if vb is None or not vb.available:
        return FilterOutcome(passed=True, detail="밸류 데이터 없음(중립)", value=50.0, score=50.0)

    score = scoring.valuation_score(vb.per, vb.pbr, vb.roe, vb.dividend_yield)
    parts: list[str] = []
    if vb.per is not None:
        parts.append(f"PER{vb.per:.0f}")
    if vb.pbr is not None:
        parts.append(f"PBR{vb.pbr:.1f}")
    if vb.roe is not None:
        parts.append(f"ROE{vb.roe * 100:.0f}%")
    if vb.dividend_yield:
        parts.append(f"배당{vb.dividend_yield * 100:.1f}%")
    detail = (" ".join(parts) if parts else "밸류") + f" ({score:.0f})"
    return FilterOutcome(passed=score >= float(p["min_score"]), detail=detail, value=score, score=score)


register(
    Filter(
        key="valuation",
        label="밸류에이션",
        description="저평가·우량 점수: 낮은 PER/PBR(쌈)+높은 ROE(우량)+배당(하방지지)(PRD 외 추가). "
        "가치함정 필터가 '제외'라면 이건 '선호'. 데이터 없으면 중립 50. "
        "US=yfinance, KR=DART재무+시총(순이익 연환산 추정). 기본은 점수만, min_score로 게이트.",
        weight=0.15,
        needs_valuation=True,
        params=[
            Param("min_score", "통과 최소 점수", "float", default=0.0, min=0.0, max=100.0, step=5.0,
                  help="0이면 제외하지 않고 점수만 기여. 올리면 비싼 종목을 거름."),
        ],
        fn=_apply,
    )
)
