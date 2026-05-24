"""Relative strength versus the market — bottoming on its own, or just beta?

Compares the stock's return over a lookback window to the benchmark's return
over the same span (US=S&P 500, KR=KOSPI). A fallen stock that *outperforms* a
weak tape is a far stronger turn signal than one merely tracking the index.
This is the orthogonal piece the screen lacks — every other signal is absolute.

Benchmark fetch is cached/memoized (see benchmark.py). No benchmark -> neutral
50 (fail-soft). Default scorer; raise min_score to gate on outperformance.
"""
from __future__ import annotations

import pandas as pd

from .. import benchmark, scoring
from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    close = data.prices["close"].dropna()
    window = int(p["window"])
    if len(close) < window + 1:
        return FilterOutcome(passed=False, detail="짧은 시계열")

    bench = benchmark.get_benchmark(data.market)
    if bench is None or bench.empty:
        return FilterOutcome(passed=True, detail="벤치마크 없음(중립)", value=50.0,
                             score=50.0, available=False)

    idx = pd.to_datetime(close.index)
    start_date, end_date = idx[-1 - window], idx[-1]
    b_win = bench[(bench.index >= start_date) & (bench.index <= end_date)]
    if len(b_win) < 2:
        return FilterOutcome(passed=True, detail="벤치 정렬부족(중립)", value=50.0,
                             score=50.0, available=False)

    stock_ret = float(close.iloc[-1]) / float(close.iloc[-1 - window]) - 1.0
    bench_ret = float(b_win.iloc[-1]) / float(b_win.iloc[0]) - 1.0
    excess = stock_ret - bench_ret
    score = scoring.relative_strength_score(excess)
    return FilterOutcome(
        passed=score >= float(p["min_score"]),
        detail=f"RS {excess * 100:+.0f}%p (종목 {stock_ret * 100:+.0f}% vs 지수 {bench_ret * 100:+.0f}%) ({score:.0f})",
        value=excess,
        score=score,
    )


register(
    Filter(
        key="relative_strength",
        label="상대강도(RS)",
        description="최근 N거래일 종목 수익률 − 시장지수 수익률(US=S&P500, KR=KOSPI). "
        "시장보다 덜 빠지거나 먼저 돌면 고점수. 모든 다른 신호가 절대값인데 이건 상대 성과. "
        "벤치마크 없으면 중립 50. 기본은 점수만, '통과 최소 점수'를 올리면 게이트.",
        weight=0.15,
        params=[
            Param("window", "비교 거래일", "int", default=63, min=10, max=252, step=1,
                  help="상대 수익률을 측정할 최근 거래일 수(63≈3개월)."),
            Param("min_score", "통과 최소 점수", "float", default=0.0, min=0.0, max=100.0, step=5.0),
        ],
        fn=_apply,
    )
)
