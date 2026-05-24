"""Daily cache for news fetches.

The news API is rate-limited (NewsAPI free = 100 req/day) and the filter runs
per surviving ticker, so a re-run or a second filter pass the same day would
burn the quota on identical queries. This caches each (source, query,
lookback) fetch for the calendar day: the first fetch hits the network, the
rest of the day reads SQLite. A failed fetch (None) is never cached, so it
retries once credentials/network recover.
"""
from __future__ import annotations

import datetime as dt
import json
from typing import Optional

from ..data import db as db_mod
from .provider import Article


def _to_articles(rows: list[dict]) -> list[Article]:
    out: list[Article] = []
    for r in rows:
        try:
            ts = dt.datetime.fromisoformat(r["published_at"])
        except (KeyError, ValueError):
            ts = dt.datetime.now(dt.timezone.utc)
        out.append(Article(title=r.get("title", ""), description=r.get("description", ""),
                           published_at=ts, source=r.get("source", "")))
    return out


def _to_rows(articles: list[Article]) -> list[dict]:
    return [{"title": a.title, "description": a.description,
             "published_at": a.published_at.isoformat(), "source": a.source}
            for a in articles]


def load(source: str, query: str, lookback_days: int) -> Optional[list[Article]]:
    """Return cached articles if fetched today (same UTC date), else None."""
    conn = db_mod.get_connection()
    try:
        row = conn.execute(
            "SELECT fetched_at, articles_json FROM news_cache "
            "WHERE source=? AND query=? AND lookback_days=?",
            (source, query, lookback_days),
        ).fetchone()
    finally:
        conn.close()
    if not row or not row[0]:
        return None
    try:
        fetched_date = dt.datetime.fromisoformat(row[0]).date()
    except ValueError:
        return None
    if fetched_date != dt.datetime.now(dt.timezone.utc).date():
        return None  # stale (different day) -> refetch
    try:
        return _to_articles(json.loads(row[1]) if row[1] else [])
    except (ValueError, TypeError):
        return None


def save(source: str, query: str, lookback_days: int, articles: list[Article]) -> None:
    conn = db_mod.get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO news_cache(source, query, lookback_days, fetched_at, articles_json)"
            " VALUES (?,?,?,?,?)",
            (source, query, lookback_days, db_mod.now_iso(), json.dumps(_to_rows(articles))),
        )
        conn.commit()
    finally:
        conn.close()
