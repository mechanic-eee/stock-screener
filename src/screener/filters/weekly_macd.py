"""Weekly (higher-timeframe) MACD confirmation — PRD §5.4.4.

Resamples the cached daily closes to weekly bars (last trading day of each
week, week ending Friday) and scores the weekly MACD state: a fresh weekly
signal-line cross is strongest, a positive-and-rising line next, a
negative-and-falling line worst.

This is a confirmation *scorer*, not a hard gate. By default it never excludes
a ticker (min_score=0, so it only contributes score); raise min_score to use
it as a gate. Pure pandas — resamples the already-cached daily history.
"""
from __future__ import annotations

import pandas as pd

from .. import indicators, scoring
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register

_LABELS = {
    "signal_cross": "주봉 시그널돌파",
    "pos_rising": "주봉+ 우상향",
    "pos_flat": "주봉+ 보합",
    "pos_falling": "주봉+ 우하향",
    "neg_rising": "주봉- 우상향",
    "neg_flat": "주봉- 보합",
    "neg_falling": "주봉- 우하향",
}


def _weekly_state(macd_line: pd.Series, signal_line: pd.Series, flat_frac: float,
                  eps: float) -> str:
    """Classify the latest weekly MACD into one of the PRD §5.4.4 states.

    `eps` is a scale-aware deadband: a cross only counts when diff rises above
    +eps from <=0, so near-zero float wobble (and the latest, still-open weekly
    bar) can't masquerade as a strong higher-timeframe signal.
    """
    diff = macd_line - signal_line
    # cross = diff climbs out of the noise/negative zone (<= eps) to clearly
    # positive (> eps). Using eps on both sides avoids both the false cross from
    # near-zero wobble and the missed cross when diff steps through the band.
    sc = (diff > eps) & (diff.shift(1, fill_value=eps) <= eps)
    if sc.tail(4).any():
        return "signal_cross"
    last = float(macd_line.iloc[-1])
    past = float(macd_line.iloc[-5])  # 4 weeks ago
    denom = abs(past) if past != 0 else 1e-9
    change = (last - past) / denom
    sign = "pos" if last >= 0 else "neg"
    if change > flat_frac:
        trend = "rising"
    elif change < -flat_frac:
        trend = "falling"
    else:
        trend = "flat"
    return f"{sign}_{trend}"


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    close = data.prices["close"].dropna()
    idx = pd.to_datetime(close.index)
    weekly = pd.Series(close.to_numpy(), index=idx).resample("W-FRI").last().dropna()
    if len(weekly) < p["slow"] + p["signal"] + 5:
        return FilterOutcome(passed=False, detail="주봉 짧음")

    macd_line, signal_line, _ = indicators.macd(weekly, p["fast"], p["slow"], p["signal"])
    # deadband ~0.1% of weekly price level: below this, MACD/signal separation
    # is noise (or an artifact of the still-open latest week), not a real cross.
    eps = max(1e-9, 1e-3 * abs(float(weekly.iloc[-1])))
    state = _weekly_state(macd_line, signal_line, float(p["flat_pct"]) / 100.0, eps)
    score = scoring.weekly_macd_score(state)
    return FilterOutcome(
        passed=score >= float(p["min_score"]),
        detail=f"{_LABELS[state]} ({score:.0f})",
        value=float(macd_line.iloc[-1]),
        score=score,
    )


register(
    Filter(
        key="weekly_macd",
        label="주봉 MACD",
        description="일봉을 주봉으로 리샘플해 상위 시간프레임 MACD 상태를 점수화(PRD §5.4.4). "
        "기본은 점수만 기여(제외 안 함), '통과 최소 점수'를 올리면 게이트로 동작.",
        weight=0.15,
        params=[
            Param("fast", "Fast EMA", "int", default=12, min=2, max=50, step=1),
            Param("slow", "Slow EMA", "int", default=26, min=5, max=100, step=1),
            Param("signal", "Signal", "int", default=9, min=2, max=50, step=1),
            Param("flat_pct", "보합 판정 ±%", "float", default=5.0, min=0.0, max=50.0, step=0.5,
                  help="최근 4주 MACD 변화율이 이 값 이내면 '보합'으로 분류."),
            Param("min_score", "통과 최소 점수", "float", default=0.0, min=0.0, max=100.0, step=5.0,
                  help="0이면 제외하지 않고 점수만 기여. 올리면 주봉이 약한 종목을 걸러내는 게이트로 사용."),
        ],
        fn=_apply,
    )
)
