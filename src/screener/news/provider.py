"""News provider abstraction.

A provider turns (query, lookback_days) into a list of articles. The default
implementation uses NewsAPI (https://newsapi.org) when NEWSAPI_KEY is set in
the environment; with no key it returns None so the news filter disables
itself gracefully instead of erroring.

To add another source (Naver News, Finnhub, ...), implement `fetch` with the
same shape and select it in `get_provider`.
"""
from __future__ import annotations

import datetime as dt
import html
import os
import re
from dataclasses import dataclass
from typing import Optional

import requests

_TAG_RE = re.compile(r"<[^>]+>")


def _clean(s: str) -> str:
    """Strip HTML tags and unescape entities (Naver wraps matches in <b>…)."""
    return html.unescape(_TAG_RE.sub("", s or "")).strip()


@dataclass
class Article:
    title: str
    description: str
    published_at: dt.datetime
    source: str


class NewsProvider:
    name = "base"

    def available(self) -> bool:  # pragma: no cover - interface
        return False

    def fetch(self, query: str, lookback_days: int) -> Optional[list[Article]]:  # pragma: no cover
        raise NotImplementedError


class NullProvider(NewsProvider):
    """No credentials configured: news filtering is unavailable."""

    name = "none"

    def available(self) -> bool:
        return False

    def fetch(self, query: str, lookback_days: int) -> Optional[list[Article]]:
        return None


class NewsApiProvider(NewsProvider):
    name = "newsapi"
    ENDPOINT = "https://newsapi.org/v2/everything"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def available(self) -> bool:
        return bool(self.api_key)

    def fetch(self, query: str, lookback_days: int) -> Optional[list[Article]]:
        frm = (dt.datetime.utcnow() - dt.timedelta(days=lookback_days)).date().isoformat()
        try:
            resp = requests.get(
                self.ENDPOINT,
                params={
                    "q": query,
                    "from": frm,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 50,
                    "apiKey": self.api_key,
                },
                timeout=15,
            )
            resp.raise_for_status()
            payload = resp.json()
        except (requests.RequestException, ValueError):
            return None
        out: list[Article] = []
        for a in payload.get("articles", []):
            try:
                ts = dt.datetime.fromisoformat(a["publishedAt"].replace("Z", "+00:00"))
            except (KeyError, ValueError):
                ts = dt.datetime.utcnow()
            out.append(
                Article(
                    title=a.get("title") or "",
                    description=a.get("description") or "",
                    published_at=ts,
                    source=(a.get("source") or {}).get("name", ""),
                )
            )
        return out


class NaverNewsProvider(NewsProvider):
    """Naver news search (Korean) — for KR tickers, which NewsAPI's English
    index can't match. The API has no date-range param, so we pull the newest
    `display` items (sort=date) and keep those within `lookback_days`.
    Free quota is 25,000 req/day. Needs NAVER_CLIENT_ID/NAVER_CLIENT_SECRET.
    """

    name = "naver"
    ENDPOINT = "https://openapi.naver.com/v1/search/news.json"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    def available(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def fetch(self, query: str, lookback_days: int) -> Optional[list[Article]]:
        from email.utils import parsedate_to_datetime

        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=lookback_days)
        try:
            resp = requests.get(
                self.ENDPOINT,
                params={"query": query, "display": 100, "sort": "date"},
                headers={"X-Naver-Client-Id": self.client_id,
                         "X-Naver-Client-Secret": self.client_secret},
                timeout=15,
            )
            resp.raise_for_status()
            payload = resp.json()
        except (requests.RequestException, ValueError):
            return None
        out: list[Article] = []
        for a in payload.get("items", []):
            try:
                ts = parsedate_to_datetime(a.get("pubDate", ""))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=dt.timezone.utc)
            except (TypeError, ValueError):
                ts = dt.datetime.now(dt.timezone.utc)
            if ts < cutoff:
                continue  # newest-first, but keep scanning — items can be slightly out of order
            out.append(Article(
                title=_clean(a.get("title", "")),
                description=_clean(a.get("description", "")),
                published_at=ts,
                source="naver",
            ))
        return out


def get_provider(market: Optional[str] = None) -> NewsProvider:
    """Pick a news source by market: KR -> Naver (Korean news), US -> NewsAPI.
    Each falls back to NullProvider when its credentials are absent (the news
    filter then treats news as unavailable). `market=None` prefers NewsAPI."""
    naver_id = os.getenv("NAVER_CLIENT_ID", "").strip()
    naver_secret = os.getenv("NAVER_CLIENT_SECRET", "").strip()
    newsapi = os.getenv("NEWSAPI_KEY", "").strip()

    if market == "KR":
        return NaverNewsProvider(naver_id, naver_secret) if (naver_id and naver_secret) else NullProvider()
    if market == "US":
        return NewsApiProvider(newsapi) if newsapi else NullProvider()
    # unspecified: best available, NewsAPI first
    if newsapi:
        return NewsApiProvider(newsapi)
    if naver_id and naver_secret:
        return NaverNewsProvider(naver_id, naver_secret)
    return NullProvider()
