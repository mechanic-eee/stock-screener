"""News filter: recent coverage is plentiful AND turning positive.

This is the expensive filter (network I/O), so the engine applies it last and
only to tickers that already passed the cheaper screens. When no news provider
is configured for a market (e.g. no NEWSAPI_KEY for US), `data.news` is None and
the filter is **fail-soft** like the other enrichment filters: it passes with a
neutral score (50) and `available=False`, so the engine discounts it instead of
silently dropping the whole market. (Was fail-closed, which made a US scan with
news on exclude every US ticker.)

Sentiment comes from a lightweight keyword dictionary (placeholder quality), so
this filter ships at a low default weight — treat it as weak confirmation, not a
driver, until a real sentiment model replaces ``news/sentiment.py``.
"""
from __future__ import annotations

from ..models import Filter, FilterOutcome, Param, TickerData
from .base import register


def _apply(data: TickerData, p: dict) -> FilterOutcome:
    bundle = data.news
    if bundle is None:
        return FilterOutcome(passed=True, detail="뉴스없음(중립)", score=50.0, available=False)
    enough = bundle.recent_count >= p["min_recent_articles"]
    positive = bundle.avg_sentiment >= p["min_sentiment"]
    ok = enough and positive
    # map avg sentiment (-1..1) -> 0..100; halve when too few recent articles
    score = (bundle.avg_sentiment + 1) / 2 * 100
    if not enough:
        score *= 0.5
    detail = f"기사{bundle.recent_count} 감성{bundle.avg_sentiment:+.2f}"
    return FilterOutcome(passed=ok, detail=detail, value=bundle.avg_sentiment, score=score)


register(
    Filter(
        key="news",
        label="긍정 뉴스 증가",
        description="최근 기간 기사 수가 일정 이상이면서 평균 감성이 양(+)인 종목. "
        "KR=네이버 검색(NAVER_CLIENT_ID/SECRET), US=NewsAPI(NEWSAPI_KEY). 키 없는 시장은 중립.",
        needs_news=True,
        weight=0.10,  # placeholder sentiment dict -> weak confirmation, not a driver
        params=[
            Param("lookback_days", "조회 기간(일)", "int", default=30, min=7, max=90, step=1),
            Param("recent_days", "최근 집계 창(일)", "int", default=7, min=1, max=30, step=1),
            Param("min_recent_articles", "최소 최근 기사 수", "int", default=3, min=1, max=50, step=1),
            Param("min_sentiment", "최소 평균 감성(-1~1)", "float", default=0.1, min=-1.0, max=1.0, step=0.05),
        ],
        fn=_apply,
    )
)
