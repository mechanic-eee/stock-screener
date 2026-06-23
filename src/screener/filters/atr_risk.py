"""ATR risk meta — how volatile/sizable is this beaten-down name?

A deep-drawdown universe is full of names whose daily swings (ATR) are huge.
Equal-weight buying those blows up position risk, and a sky-high ATR is itself a
'still-falling knife / lottery ticket' tell. This filter measures ATR as a % of
price and surfaces a suggested stop distance (mult x ATR) so the screener output
also feeds position sizing — the dimension that was missing between *finding* a
candidate and *acting* on it.

Informational by default (weight 0, never gates): it adds an "ATR% / 손절 ±x%"
column and a tradeability score you can opt to weight. Pure pandas on the cached
daily OHLC — no extra fetch, KR/US identical.
"""
from __future__ import annotations

from .. import indicators, scoring
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    px = data.prices
    close = px["close"].dropna()
    window = int(p["window"])
    if len(close) < window + 1:
        return FilterOutcome(passed=True, detail="짧은 시계열", score=50.0)

    high = px["high"] if "high" in px else None
    low = px["low"] if "low" in px else None
    atr = indicators.atr(high, low, px["close"], window=window)
    atr_val = float(atr.iloc[-1])
    last = float(close.iloc[-1])
    if last <= 0 or atr_val != atr_val:  # NaN guard
        return FilterOutcome(passed=True, detail="데이터 부족", score=50.0)

    atr_pct = atr_val / last * 100.0
    stop_pct = float(p["stop_mult"]) * atr_pct
    score = scoring.atr_risk_score(atr_pct)
    band = "차분" if atr_pct <= 4 else ("보통" if atr_pct <= 7 else "고변동⚠️")
    return FilterOutcome(
        passed=True,  # never gates — this is risk metadata, not a screen
        detail=f"ATR {atr_pct:.1f}% · 손절 ±{stop_pct:.0f}% {band} ({score:.0f})",
        value=round(atr_pct, 2),
        score=score,
    )


register(
    Filter(
        key="atr_risk",
        label="ATR 리스크/손절",
        description="일봉 ATR(평균진폭)을 가격 대비 %로 측정해 변동성·권장손절폭(mult×ATR)을 메타데이터로 노출. "
        "폭락주는 ATR이 비정상적으로 커 동일비중 매수 시 리스크가 폭증 — 발굴→사이징을 잇는 차원. "
        "기본은 정보성(가중 0, 제외 안 함). 가중을 올리면 '차분한 종목 선호' 스코어러로 동작.",
        weight=0.0,
        params=[
            Param("window", "ATR 기간", "int", default=14, min=5, max=60, step=1),
            Param("stop_mult", "손절 배수(×ATR)", "float", default=2.5, min=1.0, max=5.0, step=0.5,
                  help="권장 손절폭 = 이 배수 × ATR. 통상 2~3×ATR."),
        ],
        fn=_apply,
    )
)
