"""News aggregation: provider + sentiment -> a NewsBundle for a ticker."""
from __future__ import annotations

import datetime as dt

from ..models import NewsBundle
from . import sentiment
from .provider import NewsProvider, get_provider

__all__ = ["build_bundle", "get_provider", "NewsProvider"]


def build_bundle(
    provider: NewsProvider,
    query: str,
    lookback_days: int,
    recent_days: int,
) -> NewsBundle | None:
    """Fetch recent news for `query` and summarize into a NewsBundle.

    Returns None when the provider has no data/credentials so callers can
    treat news as unavailable.
    """
    articles = provider.fetch(query, lookback_days)
    if articles is None:
        return None

    now = dt.datetime.now(dt.timezone.utc)
    recent_cutoff = now - dt.timedelta(days=recent_days)
    scores: list[float] = []
    recent = 0
    headlines: list[str] = []
    for a in articles:
        published = a.published_at
        if published.tzinfo is None:
            published = published.replace(tzinfo=dt.timezone.utc)
        text = f"{a.title}. {a.description}"
        scores.append(sentiment.score_text(text))
        if published >= recent_cutoff:
            recent += 1
        if len(headlines) < 5:
            headlines.append(a.title)

    avg = sum(scores) / len(scores) if scores else 0.0
    return NewsBundle(
        article_count=len(articles),
        recent_count=recent,
        avg_sentiment=avg,
        headlines=headlines,
    )
