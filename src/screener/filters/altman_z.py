"""Altman Z'' — bankruptcy distance for a beaten-down name.

The distress-risk puzzle (Campbell-Hilscher-Szilagyi 2008): high-bankruptcy-risk
stocks earn abnormally LOW returns. A deep-drawdown universe is already
bankruptcy-skewed, so screening out the genuinely distressed is where the edge
is. Z'' is the emerging-market / non-manufacturing variant (no asset-turnover
term), which fits KR + non-industrial US:

    Z'' = 3.25 + 6.56·WC/TA + 3.26·RE/TA + 6.72·EBIT/TA + 1.05·BVE/TL

Distress zone Z'' < 1.1, safe >= 2.6. Ships as a pure SCORER (no auto-exclude)
until the thresholds are confirmed on real recovery data — for our loss-making
names EBIT/RE often go negative, so a hard gate could double-count the price
drawdown's own delisting penalty. Raise '통과 최소 점수' to turn it into a gate.
Fail-soft: missing inputs (e.g. banks have no current ratio) -> neutral 50.
"""
from __future__ import annotations

from .. import scoring
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    fb = data.fundamentals
    if fb is None or not fb.available or fb.altman_z is None:
        return FilterOutcome(passed=True, detail="Z 없음", score=50.0, available=False)
    z = fb.altman_z
    score = scoring.altman_z_score(z)
    zone = "위험" if z < 1.1 else ("회색" if z < 2.6 else "안전")
    return FilterOutcome(
        passed=score >= float(p["min_score"]),
        detail=f"Z'' {z:.1f} {zone} ({score:.0f})",
        value=round(z, 2),
        score=score,
    )


register(
    Filter(
        key="altman_z",
        label="알트만 Z(부도위험)",
        description="Altman Z''(신흥시장/비제조 변형)로 부도위험을 점수화. 폭락주는 이미 부도위험이 높아 "
        "'추가 배제'가 핵심. 기본은 점수만(자동제외 안 함) — 적자기업 false-positive 회피 위해 "
        "백테스트 후 게이트화 권장. '통과 최소 점수'를 올리면 distress 자동제외.",
        needs_fundamentals=True,
        weight=0.18,
        params=[
            Param("min_score", "통과 최소 점수", "float", default=0.0, min=0.0, max=100.0, step=5.0,
                  help="Z''→0~100 환산(Z 1.1=0, 2.6=100)이 이 값 이상이면 통과. 0=점수만, 올리면 게이트."),
        ],
        fn=_apply,
    )
)
