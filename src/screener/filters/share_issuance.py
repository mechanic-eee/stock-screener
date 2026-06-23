"""Share issuance — is management buying its cheap stock, or diluting to survive?

Shares-outstanding YoY change. Pontiff-Woodgate (2008): share issuance predicts
the cross-section of returns more reliably than size, B/M, or momentum each on
its own. For a fallen name the sign matters a lot: buying back cheap stock
(shares shrinking) is a confidence signal; issuing stock / convertibles to stay
alive (shares growing) is a classic falling-knife red flag and the step before
capital impairment.

Needs the fundamentals bundle. US only for now (KR shares aren't in DART's
financial statements); fail-soft to neutral 50 / available=False otherwise.
"""
from __future__ import annotations

from .. import scoring
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    fb = data.fundamentals
    if fb is None or not fb.available or fb.share_change_yoy is None:
        return FilterOutcome(passed=True, detail="주식수 변화 없음", score=50.0, available=False)
    chg = fb.share_change_yoy
    score = scoring.share_issuance_score(chg)
    tag = "자사주" if chg < -0.01 else ("희석" if chg > 0.02 else "유지")
    return FilterOutcome(
        passed=score >= float(p["min_score"]),
        detail=f"주식수 {chg * 100:+.1f}% {tag} ({score:.0f})",
        value=round(chg, 4),
        score=score,
    )


register(
    Filter(
        key="share_issuance",
        label="발행주식수(희석/자사주)",
        description="발행주식수 YoY 변화. 감소(자사주매입)=고점수, 증가(증자/CB 희석)=저점수. "
        "같은 폭락이라도 '주식수 늘려 연명'은 회복확률↓ — 자본잠식 직전 신호. "
        "현재 US만(KR 주식수는 DART 재무제표 밖). 기본 점수만.",
        needs_fundamentals=True,
        weight=0.10,
        params=[
            Param("min_score", "통과 최소 점수", "float", default=0.0, min=0.0, max=100.0, step=5.0),
        ],
        fn=_apply,
    )
)
