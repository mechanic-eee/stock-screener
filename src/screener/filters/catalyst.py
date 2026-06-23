"""Catalyst (earnings) flag + score bonus — PRD §5.4.5 / §5.5.2.

Two effects, both opt-in:
  • Upcoming-earnings warning: if the next earnings date is within `warn_days`
    calendar days, the detail carries a ⚠️ D-n flag.
  • Score bonus: if the screen's most recent MACD turn (zero- or signal-line
    cross) landed within `post_days` *trading* days after the last earnings
    release, add `bonus` points. This is a *bonus* filter — it never excludes
    and its score is added to the composite AFTER normalization (the total may
    exceed 100, per PRD §5.5.2).

The engine fetches `data.catalyst` lazily for survivors (yfinance, cached). The
MACD turn is recomputed here from the cached daily closes, so the bonus stays
self-contained.
"""
from __future__ import annotations

import pandas as pd

from .. import indicators
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _latest_cross_date(close: pd.Series, p: dict):
    """Date of the most recent MACD zero- or signal-line upward cross, or None."""
    if len(close) < p["slow"] + p["signal"] + 5:
        return None
    macd_line, signal_line, _ = indicators.macd(close, p["fast"], p["slow"], p["signal"])
    zc = (macd_line > 0) & (macd_line.shift(1, fill_value=0) <= 0)
    diff = macd_line - signal_line
    sc = (diff > 0) & (diff.shift(1, fill_value=0) <= 0)
    crossed = zc | sc
    hits = crossed[crossed]
    if hits.empty:
        return None
    return pd.Timestamp(hits.index[-1]).date()


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    ci = data.catalyst
    if ci is None or not ci.available:
        return FilterOutcome(passed=True, detail="실적일정 없음", score=0.0)

    parts: list[str] = []
    # upcoming-earnings warning
    if ci.days_until is not None and 0 <= ci.days_until <= int(p["warn_days"]):
        parts.append(f"실적 D-{ci.days_until} ⚠️")
    elif ci.next_earnings is not None:
        parts.append(f"실적 {ci.next_earnings.isoformat()}")

    # bonus: most recent MACD turn within post_days trading days after earnings
    bonus = 0.0
    if ci.last_earnings is not None:
        close = data.prices["close"].dropna()
        idx = pd.to_datetime(close.index)
        cross = _latest_cross_date(pd.Series(close.to_numpy(), index=idx), p)
        if cross is not None and cross >= ci.last_earnings:
            # trading bars strictly after earnings, up to and including the cross
            after = idx[(idx.date > ci.last_earnings) & (idx.date <= cross)]
            if len(after) <= int(p["post_days"]):
                bonus = float(p["bonus"])
                parts.append(f"실적후전환 +{bonus:.0f}")

    detail = " · ".join(parts) if parts else "실적일정"
    return FilterOutcome(passed=True, detail=detail, value=bonus, score=bonus)


register(
    Filter(
        key="catalyst",
        label="카탈리스트(실적)",
        description="실적발표 임박(7일내) ⚠️ 경고 표시 + (선택)실적 직후 3거래일 내 MACD 전환 보너스. "
        "보너스는 발동조건이 좁고 yfinance KR 실적 커버리지가 얇아 기본 OFF(0점) — "
        "임박 경고만 쓰는 정보성 필터. 점수를 켜려면 '보너스 점수' 슬라이더를 올린다. "
        "yfinance 실적일정(US+KR).",
        weight=0.0,
        needs_catalyst=True,
        is_bonus=True,
        params=[
            Param("bonus", "보너스 점수", "float", default=0.0, min=0.0, max=30.0, step=1.0,
                  help="실적 직후 MACD 전환 종목에 더할 점수. 기본 0(보너스 끔) — 올리면 가산."),
            Param("warn_days", "임박 경고 일수", "int", default=7, min=1, max=30, step=1,
                  help="다음 실적이 이 일수(달력) 이내면 ⚠️ 표시."),
            Param("post_days", "실적후 전환 허용 거래일", "int", default=3, min=1, max=10, step=1,
                  help="실적 발표 후 이 거래일 이내의 MACD 전환만 보너스 인정."),
            Param("fast", "Fast EMA", "int", default=12, min=2, max=50, step=1),
            Param("slow", "Slow EMA", "int", default=26, min=5, max=100, step=1),
            Param("signal", "Signal", "int", default=9, min=2, max=50, step=1),
        ],
        fn=_apply,
    )
)
