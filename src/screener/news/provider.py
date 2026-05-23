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
import os
from dataclasses import dataclass
from typing import Optional

import requests


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


def get_provider() -> NewsProvider:
    key = os.getenv("NEWSAPI_KEY", "").strip()
    if key:
        return NewsApiProvider(key)
    return NullProvider()
